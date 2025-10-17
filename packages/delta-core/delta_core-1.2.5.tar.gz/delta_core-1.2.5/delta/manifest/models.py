from typing import Any, Literal

from pydantic import BaseModel, Field

PARAMETER_IDENTIFIER_PATTERN: str = r"^[a-z][a-zA-Z0-9_]{0,31}$"
ParameterType = Literal[
    "boolean", "integer", "number", "string", "Data", "DriveData"
]


class Copyright(BaseModel):
    company: str = ""
    years: list[int] = [2024]


class License(BaseModel):
    name: str = "LGPLv3"
    url: str = "https://www.gnu.org/licenses/gpl-3.0.txt"
    description: str = ""
    copyrights: list[Copyright] = Field(default=[Copyright(
        company="GAEL Systems",
        years=[2023, 2024]
    )])


class Parameter(BaseModel):
    name: str = Field(pattern=PARAMETER_IDENTIFIER_PATTERN)
    type: ParameterType
    description: str | None = Field(default=None)


class Resource(Parameter):
    value: Any


class Input(Parameter):
    value: Any | None = None


class InputModel(Input):
    prefix: str | None = None


class Output(Parameter):
    pass


class OutputModel(Output):
    glob: str


class Model(BaseModel):
    path: str
    type: str
    parameters: dict[str, Any] | None = None
    inputs: dict[str, InputModel] | None = None
    outputs: dict[str, OutputModel] | None = None


class Dependency(BaseModel):
    id: str = Field(pattern=PARAMETER_IDENTIFIER_PATTERN)
    version: str


class Manifest(BaseModel):
    name: str
    description: str
    license: License = Field(default_factory=License)
    short_description: str | None = Field(default=None)
    owner: str
    resources: dict[str, Resource] = Field(default_factory=dict)
    inputs: dict[str, Input] = Field(default_factory=dict)
    outputs: dict[str, Output] = Field(default_factory=dict)
    models: dict[str, Model] = Field(default_factory=dict)
    dependencies: dict[str, Dependency] = Field(default_factory=dict)
