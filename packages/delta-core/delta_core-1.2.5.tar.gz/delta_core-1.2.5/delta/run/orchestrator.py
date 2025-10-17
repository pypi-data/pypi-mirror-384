import asyncio
import collections
import datetime
import io
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from email.message import EmailMessage
from functools import partial
from http import HTTPStatus
from string import Template
from typing import Any, Callable, Dict, List, Union
from urllib.parse import urlparse

import aiohttp
import requests

from delta.manifest.parser import (
    Dependency,
    Input,
    Manifest,
    Model,
    Output,
    OutputModel,
    Resource,
)
from delta.run.api.model import (
    DataParameterModel,
    ParameterModel,
    PrimitiveParameterModel,
    SecretParameterModel,
    RunContextModel,
    RunContextUpdateModel,
    RunStatus,
    model_param_to_orm_param,
    retrieve_primitive_type,
)
from delta.run.db.orm import ParameterKind, RunContext
from delta.run.job import Image, Job, JobService, PathMapper
from delta.run.job.builder.python_builder import PythonRunner
from delta.run.storage_manager import (
    DeltaLocalStorageManager,
    DeltaStorageManager,
)

logger = logging.getLogger("Orchestrator")
logger.setLevel(logging.DEBUG)


class PlaceholderTemplate(Template):
    idpattern = r"\(([a-z][A-Za-z0-9_-]*)(\.[a-z][A-Za-z0-9_-]*)*\)"


@dataclass
class Edge:
    id: int
    from_id: int
    from_port: str
    to_id: int
    to_port: str
    value: (DataParameterModel | PrimitiveParameterModel |
            SecretParameterModel) = None


@dataclass
class Node:
    id: str
    name: str
    element: Union[Resource, Input, Model, Output, Dependency]
    status: RunStatus = field(init=False, default=RunStatus.CREATED)
    inputs_edges: list[Edge] = field(default_factory=list)
    outputs_edges: list[Edge] = field(default_factory=list)


