import logging
import os
import tarfile
import tempfile
from typing import Callable

import docker

from delta.drive.interfaces import IDrive
from delta.manifest.parser import Model, parse
from delta.run.job.builder import JobBuilder
from delta.run.job.builder.python_builder import PythonRunner


class DeltaTypeError(Exception):
    pass


class DeltaIllegalError(Exception):
    pass


class DeltaDrive:

    def __init__(self):
        self._repo_directory = "."

    @property
    def repo_directory(self):
        return self._repo_directory

    @repo_directory.setter
    def repo_directory(self, directory):
        self._repo_directory = directory

    @staticmethod
    def get_runner_factory(kind: str) -> Callable[[Model], JobBuilder]:
        if kind == "python":
            return PythonRunner
        raise ValueError(f"Unknown runner kind '{kind}'")

    @staticmethod
    def generate_docker_build_context(
        path: str, dockerfile_content: str
    ) -> str:
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as ctx:
            with tempfile.NamedTemporaryFile() as dockerfile:
                dockerfile.write(dockerfile_content.encode(encoding="utf-8"))
                dockerfile.flush()
                with tarfile.open(ctx.name, "w") as tar:
                    tar.add(path, arcname=".")
                    tar.add(
                        dockerfile.name, arcname="Dockerfile", recursive=False
                    )
            return ctx.name

    def docker_build(
        self,
        version: str = "dev",
        registry: str = None,
        no_cache: bool = False,
    ):
        manifest_json = parse(
            os.path.join(self._repo_directory, "manifest.json")
        )
        if not manifest_json.models:
            logging.info(f"No models images to build")
            return
        for name, model in manifest_json.models.items():
            logging.info(f"Building image for '{name}' model.")
            # retrieve runner
            runner = self.get_runner_factory(model.type)(model)
            # generate dockerfile via the runner
            dockerfile_str = runner.generate_dockerfile()
            # generate docker build context
            context = self.generate_docker_build_context(
                os.path.join(self._repo_directory, model.path), dockerfile_str
            )
            # perform docker build
            try:
                with open(context, "rb") as ctx:
                    tag = f"{manifest_json.name}/{name}:{version}"
                    if registry is not None:
                        tag = f"{registry}/{tag}"
                    cli = docker.from_env()
                    cli.images.build(
                        custom_context=True,
                        rm=True,
                        fileobj=ctx,
                        tag=tag,
                        platform="linux/amd64",
                        nocache=no_cache,
                    )
                    logging.info(f"'{name}' model image successfully built.")
            except docker.errors.DockerException as ex:
                logging.error("Error during docker build")
                raise ex
            finally:
                # remove docker build
                os.remove(context)
