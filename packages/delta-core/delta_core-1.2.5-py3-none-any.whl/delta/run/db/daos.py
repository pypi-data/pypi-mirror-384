from typing import Sequence

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, select, update

from delta.run.api.model import RunContextUpdateModel, model_param_to_orm_param
from delta.run.db.orm import Parameter, ParameterKind, RunContext, RunStatus
from datetime import datetime, timedelta


def get_runs(
    session: Session,
    dt_id: str = None,
    owner: str = None,
    status: RunStatus = None,
    limit: int = 0,
    offset: int = 0,
) -> Sequence[RunContext]:
    stmt = session.query(RunContext)
    if dt_id is not None:
        stmt = stmt.filter(RunContext.deltatwin_id == dt_id)
    if owner is not None:
        stmt = stmt.filter(RunContext.owner == owner)
    if status is not None:
        stmt = stmt.filter(RunContext.status == status)
    if limit > 0:
        stmt = stmt.limit(limit)
    if offset > 0:
        stmt = stmt.offset(offset)
    return session.scalars(stmt).all()


def add_run(session: Session, run: RunContext) -> RunContext:
    session.add(run)
    return session.get_one(RunContext, run.id)


def update_run(session: Session, run_id, run: RunContextUpdateModel):
    db_run_ctx = get_run_by_id(session, run_id)
    if run.status:
        db_run_ctx.status = run.status
    if run.return_code:
        db_run_ctx.return_code = run.return_code
    if run.message:
        db_run_ctx.message = run.message
    if run.inputs:
        inputs = [
            model_param_to_orm_param(p, ParameterKind.INPUT)
            for p in run.inputs
        ]
        db_run_ctx.inputs = inputs
    if run.outputs:
        outputs = [
            model_param_to_orm_param(p, ParameterKind.OUTPUT)
            for p in run.outputs
        ]
        db_run_ctx.outputs = outputs


def get_run_by_id(session: Session, id_: str) -> RunContext:
    return session.get_one(RunContext, id_)


def get_runs_by_date(session: Session,
                     threshold_date: datetime) -> Sequence[RunContext]:
    stmt = session.query(RunContext).filter(
        RunContext.date_created < threshold_date)
    return session.scalars(stmt).all()


def delete_run(session: Session, run_id: str):
    run = get_run_by_id(session, run_id)
    if run:
        session.delete(run)
        session.commit()


def get_data_output(
    session: Session, run_id: str, name_output: str, type_output: str
) -> Sequence[Parameter]:
    stmt = session.query(Parameter)
    if run_id is not None:
        stmt = stmt.filter(Parameter.run_id == run_id)
    if name_output is not None:
        stmt = stmt.filter(Parameter.name == name_output)
    if type_output is not None:
        stmt = stmt.filter(Parameter.type == type_output)

    stmt = stmt.filter(Parameter.kind == ParameterKind.OUTPUT)

    return session.scalars(stmt).all()


def get_number_of_run_by_user(session: Session, user: str) -> int:
    now = datetime.now()
    threshold_date = now - timedelta(hours=24)
    stmt = (
        select(func.count())
        .select_from(RunContext)
        .where(
            and_(
                RunContext.date_created > threshold_date,
                RunContext.owner == user,
                RunContext.parent_run == "",
                RunContext.return_code != 410,
            )
        )
    )
    return session.scalar(stmt)


def set_running_runs_to_error_at_startup(session: Session):
    stmt = (
        update(RunContext)
        .where(RunContext.status == RunStatus.RUNNING)
        .values(
            status=RunStatus.ERROR,
            return_code=410,
            message="Unexpected error, please retry later.",
        )
    )
    session.execute(stmt)
    session.commit()
