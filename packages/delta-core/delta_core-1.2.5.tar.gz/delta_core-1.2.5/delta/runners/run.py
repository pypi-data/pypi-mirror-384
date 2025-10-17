import inspect
import logging
import platform
import importlib.metadata
from abc import ABC, abstractmethod
from typing import Callable, Iterable, Optional
from delta.exceptions.runners import DeltaRunnerNotFound


_entry_point_name = 'delta.runner'
_runners = None


# Define the DeltaRun interface
class DeltaRun(ABC):

    def __init__(self, parameters: Optional[dict] = None):
        self._parameters = parameters or {}

    @abstractmethod
    def configure(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def start(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def stop(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def resume(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def monitor(self, **kwargs):
        raise NotImplementedError


def _get_entry_points(name: str) -> Iterable[importlib.metadata.EntryPoint]:
    version = platform.python_version()
    major, minor, patch = map(lambda x: int(x), version.split('.'))
    eps = importlib.metadata.entry_points()

    # Python 3.8 & 3.9 importlib.metadata.entry_points() -> dict
    if minor == 8 or minor == 9:
        if name in eps:
            return eps[name]

    # Python 3.10+ importlib.metadata.entry_points() -> Collection
    elif minor >= 10:
        if name in eps.groups:
            return eps.select(group=name)

    return []


def _filter_runner_by_name(name: str):
    """
    Returns specific lambda checking if the given object is a class, and it
    names as the given name.
    """
    return lambda obj: inspect.isclass(obj) and obj.__name__ == name


def _load_runners():
    """
    Loads runners defined in the Python environment via the entry point
    mechanism.
    """
    for entry_point in _get_entry_points(_entry_point_name):
        if entry_point.name in _runners:
            logging.warning(
                f'Runner({entry_point.name},{entry_point.value}) skipped '
                f'caused by runner name ({entry_point.name}) already used')
            continue

        module_path, class_name = entry_point.value.split(':')
        try:
            module = importlib.import_module(module_path)

            members = inspect.getmembers(module,
                                         _filter_runner_by_name(class_name))
            if len(members) != 1:
                raise DeltaRunnerNotFound(
                    f'DeltaRun not found at: {entry_point.value}')

            _, obj = members[0]
            if not issubclass(obj, DeltaRun):
                raise TypeError(f'{entry_point.value} is not a DeltaRun')

            _runners[entry_point.name] = obj
        except ModuleNotFoundError:
            logging.error(f'module {module_path} not found')
        except Exception as ex:
            logging.error('an error occurred during loading runner '
                          f'"{entry_point.name}": {ex}')


def get(name: str) -> Callable:
    if name not in _runners:
        raise KeyError(f'Runner not found: {name}')
    return _runners[name]


if _runners is None:
    _runners = {}
    _load_runners()
