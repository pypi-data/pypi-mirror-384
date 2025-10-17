from __future__ import annotations

import typing as t

from sqlalchemy.sql import operators
from sqlalchemy.sql.annotation import AnnotatedColumn  # type: ignore
from sqlalchemy.sql.elements import (
    BinaryExpression,
    BindParameter,
    BooleanClauseList,
    ClauseElement,
    ClauseList,
    ColumnElement,
    ExpressionClauseList,
    Grouping,
    UnaryExpression,
)
from sqlalchemy.sql.selectable import Select

TSupportedExprs = t.Union[
    BooleanClauseList,
    BinaryExpression,
    ColumnElement,
    UnaryExpression,
    Grouping,
    ClauseElement,
]


def evaluate_expression(expr: TSupportedExprs, **kw) -> t.Callable[[t.Any], t.Any]:
    """
    Evaluate BinaryExpressions of a Select statement to create a filter function which is ready for higher order functions
    """
    op: t.Any  # too lazy to fix typing...
    if isinstance(expr, (BooleanClauseList)) or (
        ExpressionClauseList is not None and isinstance(expr, ExpressionClauseList)
    ):
        eval_clauses = [evaluate_expression(clause, **kw) for clause in expr.clauses]
        if expr.operator is operators.and_:
            return lambda obj: all(clause(obj) for clause in eval_clauses)
        elif expr.operator is operators.or_:
            return lambda obj: any(clause(obj) for clause in eval_clauses)
    elif isinstance(expr, ClauseList):
        return lambda obj: [
            evaluate_expression(clause, **kw)(obj)
            for clause in expr.clauses  # type: ignore
        ]
    elif isinstance(expr, BinaryExpression):
        eval_left = evaluate_expression(expr.left, **kw)
        eval_right = evaluate_expression(expr.right, **kw)
        op = expr.operator
        if op is operators.is_:
            op = lambda a, b: a is b
        elif op is operators.is_not:
            op = lambda a, b: a is not b
        elif op is operators.in_op:
            op = lambda a, b: a in b
        elif op is operators.not_in_op:
            op = lambda a, b: a not in b
        elif op is operators.between_op:
            bounds = (
                evaluate_expression(expr.right.clauses[0], **kw),
                evaluate_expression(expr.right.clauses[1], **kw),
            )

            def between_comparison(obj: t.Any):
                bounds_values = [bound_get(obj) for bound_get in bounds]
                value = eval_left(obj)
                # use min-max for symmetric behavior
                lower = min(bounds_values)
                higher = max(bounds_values)
                return lower <= value and higher >= value

            return between_comparison
        return lambda obj: op(eval_left(obj), eval_right(obj))
    elif isinstance(expr, UnaryExpression):
        eval_expr = evaluate_expression(expr.element, **kw)
        op = expr.operator

        if op is operators.inv:
            op = lambda value: not value

        return lambda obj: op(eval_expr(obj))
    elif isinstance(expr, Grouping):
        eval_expr = evaluate_expression(expr.element, **kw)
        return lambda obj: eval_expr(obj)
    elif isinstance(expr, AnnotatedColumn):
        # try to access attribute from instance
        return lambda obj: getattr(obj, expr.description)
    elif isinstance(expr, BindParameter):
        return lambda obj: expr.effective_value  # type: ignore

    raise TypeError(f"Don't know how to evaluate expression of type {type(expr)}")


def construct_filter_from_statement(
    statement: Select, **kw
) -> t.Callable[[t.Any], bool]:
    """
    Evaluate where criteria expressions of a select statement and return a filter function
    """

    criteria_filters = [
        evaluate_expression(criteria, **kw)
        for criteria in statement._where_criteria  # type: ignore
    ]
    return lambda obj: all(filter_(obj) for filter_ in criteria_filters)
