from __future__ import annotations

import typing as t

import sqlalchemy.orm as sa_orm
from sqlalchemy import event
from sqlalchemy.engine.result import IteratorResult, SimpleResultMetaData
from sqlalchemy.orm.session import ORMExecuteState

from .options import SessionLoadOption


def is_query_api(orm_execute_state: ORMExecuteState) -> bool:
    return getattr(
        orm_execute_state.execution_options.get("_sa_orm_load_options", None),
        "_legacy_uniquing",
        False,
    )


class QueryAPIIteratorResult(IteratorResult):
    @property
    def _row_getter(self):
        return None


class SQLAlchemySessionLoad:
    def __init__(self, session_factory: sa_orm.sessionmaker[t.Any]) -> None:
        event.listen(session_factory, "do_orm_execute", self.receive_orm_execute)

    def handle_select(
        self,
        orm_execute_state: ORMExecuteState,
        plugin_options: t.Sequence[SessionLoadOption],
    ):
        if orm_execute_state.bind_mapper is None:  # pragma: no cover
            raise ValueError("Cannot do session load with no mapper present")
        for option in plugin_options:
            if option.is_active(orm_execute_state):
                result_iterator = option.handle(orm_execute_state)

                result_metadata = SimpleResultMetaData(
                    [orm_execute_state.bind_mapper.class_.__name__]
                )

                if not orm_execute_state.is_relationship_load and is_query_api(
                    orm_execute_state
                ):
                    return QueryAPIIteratorResult(result_metadata, result_iterator)
                return IteratorResult(
                    result_metadata, map(lambda obj: (obj,), result_iterator)
                )

    def receive_orm_execute(self, orm_execute_state: ORMExecuteState):
        if orm_execute_state.is_orm_statement and orm_execute_state.is_select:
            plugin_options: list[SessionLoadOption] = [
                option
                for option in orm_execute_state.user_defined_options
                if isinstance(option, SessionLoadOption)
            ]

            if plugin_options:
                return self.handle_select(orm_execute_state, plugin_options)