class DeltaOrchestrator:
    def __init__(
        self,
        manifest: Manifest,
        workflow: dict,
        run_ctx: RunContextModel,
        storage_manager: DeltaStorageManager,
        job_service: JobService,
        on_update_context: Callable[[str, RunContextUpdateModel], None] = None,
        on_create_sub_context: Callable[[str, RunContext], None] = None,
        notify_update_status: Callable[[str, str, RunStatus], None] = None,
    ):
        self._manifest = manifest
        self._workflow = workflow
        self.run_ctx = run_ctx
        self.storage_manager = storage_manager
        self.job_service = job_service
        self._on_update_run_context = on_update_context
        self._on_create_sub_run_context = on_create_sub_context
        self._notify_update_status = notify_update_status
        self.graph = self._init_graph(workflow["edges"])
        self.nodes = self._init_nodes(manifest, workflow)
        self.number_of_nodes = len(self.nodes)
        self._in_degree = self._init_in_degrees(self.graph, self.nodes)

    @staticmethod
    def _init_nodes(manifest: Manifest, workflow: dict):
        # on parcours la liste des edges pour trouver les ports
        nodes = {}
        inputs = collections.defaultdict(list)
        outputs = collections.defaultdict(list)

        for i, edge in enumerate(workflow["edges"]):
            from_id = edge["from"]["id"]
            from_port = edge["from"].get("port", "data")
            to_id = edge["to"]["id"]
            to_port = edge["to"].get("port", "data")
            edge = Edge(i, from_id, from_port, to_id, to_port, None)
            outputs[from_id].append(edge)
            inputs[to_id].append(edge)
        # parcours la liste de noeud
        for node in workflow["nodes"]:
            _id = node["id"]
            (section, name) = node["ref"].split(".", maxsplit=1)
            element = eval(f'manifest.{section}["{name}"]')
            n = Node(_id, name, element, inputs[_id], outputs[_id])
            nodes[_id] = n
        return nodes

    @staticmethod
    def _init_in_degrees(
        graph: Dict[Any, list], nodes: Dict[Any, Node]
    ) -> Dict[Any, int]:
        in_degree = {}
        for node in nodes:
            in_degree[node] = 0
        for i in graph:
            for j in graph[i]:
                in_degree[j] += 1
        return in_degree

    @staticmethod
    def _init_graph(edges: List[dict]) -> Dict[Any, List]:
        graph = collections.defaultdict(list)
        for edge in edges:
            from_id = edge["from"]["id"]
            to_id = edge["to"]["id"]

            graph[from_id].append(to_id)
        return graph

    @staticmethod
    def substitute_output_placeholder(args: dict, output: OutputModel):
        t = PlaceholderTemplate(output.glob)
        sbt_dict = {}
        for id in t.get_identifiers():
            keys = id[1:-1].split(".")

            val = args[keys[0]][keys[1]]
            if isinstance(val, SecretParameterModel):
                val = val.secret_value
            if isinstance(val, PrimitiveParameterModel):
                val = val.value
            if isinstance(val, DataParameterModel):
                val = os.path.basename(val.path)
            sbt_dict[id] = val
        return t.substitute(sbt_dict)

    async def run(self):
        self.storage_manager.add_run_directory(uuid.UUID(self.run_ctx.id))
        self.run_ctx.status = RunStatus.RUNNING
        logger.info(
            "Run(%s) starting (dt: %s, dtv: %s, owner: %s)",
            self.run_ctx.id,
            str(self.run_ctx.deltatwin_id),
            self.run_ctx.deltatwin_version,
            self.run_ctx.owner,
        )

        # Update run context --> set status to running
        rcup = RunContextUpdateModel(status=self.run_ctx.status)
        if self._on_update_run_context:
            self._on_update_run_context(self.run_ctx.id, rcup)
        if self._notify_update_status:
            await self._notify_update_status(
                self.run_ctx.owner,
                self.run_ctx.deltatwin_id,
                self.run_ctx.id,
                self.run_ctx.status,
                self.run_ctx.deltatwin_version,
            )

        try:
            self.check_inputs()
            async with asyncio.TaskGroup() as group:
                for node_id, value in self._in_degree.items():
                    if value == 0:
                        group.create_task(
                            self.exec_task(self.nodes[node_id], group),
                            name=node_id,
                        )
        except TypeError as eg:
            self.run_ctx.status = RunStatus.ERROR
            logger.error(eg)
        except BaseExceptionGroup as eg:
            for ex in eg.exceptions:
                logger.error(ex)
            self.run_ctx.status = RunStatus.ERROR

        if self.run_ctx.status == RunStatus.RUNNING:
            self.run_ctx.status = RunStatus.SUCCESS
            self.run_ctx.return_code = 0

        # update run context --> run completion
        rcup = RunContextUpdateModel(
            status=self.run_ctx.status,
            return_code=self.run_ctx.return_code,
            message=self.run_ctx.message,
            inputs=self.run_ctx.inputs,
            outputs=self.run_ctx.outputs,
        )
        if self._on_update_run_context:
            self._on_update_run_context(self.run_ctx.id, rcup)
        if self._notify_update_status:
            await self._notify_update_status(
                self.run_ctx.owner,
                self.run_ctx.deltatwin_id,
                self.run_ctx.id,
                self.run_ctx.status,
                self.run_ctx.deltatwin_version,
            )

        # logging run completion
        logger.info(
            "Run %s (%s | %s) finished with status : %s (%d: %s)",
            self.run_ctx.id,
            self.run_ctx.deltatwin_id,
            self.run_ctx.deltatwin_version,
            self.run_ctx.status.value,
            self.run_ctx.return_code,
            self.run_ctx.message,
        )
        date_format = "%Y-%m-%d %H:%M:%S"
        started = self.run_ctx.date_created
        computation_time = (
            datetime.datetime.now(datetime.timezone.utc)
            - self.run_ctx.date_created
        )
        ended = started + computation_time
        logger.info(
            "[user-id: %s - process-id: %s - deltatwin-id: %s - "
            "deltatwin-version: %s - deltatwin-status: %s - "
            "starting-date: %s - ending-date: %s]",
            self.run_ctx.owner,
            "run",
            self.run_ctx.deltatwin_id,
            self.run_ctx.deltatwin_version,
            self.run_ctx.status.value,
            started.strftime(date_format),
            ended.strftime(date_format),
        )
        return self.run_ctx

    async def exec_task(self, node: Node, group: asyncio.TaskGroup):
        logger.debug(f"execute run: {self.run_ctx.id}, node: {node.id}")
        node.status = RunStatus.RUNNING

        if isinstance(node.element, Resource):
            await self.execute_resource_node(node, group)
        if isinstance(node.element, Input):
            await self.execute_input_node(node, group)
        if isinstance(node.element, Model):
            await self.execute_model_node(node, group)
        if isinstance(node.element, Output):
            await self.execute_output_node(node, group)
        if isinstance(node.element, Dependency):
            await self.execute_dependency_node(node, group)

    async def fetch_resource(
        self, node: Node, resource: ParameterModel, group: asyncio.TaskGroup
    ):
        if node.element.type == "Data" and resource.path is None:
            resource_path = resource.url.strip()
            try:
                if re.match("^https?://", resource_path):
                    resp = requests.get(resource_path, stream=True)
                    if resp.status_code != 200:
                        node.status = RunStatus.ERROR
                        self.run_ctx.return_code = 210
                        self.run_ctx.message = (
                            f"Error while fetching input {node.name} "
                            f"from url {resource_path}. Please verify the url."
                        )
                        raise RuntimeError(f"Error while fetching {node.name}")
                    filename = urlparse(resource_path).path.split("/")[-1]
                    msg = EmailMessage()
                    for k, v in resp.headers.items():
                        msg[k] = v
                    filename = msg.get_filename(failobj=filename)
                    path = await asyncio.to_thread(
                        self.storage_manager.set_data,
                        self.run_ctx.id,
                        str(node.id),
                        filename,
                        io.BytesIO(resp.content),
                    )
                elif os.path.isfile(resource_path):
                    basename = os.path.basename(resource_path)
                    if isinstance(
                            self.storage_manager,
                            DeltaLocalStorageManager
                    ):
                        path = resource_path
                    else:
                        with open(resource_path, "rb") as f:
                            path = await asyncio.to_thread(
                                self.storage_manager.set_data,
                                self.run_ctx.id,
                                str(node.id),
                                basename,
                                f,
                            )
                else:
                    raise FileNotFoundError(resource_path)
            except Exception:
                logger.error(f"Error while fetching {node.name}")
                node.status = RunStatus.ERROR
                self.run_ctx.return_code = 211
                self.run_ctx.message = (
                    f"Error while fetching input {node.name} "
                    f"from url {resource_path}. Please verify the url."
                )
                raise RuntimeError(f"Error while fetching {node.name}")
            resource.path = path
            infos = await asyncio.to_thread(
                self.storage_manager.get_data_info, path
            )
            resource.size = infos["size"]
            resource.checksum = infos["checksum"]
            logger.debug(
                f"file (basename:{os.path.basename(resource.path)},"
                f"size:{resource.size}, "
                f"checksum:{resource.checksum})"
            )
        for output_edge in node.outputs_edges:
            output_edge.value = resource
        node.status = RunStatus.SUCCESS

    async def execute_input_node(self, node: Node, group: asyncio.TaskGroup):
        logger.debug(f"executing input node {node.name}")
        # Check if the user specified the input
        _input = None
        for user_input in self.run_ctx.inputs:
            if user_input.name == node.name:
                _input = user_input
        # If not, we get the input from the manifest file
        if _input is None:
            logger.debug("Getting input from manifest")
            input_value = node.element.value
            if node.element.type == "Data":
                _input = DataParameterModel(
                    name=node.name, type="Data", url=input_value["url"]
                )
            elif node.element.type == "secret":
                print(f"input: {input_value}")
                _input = SecretParameterModel(
                    name=node.name,
                    type="secret",
                    value=input_value,
                )
            else:
                _input = PrimitiveParameterModel(
                    name=node.name,
                    type=retrieve_primitive_type(input_value),
                    value=input_value,
                )
            self.run_ctx.inputs.append(_input)

        await self.fetch_resource(node, _input, group)
        rcup = RunContextUpdateModel(inputs=self.run_ctx.inputs)
        if self._on_update_run_context:
            self._on_update_run_context(self.run_ctx.id, rcup)
        self.task_done(node, group)

    async def execute_resource_node(
        self, node: Node, group: asyncio.TaskGroup
    ):
        logger.debug(f"executing resource node {node.name}")
        resource_value = node.element.value
        if node.element.type == "Data":
            resource = DataParameterModel(
                name=node.name, type="Data", url=resource_value
            )
        elif node.element.type == "secret":
            resource = SecretParameterModel(
                name=node.name,
                type="secret",
                value=resource_value,
            )
        else:
            resource = PrimitiveParameterModel(
                name=node.name,
                type=retrieve_primitive_type(resource_value),
                value=resource_value,
            )
        await self.fetch_resource(node, resource, group)
        self.task_done(node, group)

    async def execute_model_node(self, node: Node, group: asyncio.TaskGroup):
        tag = f"{self.run_ctx.deltatwin_id}/{node.name}"
        if self.run_ctx.deltatwin_version:
            tag += f":{self.run_ctx.deltatwin_version}"

        img = Image(tag)
        pr = PythonRunner(node.element)
        args = {}
        inputs = {}
        inputs_mount: List[PathMapper] = []
        outputs_mount: List[PathMapper] = []
        for edge in node.inputs_edges:
            inputs[edge.to_port] = edge.value
            if isinstance(edge.value, DataParameterModel):
                path = self.storage_manager.get_full_path(edge.value.path)
                pm = PathMapper(path, os.path.join("/s3", edge.value.path))
                inputs_mount.append(pm)
        args["inputs"] = inputs
        for output in node.element.outputs.values():
            if output.type == "Data":
                output_path = self.substitute_output_placeholder(args, output)
                path = os.path.join("runs", str(self.run_ctx.id), str(node.id))
                # need "/" at the end for ansible playbook
                # to work with directory
                storage_path = self.storage_manager.get_full_path(path) + "/"
                if not os.path.isabs(output_path):
                    mount_path = os.path.join(".", output_path)
                    pm = PathMapper(mount_path, storage_path)
                else:
                    pm = PathMapper(output_path, storage_path)
                outputs_mount.append(pm)

        cmd = pr.build_command(**args)
        cmd_secure = pr.build_command(secure=True, **args)
        job = Job(
            command=cmd,
            image=img,
            inputs=inputs_mount,
            outputs=outputs_mount,
        )
        logger.debug("Job id : %s", job.id)
        event = asyncio.Event()
        model_done = partial(self.model_done_callback, node, event)
        job.add_callback(model_done)
        await self.job_service.execute_job(job)
        await event.wait()
        if node.status == RunStatus.SUCCESS:
            for output in node.element.outputs.values():
                if output.type == "Data":
                    output_name = self.substitute_output_placeholder(
                        args, output
                    )
                    output_path = self.storage_manager.find_data(
                        self.run_ctx.id, node.id, output_name
                    )
                    if len(output_path) != 1:
                        self.run_ctx.status = RunStatus.ERROR
                        self.run_ctx.return_code = 221
                        self.run_ctx.message = (
                            "Something went wrong during the execution of "
                            f"model {node.name}. Should have only 1 output.\n"
                            f"Node Id: {node.id}\n"
                            f"Image: {tag}\n"
                            f"cmd: {cmd_secure}\n"
                        )
                        return
                    output_path = output_path[0]
                    storage_path = self.storage_manager.get_full_path(
                        output_path
                    )
                    # update output edges with final output name
                    for oe in node.outputs_edges:
                        if oe.from_port == output.name:
                            oe.value = DataParameterModel(
                                name=output.name,
                                type="Data",
                                url=storage_path,
                                path=output_path,
                            )

            self.task_done(node, group)

        elif node.status == RunStatus.ERROR:
            self.run_ctx.status = RunStatus.ERROR
            self.run_ctx.return_code = 221
            self.run_ctx.message = (
                "Something went wrong during the execution"
                f" of model {node.name}.\n"
                f"Node Id: {node.id}\n"
                f"Image: {tag}\n"
                f"cmd: {cmd_secure}\n"
            )

    async def execute_output_node(self, node: Node, group: asyncio.TaskGroup):
        for ie in node.inputs_edges:
            if isinstance(ie.value, DataParameterModel):
                infos = await asyncio.to_thread(
                    self.storage_manager.get_data_info, ie.value.path
                )
                ie.value.size = infos["size"]
                ie.value.checksum = infos["checksum"]
                output = ie.value
                output.name = node.name
            self.run_ctx.outputs.append(output)

        node.status = RunStatus.SUCCESS
        rcup = RunContextUpdateModel(outputs=self.run_ctx.outputs)
        if self._on_update_run_context:
            self._on_update_run_context(self.run_ctx.id, rcup)
        self.task_done(node, group)

    async def execute_dependency_node(
        self, node: Node, group: asyncio.TaskGroup
    ):
        # create a new run context for the dependency
        inputs = []
        # the name of the Data or primitive Parameter of the edges
        # is the name of the output of the previous node
        # so we need to change the name to match
        # the name of the dependency's input
        for ie in node.inputs_edges:
            _input = ie.value
            _input.name = ie.to_port
            inputs.append(_input)
        run_ctx = RunContext(
            id=str(uuid.uuid4()),
            deltatwin_id=node.element.id,
            deltatwin_version=node.element.version,
            owner=self.run_ctx.owner,
            status=RunStatus.CREATED,
            date_created=self.run_ctx.date_created,
            parent_run=self.run_ctx.id,
            inputs=[
                model_param_to_orm_param(p, ParameterKind.INPUT)
                for p in inputs
            ],
            return_code=0,
            message="",
        )

        run = RunContextModel.from_run_context(run_ctx)
        if self._on_create_sub_run_context:
            self._on_create_sub_run_context(self.run_ctx.id, run_ctx)
        logger.debug(
            "Executing dependecy : %s with run id : %s", node.name, run.id
        )

        orch = DeltaOrchestrator(
            self.storage_manager.get_deltatwin_manifest(
                run.deltatwin_id, run.deltatwin_version
            ),
            self.storage_manager.get_deltatwin_workflow(
                run.deltatwin_id, run.deltatwin_version
            ),
            run,
            self.storage_manager,
            self.job_service,
            on_update_context=self._on_update_run_context,
            on_create_sub_context=self._on_create_sub_run_context,
        )
        await orch.run()
        logger.debug(
            "Dependency %s finished with status %s", node.name, run.status
        )
        # run outputs should correspond to the outputs_edges of the node
        if run.status != RunStatus.SUCCESS:
            self.run_ctx.status = RunStatus.ERROR
            self.run_ctx.return_code = 230
            self.run_ctx.message = (
                f"Error while running dependency {node.name}."
                " See dependency error for more info "
                f"(Dependency run id : {run.id})"
            )
            return

        for oe in node.outputs_edges:
            oe.value = next(
                filter(
                    lambda output: output.name == oe.from_port, run.outputs
                ),
                None,
            )
        self.task_done(node, group)

    def model_done_callback(
        self, node: Node, event: asyncio.Event, old_status, new_status
    ):
        node.status = new_status
        event.set()

    def task_done(self, node: Node, group: asyncio.TaskGroup):
        node.status = RunStatus.SUCCESS
        self._in_degree[node.id] -= 1
        for i in self.graph[node.id]:
            self._in_degree[i] -= 1
            if self._in_degree[i] == 0:
                group.create_task(
                    self.exec_task(self.nodes[i], group),
                    name=self.nodes[i].id,
                )

    def check_inputs(self):
        user_inputs = {i.name: i for i in self.run_ctx.inputs}
        missing_inputs = []
        for k, v in self._manifest.inputs.items():
            if v.value is None and k not in user_inputs:
                missing_inputs.append(k)
            if k in user_inputs:
                if v.type == "Data" and not isinstance(
                    user_inputs[k], DataParameterModel
                ):
                    self.run_ctx.return_code = 110
                    if isinstance(
                            user_inputs[k], SecretParameterModel
                    ):
                        self.run_ctx.message = (
                            f"Input {k} must be of type {v.type} "
                            f"but is of type secret."
                        )
                        raise TypeError(
                            (
                                f"Input {k} must be of type {v.type} "
                                "but is of type secret."
                            )
                        )
                    elif isinstance(
                            user_inputs[k], PrimitiveParameterModel
                    ):
                        self.run_ctx.message = (
                            f"Input {k} must be of type {v.type} "
                            f"but is of type "
                            f"{retrieve_primitive_type(user_inputs[k].value)}."
                        )
                        raise TypeError(
                            f"Input {k} must be of type {v.type} "
                            "but is of type "
                            f"{retrieve_primitive_type(user_inputs[k].value)}."
                        )
                elif v.type == "secret" and not isinstance(
                    user_inputs[k], SecretParameterModel
                ):
                    self.run_ctx.return_code = 110
                    if isinstance(
                            user_inputs[k], DataParameterModel
                    ):
                        self.run_ctx.message = (
                            f"Input {k} must be of type {v.type} "
                            f"but is of type Data."
                        )
                        raise TypeError(
                            f"Input {k} must be of type {v.type} "
                            "but is of type Data."
                        )
                    elif isinstance(
                            user_inputs[k], PrimitiveParameterModel
                    ):
                        self.run_ctx.message = (
                            f"Input {k} must be of type {v.type} "
                            f"but is of type "
                            f"{retrieve_primitive_type(user_inputs[k].value)}."
                        )
                        raise TypeError(
                            f"Input {k} must be of type {v.type} "
                            "but is of type "
                            f"{retrieve_primitive_type(user_inputs[k].value)}."
                        )
                elif (v.type != "Data" and v.type != "secret" and
                      v.type != retrieve_primitive_type(user_inputs[k].value)):
                    self.run_ctx.return_code = 110
                    self.run_ctx.message = (
                        f"Input {k} must be of type {v.type} but is of type"
                        f" {retrieve_primitive_type(user_inputs[k].value)}."
                    )
                    raise TypeError(
                        f"Input {k} must be of type {v.type} "
                        "but is of type "
                        f"{retrieve_primitive_type(user_inputs[k].value)}."
                    )
        if missing_inputs:
            self.run_ctx.return_code = 120
            self.run_ctx.message = f"Inputs {missing_inputs} required."
            raise TypeError(f"Inputs {missing_inputs} required.")

    def are_user_inputs_valid(self):
        is_valid = True
        manifest = self.storage_manager.get_deltatwin_manifest(
            self.run_ctx.deltatwin_id, self.run_ctx.deltatwin_version
        )
        for i in self.run_ctx.inputs:
            input = manifest.inputs.get(i.name, None)
            if input is None:
                logger.error(f"Input {i} is not a valid input")
                is_valid = False
            type = input.get("type", None)
            if type is None:
                logger.error(f"Input {i} has no type")
                is_valid = False
        return is_valid

    def is_valid_dag(self):
        top_sorted = []
        queue = []
        in_degree = self._init_in_degrees(self.graph, self.nodes)
        for i in self.graph:
            if in_degree[i] == 0:
                queue.append(i)

        cnt = 0
        while queue:
            u = queue.pop(0)
            top_sorted.append(u)
            for i in self.graph[u]:
                in_degree[i] -= 1
                if in_degree[i] == 0:
                    queue.append(i)

            cnt += 1

        # Check if there was a cycle
        if cnt != self.number_of_nodes:
            return False
        logger.debug("Possible node execution order: %s", top_sorted)
        return True
