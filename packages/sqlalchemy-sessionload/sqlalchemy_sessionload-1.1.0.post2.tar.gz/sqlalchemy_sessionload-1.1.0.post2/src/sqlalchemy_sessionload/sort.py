from __future__ import annotations

import operator
import typing as t
from enum import Enum
from functools import partial, total_ordering

import sqlalchemy as sa
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.roles import OrderByRole
from sqlalchemy.sql.selectable import Select


# adapted from: https://giannitedesco.github.io/2019/03/16/sql-sort-python.html
class Order(Enum):
    ASC = 0
    DESC = 1


TSortSpec = t.Tuple[str, Order]


def _cmp_func(*args: TSortSpec):
    spec: t.Iterable[tuple[str, Order]] = args
    cmp_func = lambda a, c, x, y: c(getattr(x, a), getattr(y, a))
    for attr, sense in spec:
        c_eq = partial(cmp_func, attr, operator.eq)
        if sense == Order.ASC:
            c_lt = partial(cmp_func, attr, operator.lt)
        elif sense == Order.DESC:
            c_lt = partial(cmp_func, attr, operator.ge)
        else:
            raise ValueError
        yield (c_lt, c_eq)


def sql_sort_key(*spec: TSortSpec):
    comparators = tuple(_cmp_func(*spec))

    @total_ordering
    class K:
        __slots__ = ["_obj"]
        __hash__ = None  # type: ignore

        def __init__(self, obj):
            self._obj = obj

        def __lt__(self, other):
            for lt_cmp, eq_cmp in comparators:
                if lt_cmp(self._obj, other._obj):
                    return True
                elif not eq_cmp(self._obj, other._obj):
                    return False
            return False

        def __eq__(self, other):
            for _, eq_cmp in comparators:
                if not eq_cmp(self._obj, other._obj):
                    return False
            return True

    return K


def generate_sort_key_spec(clause: OrderByRole) -> TSortSpec:
    if isinstance(clause, UnaryExpression):
        if not isinstance(clause.element, sa.Column):
            raise TypeError(
                f"Cannot handle UnaryExpression with anything other than {type(sa.Column)}"
            )
        column_name = clause.element.name

        if clause.modifier is operators.desc_op:
            return (column_name, Order.DESC)
        return (column_name, Order.ASC)

    if isinstance(clause, sa.Column):
        return (clause.name, Order.ASC)

    raise TypeError(f"Cannot evaluate in {type(clause)} order_by expression")


def construct_sort_key(
    statement: Select,
):
    sort_key_spec = (
        generate_sort_key_spec(clause)
        for clause in statement._order_by_clauses  # type: ignore
    )
    return sql_sort_key(*sort_key_spec)


_T = t.TypeVar("_T")


def sort_with_statement(statement: Select, objects: t.Iterable[_T]) -> list[_T]:
    sort_key = construct_sort_key(statement)
    return sorted(objects, key=sort_key)


def maybe_apply_sort(
    statement: Select, objects: t.Iterable[_T]
) -> list[_T] | t.Iterable[_T]:
    if statement._order_by_clauses:  # type: ignore
        return sort_with_statement(statement, objects)
    return objects
