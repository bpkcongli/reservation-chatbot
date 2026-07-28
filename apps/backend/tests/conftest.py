from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine


@pytest.fixture
def sqlite_engine() -> Iterator[Engine]:
    database_engine = create_engine("sqlite+pysqlite:///:memory:")
    yield database_engine
    database_engine.dispose()
