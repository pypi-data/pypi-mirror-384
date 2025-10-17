from __future__ import annotations

import typing as t

from sqlalchemy.orm import Mapper, Session
from sqlalchemy.sql import operators
from sqlalchemy.sql.annotation import AnnotatedColumn  # type: ignore
from sqlalchemy.sql.elements import BinaryExpression, BindParameter, BooleanClauseList
from sqlalchemy.sql.selectable import Select

from sqlalchemy_sessionload.filter import construct_filter_from_statement


def iter_session_mapper_instances(session: Session, mapper: Mapper):
    for instance in session.identity_map.values():
        if isinstance(instance, mapper.class_):
            yield instance


def load_by_primary_key(
    session: Session,
    mapper: Mapper,
    statement: Select,
    identity_token: t.Any | None = None,
):
    """
    Try to load an instance by primary key
    """
    criteria = list(statement._where_criteria)  # type: ignore
    for expr in criteria:
        if isinstance(expr, BooleanClauseList):
            if expr.operator is operators.and_:
                criteria.remove(expr)
                criteria.extend(expr.clauses)
            else:
                return None
    primary_key_names: list[str] = [c.name for c in mapper.primary_key]
    primary_key_values: list[t.Any] = []

    for expr in criteria:
        if not isinstance(expr, BinaryExpression) or expr.operator is not operators.eq:
            return None

        if isinstance(expr.left, AnnotatedColumn) and isinstance(
            expr.right, BindParameter
        ):
            col = expr.left
            val = expr.right
        elif isinstance(expr.left, BindParameter) and isinstance(
            expr.right, AnnotatedColumn
        ):
            col = expr.right
            val = expr.left
        else:
            return None
        col_table = col.table
        col_description = col.description
        if (
            col_table.name != mapper.class_.__tablename__
            or col_description not in primary_key_names
        ):
            return None

        primary_key_values.insert(
            primary_key_names.index(col_description), val.effective_value
        )

    if len(primary_key_values) != len(primary_key_names):
        return None

    return session.identity_map.get(
        (mapper.class_, tuple(primary_key_values), identity_token), None
    )


def load_from_session(session: Session, mapper: Mapper, statement: Select):
    filter_ = construct_filter_from_statement(statement, mapper=mapper)
    return (
        instance
        for instance in filter(
            filter_,
            iter_session_mapper_instances(session, mapper),
        )
    )
