from __future__ import annotations

import typing as t
from abc import ABCMeta, abstractmethod

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.interfaces import UserDefinedOption
from sqlalchemy.orm.path_registry import PropRegistry
from sqlalchemy.orm.session import ORMExecuteState
from sqlalchemy.sql.selectable import Select

from .loaders import load_by_primary_key, load_from_session
from .sort import maybe_apply_sort


class SessionLoadOption(UserDefinedOption, metaclass=ABCMeta):
    @abstractmethod
    def is_active(self, orm_execute_state: ORMExecuteState) -> bool:
        """
        Check if statement is the target of this Option instance
        """

    @abstractmethod
    def handle(self, orm_execute_state: ORMExecuteState) -> t.Iterator[t.Any]:
        """
        Load from session and return instance objects
        """


def default_handle(
    orm_execute_state: ORMExecuteState, identity_token: t.Any | None = None
):
    if orm_execute_state.bind_mapper is None:  # pragma: no cover
        raise ValueError("Cannot do session load with no mapper present")
    statement: Select = orm_execute_state.statement  # type: ignore
    instance = load_by_primary_key(
        orm_execute_state.session,
        orm_execute_state.bind_mapper,
        statement,
        identity_token=identity_token,
    )
    if instance is not None:
        return [instance]

    yield from maybe_apply_sort(
        statement,
        load_from_session(
            orm_execute_state.session, orm_execute_state.bind_mapper, statement
        ),
    )


class SessionLoad(SessionLoadOption):
    def __init__(
        self, mapped_class: type[t.Any], identity_token: t.Any | None = None
    ) -> None:
        self.mapped_class = mapped_class
        self.identity_token = identity_token

    def is_active(self, orm_execute_state: ORMExecuteState) -> bool:
        return bool(
            not orm_execute_state.is_relationship_load
            and not orm_execute_state.is_column_load
            and orm_execute_state.bind_mapper
            and orm_execute_state.bind_mapper.class_ == self.mapped_class
        )

    def handle(self, orm_execute_state: ORMExecuteState) -> t.Iterator[t.Any]:
        return default_handle(orm_execute_state, self.identity_token)


class SessionRelationshipLoad(SessionLoadOption):
    def __init__(
        self, *path: InstrumentedAttribute, identity_token: t.Any | None = None
    ) -> None:
        if len(path) < 1:
            raise ValueError("Relationship path cannot be empty")
        self.path = path
        self.identity_token = identity_token

    def is_active(self, orm_execute_state: ORMExecuteState) -> bool:
        target_mapper = self.path[-1].class_.__mapper__

        strategy_path = orm_execute_state.loader_strategy_path
        if not strategy_path:
            return False

        return (
            orm_execute_state.is_orm_statement
            and orm_execute_state.is_relationship_load
            and isinstance(strategy_path, PropRegistry)
            and strategy_path.mapper is target_mapper
        )

    def handle(self, orm_execute_state: ORMExecuteState) -> t.Iterator[t.Any]:
        return default_handle(orm_execute_state, self.identity_token)
