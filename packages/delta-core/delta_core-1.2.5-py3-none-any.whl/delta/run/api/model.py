from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from delta.run.db.orm import (
    DataParameter,
    Parameter,
    SecretParameter,
    ParameterKind,
    PrimitiveParameter,
    RunContext,
    RunStatus,
)


class ParameterModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    type: Optional[str] = None


class PrimitiveParameterModel(ParameterModel):
    value: Union[bool, int, float, str]


class SecretParameterModel(ParameterModel):
    secret_value: Union[str, bytes] = Field(repr=False, exclude=True)


class DataParameterModel(ParameterModel):
    url: str
    path: Optional[str] = Field(default=None)
    size: Optional[int] = Field(default=None)
    checksum: Optional[str] = Field(default=None)


def orm_param_to_model_param(param: Parameter) -> ParameterModel:
    if isinstance(param, SecretParameter):
        value = param.secret_value
        return SecretParameterModel(
            name=param.name, secret_value=value, type=param.type
        )
    if isinstance(param, PrimitiveParameter):
        return PrimitiveParameterModel(
            name=param.name, value=param.value, type=param.type
        )
    elif isinstance(param, DataParameter):
        return DataParameterModel(
            name=param.name,
            url=param.url,
            path=param.path,
            size=param.size,
            type=param.type,
            checksum=param.checksum,
        )
    else:
        raise ValueError(f"Unsupported parameter type: {param.type}")


def retrieve_primitive_type(value: Union[bool, int, float, str]):
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        return "string"
    raise ValueError(f"Unsupported primitive parameter type: {type(value)}")


def model_param_to_orm_param(
    param: ParameterModel, kind: ParameterKind
) -> Parameter:
    if isinstance(param, SecretParameterModel):
        return SecretParameter(
            name=param.name,
            param_type="secret_parameter",
            type="secret",
            kind=kind,
            secret_value=param.secret_value
        )
    if isinstance(param, PrimitiveParameterModel):
        return PrimitiveParameter(
            name=param.name,
            param_type="primitive_parameter",
            type=retrieve_primitive_type(param.value),
            kind=kind,
            value=param.value
        )
    elif isinstance(param, DataParameterModel):
        return DataParameter(
            name=param.name,
            param_type="data_parameter",
            type="Data",
            kind=kind,
            url=param.url,
            path=param.path,
            size=param.size,
            checksum=param.checksum,
        )


class RunContextModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    deltatwin_id: str
    deltatwin_version: str = Field(default="main")
    owner: str
    date_created: datetime
    status: RunStatus = Field(default=RunStatus.CREATED)
    return_code: int = Field(default=0)
    message: str = Field(default="")
    parent_run: str = Field(default="")
    inputs: List[Union[PrimitiveParameterModel,
                       DataParameterModel, SecretParameterModel]] = Field(
        default_factory=list
    )
    outputs: List[Union[PrimitiveParameterModel,
                        DataParameterModel, SecretParameterModel]] = Field(
        default_factory=list
    )

    @classmethod
    def from_run_context(cls, run_context: RunContext) -> RunContextModel:
        return cls(
            id=run_context.id,
            deltatwin_id=run_context.deltatwin_id,
            deltatwin_version=run_context.deltatwin_version,
            owner=run_context.owner,
            status=run_context.status,
            date_created=run_context.date_created,
            message=run_context.message,
            return_code=run_context.return_code,
            parent_run=run_context.parent_run,
            inputs=[orm_param_to_model_param(p) for p in run_context.inputs],
            outputs=[orm_param_to_model_param(p) for p in run_context.outputs],
        )


class RunContextInsertModel(BaseModel):
    deltatwin_id: str
    owner: str
    date_created: datetime = Field(
        default_factory=partial(datetime.now, timezone.utc)
    )
    deltatwin_version: str = Field(default="main")
    inputs: List[Union[PrimitiveParameterModel, DataParameterModel,
                       SecretParameterModel]]


class RunContextUpdateModel(BaseModel):
    status: Optional[RunStatus] = None
    return_code: Optional[int] = None
    message: Optional[str] = None
    inputs: Optional[
        List[Union[PrimitiveParameterModel, DataParameterModel,
                   SecretParameterModel]]
    ] = None
    outputs: Optional[
        List[Union[PrimitiveParameterModel, DataParameterModel,
                   SecretParameterModel]]
    ] = None
