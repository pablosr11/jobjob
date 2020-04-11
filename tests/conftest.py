from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from jobjob.database_app.models import Base  # Base loaded with the models


@pytest.fixture(scope='session')
def engine():
    return create_engine('postgres://postgres:postgres@localhost/test_db')

@pytest.yield_fixture(scope='session')
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function") # scope module?
def db(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()

    # begin the nested transaction
    # transaction = connection.begin()

    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()

    # roll back the broader transaction
    # transaction.rollback()

    # put back the connection to the connection pool
    connection.close()


@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch):
    monkeypatch.setattr(BackgroundTasks, 'add_task', MagicMock)
