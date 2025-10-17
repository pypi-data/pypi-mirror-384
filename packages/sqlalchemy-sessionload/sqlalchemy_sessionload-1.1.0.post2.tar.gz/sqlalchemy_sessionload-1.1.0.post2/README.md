# sqlalchemy-sessionload

![PyPI - Downloads](https://img.shields.io/pypi/dd/sqlalchemy-sessionload)
[![GitHub license](https://img.shields.io/github/license/jvllmr/sqlalchemy-sessionload)](https://github.com/jvllmr/sqlalchemy-sessionload/blob/dev/LICENSE)
[![Codecov](https://img.shields.io/codecov/c/github/jvllmr/sqlalchemy-sessionload/dev?style=plastic)](https://app.codecov.io/gh/jvllmr/sqlalchemy-sessionload/tree/dev)
[![Routine Checks](https://github.com/jvllmr/sqlalchemy-sessionload/actions/workflows/test.yaml/badge.svg)](https://github.com/jvllmr/sqlalchemy-sessionload/actions/workflows/test.yaml)

SQLAlchemy load option that loads from persisted session instances.

The goal of this load option is to achieve performance gains in specific use-cases by not querying the database or serializing new objects and reading from cache instead. This means that you as a user need to make sure before that all of the objects you expect to find within a query are already present the session store. Use with care!

## Basic usage

SessionLoad is available for basic queries and relationship loading

Filters and Order By constructs are also supported.
If you miss something you are invited to contribute.

For installation the plugin has to be registered:

```python
from sqlalchemy_sessionload import SQLAlchemySessionLoad

Session = sessionmaker(...)
SQLAlchemySessionLoad(Session)
```

### Simple Query

```python
from sqlalchemy_sessionload import SessionLoad
from project.model import Message

# assignment is needed
# otherwise instances are not saved in session
all_messages = session.query(Message).all()

session_messages = session.query(Message).options(SessionLoad(Message)).all()
```

### Load relationship

Joined loading is currently only available with subqueryload.

```python
from sqlalchemy_sessionload import SessionRelationshipLoad
from project.model import Message, User
import sqlalchemy.orm as sa_orm

# assignment is needed
# otherwise instances are not saved in session
all_users = session.query(User).all()


# users connected to messages are now loaded from session
session_messages = (
    session.query(Message)
    .options(sa_orm.subqueryload(Message.user), SessionRelationshipLoad(Message.user))
    .all()
)
```

## Benchmark

A benchmark is available [here](https://jvllmr.github.io/sqlalchemy-sessionload/dev/bench)
