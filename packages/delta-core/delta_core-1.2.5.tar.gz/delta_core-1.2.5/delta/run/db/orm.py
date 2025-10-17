import datetime as dt
import enum
from typing import List

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class RunStatus(enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    SUCCESS = "success"
    CANCELLED = "cancelled"
    ERROR = "error"


class ParameterKind(enum.Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class Base(DeclarativeBase):
    pass


class Parameter(Base):
    __tablename__ = 'parameters'
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey('runs.id'))
    name: Mapped[str]
    param_type: Mapped[str]
    type: Mapped[str]
    kind: Mapped[ParameterKind]

    __mapper_args__ = {
        'polymorphic_on': 'param_type',
        'polymorphic_identity': 'parameter'
    }


class PrimitiveParameter(Parameter):
    value: Mapped[str] = mapped_column(nullable=True)

    __mapper_args__ = {'polymorphic_identity': 'primitive_parameter'}


class SecretParameter(Parameter):
    secret_value: Mapped[bytes] = mapped_column(nullable=True)

    __mapper_args__ = {'polymorphic_identity': 'secret_parameter'}


class DataParameter(Parameter):
    url: Mapped[str] = mapped_column(nullable=True)
    path: Mapped[str] = mapped_column(nullable=True)
    size: Mapped[int] = mapped_column(nullable=True)
    checksum: Mapped[str] = mapped_column(nullable=True)

    __mapper_args__ = {'polymorphic_identity': 'data_parameter'}


class RunContext(Base):
    __tablename__ = 'runs'

    id: Mapped[str] = mapped_column(primary_key=True)
    deltatwin_id: Mapped[str]
    deltatwin_version: Mapped[str] = mapped_column(default="main")
    owner: Mapped[str]
    date_created: Mapped[dt.datetime] = mapped_column(
        default=dt.datetime.now(dt.timezone.utc))
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus))
    return_code: Mapped[int] = mapped_column(default=0)
    message: Mapped[str] = mapped_column(default="")
    parent_run: Mapped[str] = mapped_column(default="")
    inputs: Mapped[List[Parameter]] = relationship(
        "Parameter",
        primaryjoin="and_(RunContext.id==Parameter.run_id,"
                    f"Parameter.kind=='{ParameterKind.INPUT.value}')",
        cascade="all, delete-orphan"
    )
    outputs: Mapped[List[Parameter]] = relationship(
        "Parameter",
        primaryjoin="and_(RunContext.id==Parameter.run_id,"
                    f"Parameter.kind=='{ParameterKind.OUTPUT.value}')",
        cascade="all, delete-orphan",
        overlaps='inputs'
    )
