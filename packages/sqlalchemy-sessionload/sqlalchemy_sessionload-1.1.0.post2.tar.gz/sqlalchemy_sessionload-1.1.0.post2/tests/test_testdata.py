# assure our test model and test data works
import sqlalchemy.orm as sa_orm

from .model import Chatroom, Message, User


def test_users_exist(db_session: sa_orm.Session):
    users_count = db_session.query(User).count()

    assert users_count > 0


def test_chat_rooms_exist(db_session: sa_orm.Session):
    chatroom_count = db_session.query(Chatroom).count()

    assert chatroom_count > 0


def test_messages_exist(db_session: sa_orm.Session):
    messages_count = db_session.query(Message).count()

    assert messages_count > 0
