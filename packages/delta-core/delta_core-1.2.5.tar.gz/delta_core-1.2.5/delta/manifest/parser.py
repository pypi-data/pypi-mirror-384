import abc
import dataclasses
import importlib
import inspect
import json
from re import S
from typing import IO, Any, Dict, List, Union

import yaml

from delta.manifest.constants import manifest_version
from delta.manifest.manifest import check_manifest, read_manifest


@dataclasses.dataclass
class Copyright:
    company: str
    years: List[int] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class License:
    name: str
    url: str
    description: str = dataclasses.field(default=None)
    copyrights: List[Copyright] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Parameter:
    name: str
    type: str
    description: str = dataclasses.field(default=None)


@dataclasses.dataclass
class Resource(Parameter):
    value: Any = dataclasses.field(default=None)


@dataclasses.dataclass
class Input(Parameter):
    value: Any = dataclasses.field(default=None)


@dataclasses.dataclass
class InputModel(Input):
    prefix: str = dataclasses.field(default=None)


@dataclasses.dataclass
class Output(Parameter):
    pass


@dataclasses.dataclass
class OutputModel(Output):
    glob: str = dataclasses.field(default=None)


@dataclasses.dataclass
class Model:
    path: str
    type: str
    parameters: Dict[str, Any] = dataclasses.field(default_factory=dict)
    inputs: Dict[str, InputModel] = dataclasses.field(default_factory=dict)
    outputs: Dict[str, OutputModel] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Dependency:
    id: str
    version: str


@dataclasses.dataclass
class Manifest:
    name: str
    description: str
    license: License
    short_description: str = dataclasses.field(default_factory=str)
    owner: str = dataclasses.field(default_factory=str)
    resources: Dict[str, Resource] = \
        dataclasses.field(default_factory=dict)
    inputs: Dict[str, Input] = dataclasses.field(default_factory=dict)
    outputs: Dict[str, Output] = dataclasses.field(default_factory=dict)
    models: Dict[str, Model] = dataclasses.field(default_factory=dict)
    dependencies: Dict[str, Dependency] = dataclasses.field(
        default_factory=dict
    )


class ManifestParser(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def parse_license(cls, data: dict) -> License:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def parse_resource(cls, data: dict) -> Resource:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def parse_input(cls, data: dict) -> Input:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def parse_output(cls, data: dict) -> Output:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def parse_model(cls, data: dict) -> Model:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def parse(cls, data: dict) -> Manifest:
        raise NotImplementedError


def _manifest_parser_filter(obj: Any) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, ManifestParser)
        and obj != ManifestParser
    )


def _parse_from_dict(data: dict) -> Manifest:
    version = data.get("deltaVersion", manifest_version)
    validated = check_manifest(data, version=version, verbose=True)
    if validated is False:
        raise ValueError("Invalid manifest content")

    try:
        module = importlib.import_module(
            f"delta.manifest.v{version.replace('.', '_')}"
        )
    except ModuleNotFoundError:
        module = importlib.import_module(
            f"delta.manifest.v{manifest_version.replace('.', '_')}"
        )
    members = inspect.getmembers(module, predicate=_manifest_parser_filter)

    if not members:
        raise RuntimeError(
            f"No DeltaTwin manifest parser found for version: {version}"
        )
    parser: ManifestParser = members[-1][1]
    return parser.parse(data)


def _parse_from_path(path: str) -> Manifest:
    data = read_manifest(path)
    return _parse_from_dict(data)


def _parse_from_stream(stream: IO) -> Manifest:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError:
        data = json.load(stream)
    return _parse_from_dict(data)


def parse(obj: Union[str, dict, IO]) -> Manifest:
    if isinstance(obj, str):
        return _parse_from_path(obj)
    elif isinstance(obj, IO) or hasattr(obj, "read"):
        return _parse_from_stream(obj)
    return _parse_from_dict(obj)
