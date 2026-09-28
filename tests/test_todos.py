import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
INVALID_TITLE_MESSAGE = "title must contain 1 to 100 characters after trimming"


def test_create_todo_trims_title_and_returns_contract_response() -> None:
    response = client.post("/todos", json={"title": "  Buy milk  "})

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], str)
    assert body["id"]
    assert body["title"] == "Buy milk"
    assert body["completed"] is False


def test_create_todo_assigns_distinct_opaque_ids() -> None:
    first = client.post("/todos", json={"title": "First"}).json()
    second = client.post("/todos", json={"title": "Second"}).json()

    assert first["id"] != second["id"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 101},
        {"title": " " + "x" * 101 + " "},
    ],
)
def test_invalid_title_returns_contract_error(payload: dict[str, str]) -> None:
    response = client.post("/todos", json=payload)

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_TITLE",
        "message": INVALID_TITLE_MESSAGE,
    }


def test_openapi_documents_only_contract_responses() -> None:
    responses = app.openapi()["paths"]["/todos"]["post"]["responses"]

    assert set(responses) == {"201", "400"}


def test_unexpected_properties_return_contract_error() -> None:
    response = client.post("/todos", json={"title": "Buy milk", "completed": True})

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_TITLE",
        "message": INVALID_TITLE_MESSAGE,
    }


def test_non_string_title_returns_contract_error() -> None:
    response = client.post("/todos", json={"title": 7})

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_TITLE",
        "message": INVALID_TITLE_MESSAGE,
    }


def test_missing_request_body_returns_contract_error() -> None:
    response = client.post("/todos")

    assert response.status_code == 400
    assert response.json() == {
        "code": "INVALID_TITLE",
        "message": INVALID_TITLE_MESSAGE,
    }
