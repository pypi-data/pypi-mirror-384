import abc
import asyncio
import dataclasses
import logging
import uuid
from collections import namedtuple
from contextlib import suppress
from delta.run.db.orm import RunStatus
from typing import Callable, List


PathMapper = namedtuple("PathMapper", ["src", "dest"])


@dataclasses.dataclass
class Image:
    tag: str
    registry_url: str = dataclasses.field(default=None)
    registry_username: str = dataclasses.field(default=None)
    registry_password: str = dataclasses.field(default=None)


@dataclasses.dataclass
class Job:
    command: str
    image: Image
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    working_dir: str = dataclasses.field(default=None)
    inputs: List[PathMapper] = dataclasses.field(default_factory=list)
    outputs: List[PathMapper] = dataclasses.field(default_factory=list)
    _status: RunStatus = dataclasses.field(
        init=False, default=RunStatus.CREATED
    )
    _callbacks: List[Callable] = dataclasses.field(
        init=False, default_factory=list
    )

    @property
    def status(self) -> RunStatus:
        return self._status

    @status.setter
    def status(self, new: RunStatus):
        old = self._status
        self._status = new
        for callback in self._callbacks:
            callback(old, new)

    def add_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def __repr__(self):
        return (
            f"Job(command={self.command!r}, image={self.image!r}, "
            f"inputs={self.inputs!r}, outputs={self.outputs!r})"
        )

    def __str__(self):
        return self.__repr__()


class JobChecker:
    def __init__(self, func, time):
        self.func = func
        self.time = time
        self.started = False
        self._task = None

    async def start(self):
        if not self.started:
            self.started = True
            self._task = asyncio.ensure_future(self._check())

    async def stop(self):
        if self.started:
            self.started = False
            self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task

    async def _check(self):
        while True:
            await asyncio.sleep(self.time)
            self.func()


class JobService(abc.ABC):
    def __init__(self, check_interval: int = 5):
        self._logger = logging.getLogger("JobService")
        self._jobs: dict[uuid.UUID, Job] = {}
        self.__interval = check_interval
        self.__checker = None

    async def __aenter__(self):
        if self.__checker is None:
            self.__checker = JobChecker(self.check_jobs, self.__interval)
        await self.__checker.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__checker.stop()

    @abc.abstractmethod
    async def execute_job(self, job: Job):
        raise NotImplementedError

    @abc.abstractmethod
    def check_jobs(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def shutdown(self):
        raise NotImplementedError
