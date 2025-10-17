import typing as t
from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from faker import Faker
from sqlalchemy_utils.models import generic_repr

faker = Faker()


metadata = sa.MetaData()


@sa_orm.as_declarative(metadata=metadata)
@generic_repr
class DeclarativeBase:
    pass


chatroom_members_table = sa.Table(
    "chatroom_members",
    metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("user.user_id"), primary_key=True),
    sa.Column(
        "chatroom_id",
        sa.Integer,
        sa.ForeignKey("chatroom.chatroom_id"),
        primary_key=True,
    ),
)


class User(DeclarativeBase):
    __tablename__ = "user"

    user_id: sa_orm.Mapped[int] = sa.Column(
        sa.Integer, autoincrement=True, primary_key=True
    )
    name: sa_orm.Mapped[str] = sa.Column(sa.String, nullable=False, default=faker.name)

    chat_rooms: sa_orm.Mapped[t.List["Chatroom"]] = sa_orm.relationship(
        "Chatroom",
        secondary=chatroom_members_table,
        back_populates="members",
        lazy="raise",
    )

    messages: sa_orm.Mapped[t.List["Message"]] = sa_orm.relationship(
        "Message",
        back_populates="user",
        lazy="raise",
        order_by="desc(Message.created_at)",
        secondary=chatroom_members_table,
        viewonly=True,
    )


class Chatroom(DeclarativeBase):
    __tablename__ = "chatroom"

    chatroom_id: sa_orm.Mapped[int] = sa.Column(
        sa.Integer, autoincrement=True, primary_key=True
    )

    members: sa_orm.Mapped[t.List[User]] = sa_orm.relationship(
        "User",
        secondary=chatroom_members_table,
        back_populates="chat_rooms",
        order_by="asc(User.name)",
        lazy="raise",
    )

    messages: sa_orm.Mapped[t.List["Message"]] = sa_orm.relationship(
        "Message",
        back_populates="chatroom",
        lazy="raise",
        order_by="desc(Message.created_at)",
        secondary=chatroom_members_table,
        viewonly=True,
    )


class Message(DeclarativeBase):
    __tablename__ = "message"

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["chatroom_id", "user_id"],
            [chatroom_members_table.c.chatroom_id, chatroom_members_table.c.user_id],
        ),
    )

    message_id: sa_orm.Mapped[int] = sa_orm.mapped_column(
        sa.Integer, autoincrement=True, primary_key=True
    )
    user_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.Integer, nullable=False)
    chatroom_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.Integer, nullable=False)

    created_at: sa_orm.Mapped[datetime] = sa_orm.mapped_column(
        sa.DateTime(False), nullable=False, default=faker.date_time
    )

    text: sa_orm.Mapped[str] = sa_orm.mapped_column(
        sa.Text, nullable=False, default=faker.sentence
    )

    chatroom: sa_orm.Mapped[Chatroom] = sa_orm.relationship(
        "Chatroom",
        back_populates="messages",
        lazy="raise",
        secondary=chatroom_members_table,
        uselist=False,
        overlaps="chat_rooms,members",
    )

    user: sa_orm.Mapped[User] = sa_orm.relationship(
        "User",
        back_populates="messages",
        lazy="raise",
        secondary=chatroom_members_table,
        uselist=False,
        overlaps="chat_rooms,members,chatroom",
    )
