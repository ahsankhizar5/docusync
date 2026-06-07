import pytest

from app.database import reset_engine_for_tests
from app.settings import get_settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_settings_and_database_engine():
    get_settings.cache_clear()
    reset_engine_for_tests()
    yield
    get_settings.cache_clear()
    reset_engine_for_tests()
