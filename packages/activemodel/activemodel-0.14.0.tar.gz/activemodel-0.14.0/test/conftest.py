import pytest

import activemodel
from . import models  # noqa: F401

from .utils import database_url, drop_all_tables, temporary_tables


def pytest_sessionstart(session):
    "only executes once if a test is run, at the beginning of the test suite execution"

    activemodel.init(database_url())

    # start off by removing all of the tables
    drop_all_tables()


@pytest.fixture(scope="function")
def create_and_wipe_database():
    with temporary_tables():
        yield
