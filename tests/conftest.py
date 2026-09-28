import pytest

from app.main import _todos


@pytest.fixture(autouse=True)
def reset_in_memory_todos() -> None:
    _todos.clear()
