from __future__ import annotations

import random
import typing as t

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy_sessionload.plugin import SQLAlchemySessionLoad

from .model import Chatroom, Message, User, chatroom_members_table, metadata

engine = create_engine("sqlite:///:memory:", future=True)
Session = sessionmaker(engine)
SQLAlchemySessionLoad(Session)
_T = t.TypeVar("_T")


def random_choice(items: list[_T], min_length: int) -> list[_T]:
    if min_length > len(items):
        raise ValueError("min_length cannot be bigger than amount of given items")
    res = items.copy()
    final_length = random.randint(min_length, len(res))
    # perfect opportunity for performance optimization with walrus operator
    # sadly I want to support py3.8
    # maybe next year
    while len(res) > final_length:
        del res[random.randint(0, len(res) - 1)]

    return res


@pytest.fixture()
def db_session():
    with Session() as session:
        # load everything into session
        messages = session.query(Message).all()
        assert len(messages) > 0
        users = session.query(User).options(sa_orm.joinedload(User.chat_rooms)).all()
        assert len(users) > 0
        chat_rooms = session.query(Chatroom).all()
        assert len(chat_rooms) > 0
        yield session


@pytest.fixture(autouse=True, scope="session")
def generate_testdata():
    metadata.create_all(engine)
    with Session() as session:
        users = [User() for _ in range(50)]
        session.add_all(users)
        chatrooms = [Chatroom() for _ in range(100)]
        session.add_all(chatrooms)
        session.flush()
        for chatroom in chatrooms:
            members = random_choice(users, 2)
            session.execute(
                sa.insert(chatroom_members_table).values(
                    [
                        {"chatroom_id": chatroom.chatroom_id, "user_id": member.user_id}
                        for member in members
                    ]
                )
            )

            messages = [
                Message(
                    user_id=random.choice(members).user_id,
                    chatroom_id=chatroom.chatroom_id,
                )
                for _ in range(random.randint(1, 10))
            ]
            session.add_all(messages)
        session.commit()
