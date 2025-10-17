from __future__ import annotations

import random
import typing as t

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

from sqlalchemy_sessionload.filter import (
    TSupportedExprs,
    construct_filter_from_statement,
    evaluate_expression,
)

from .model import Message

TExprFactory = t.Callable[[Message], TSupportedExprs]


def basic_expr_test(
    db_session: sa_orm.Session,
    matching_filter_exprs: list[TExprFactory],
    no_match_filter_exprs: list[TExprFactory],
):
    message: Message | None = db_session.query(Message).first()
    assert message is not None
    for no_match_filter_expr in no_match_filter_exprs:
        no_match_filter = evaluate_expression(no_match_filter_expr(message))
        assert no_match_filter(message) is False

    for matching_filter_expr in matching_filter_exprs:
        matching_filter = evaluate_expression(matching_filter_expr(message))
        assert matching_filter(message) is True


def test_expr_equal(db_session: sa_orm.Session):
    basic_expr_test(
        db_session,
        [
            lambda message: Message.message_id == message.message_id,
            lambda message: message.message_id == Message.message_id,
        ],
        [lambda _: Message.message_id == 0, lambda _: 0 == Message.message_id],
    )


def test_expr_and(db_session):
    basic_expr_test(
        db_session,
        [
            lambda message: sa.and_(
                Message.message_id == message.message_id,
                Message.chatroom_id == message.chatroom_id,
            )
        ],
        [
            lambda message: sa.and_(
                Message.message_id == 0,
                Message.chatroom_id == message.chatroom_id,
            ),
            lambda message: sa.and_(
                Message.message_id == message.message_id,
                Message.chatroom_id == 0,
            ),
            lambda message: sa.and_(
                Message.message_id == 0,
                Message.chatroom_id == 0,
            ),
        ],
    )


def test_expr_or(db_session):
    basic_expr_test(
        db_session,
        [
            lambda message: sa.or_(
                Message.message_id == message.message_id,
                Message.chatroom_id == message.chatroom_id,
            ),
            lambda message: sa.or_(
                Message.message_id == 0,
                Message.chatroom_id == message.chatroom_id,
            ),
            lambda message: sa.or_(
                Message.message_id == message.message_id,
                Message.chatroom_id == 0,
            ),
        ],
        [
            lambda _: sa.and_(
                Message.message_id == 0,
                Message.chatroom_id == 0,
            ),
        ],
    )


def test_expr_greater(db_session):
    basic_expr_test(
        db_session,
        [
            lambda message: sa.and_(
                Message.message_id > message.message_id - 1,
                message.message_id + 1 > Message.message_id,
            )
        ],
        [lambda _: 0 > Message.message_id],
    )


def test_expr_greater_equal(db_session):
    basic_expr_test(
        db_session,
        [
            lambda message: sa.and_(
                Message.message_id >= message.message_id - 1,
                message.message_id + 1 >= Message.message_id,
                Message.message_id >= message.message_id,
            )
        ],
        [lambda _: 0 >= Message.message_id],
    )


def test_expr_lower(db_session):
    basic_expr_test(
        db_session,
        [
            lambda message: sa.and_(
                Message.message_id < message.message_id + 1,
                message.message_id - 1 < Message.message_id,
            )
        ],
        [lambda _: Message.message_id < 0],
    )


def test_expr_lower_equal(db_session):
    basic_expr_test(
        db_session,
        [
            lambda message: sa.and_(
                Message.message_id <= message.message_id + 1,
                message.message_id - 1 <= Message.message_id,
                Message.message_id <= message.message_id,
            )
        ],
        [lambda _: Message.message_id <= 0],
    )


def test_expr_not_equal(db_session):
    basic_expr_test(
        db_session,
        [lambda _: Message.message_id != 0],
        [lambda message: Message.message_id != message.message_id],
    )


def test_expr_not(db_session):
    # inverse of and test
    basic_expr_test(
        db_session,
        [
            lambda message: sa.not_(
                sa.and_(
                    Message.message_id == 0,
                    Message.chatroom_id == message.chatroom_id,
                )
            ),
            lambda message: sa.not_(
                sa.and_(
                    Message.message_id == message.message_id,
                    Message.chatroom_id == 0,
                )
            ),
            lambda message: sa.not_(
                sa.and_(
                    Message.message_id == 0,
                    Message.chatroom_id == 0,
                )
            ),
        ],
        [
            lambda message: sa.not_(
                sa.and_(
                    Message.message_id == message.message_id,
                    Message.chatroom_id == message.chatroom_id,
                )
            )
        ],
    )


def test_expr_is(db_session: sa_orm.Session):
    basic_expr_test(
        db_session,
        [
            lambda message: Message.message_id.is_(message.message_id),
        ],
        [lambda _: Message.message_id.is_(0)],
    )


def test_expr_is_not(db_session: sa_orm.Session):
    basic_expr_test(
        db_session,
        [lambda _: Message.message_id.is_not(0)],
        [
            lambda message: Message.message_id.is_not(message.message_id),
        ],
    )


def test_expr_in(db_session: sa_orm.Session):
    basic_expr_test(
        db_session,
        [
            lambda message: Message.message_id.in_([message.message_id]),
        ],
        [lambda _: Message.message_id.in_([0])],
    )


def test_expr_not_in(db_session: sa_orm.Session):
    basic_expr_test(
        db_session,
        [lambda _: Message.message_id.not_in([0])],
        [
            lambda message: Message.message_id.not_in([message.message_id]),
        ],
    )


def test_expr_between(db_session: sa_orm.Session):
    basic_expr_test(
        db_session,
        [lambda _: Message.message_id.between(0, 1000)],
        [
            lambda message: Message.message_id.between(-1000, 0),
        ],
    )


def test_construct_filter_simple_test(db_session: sa_orm.Session):
    messages: list[Message] = db_session.query(Message).all()
    selected_message = random.choice(messages)
    filter_ = construct_filter_from_statement(
        sa.select(Message).where(
            Message.message_id == selected_message.message_id,
            Message.chatroom_id == selected_message.chatroom_id,
        )
    )
    for message in messages:
        if message is selected_message:
            assert filter_(message) is True
        else:
            assert filter_(message) is False
