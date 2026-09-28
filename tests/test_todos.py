from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app, todos_in_memory

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


def test_in_memory_store_starts_empty_for_each_test() -> None:
    assert todos_in_memory() == ()


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


def test_served_openapi_matches_approved_contract() -> None:
    plan_path = Path(__file__).parents[1] / "openapi" / "todo-api.openapi.yaml"
    approved_contract = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json() == approved_contract
    assert app.openapi() == approved_contract


def test_openapi_documents_only_contract_responses() -> None:
    responses = app.openapi()["paths"]["/todos"]["post"]["responses"]

    assert set(responses) == {"201", "400"}


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_cors_preflight_allows_approved_vite_origins(origin: str) -> None:
    response = client.options(
        "/todos",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-methods"] == "POST, OPTIONS"
    assert "content-type" in response.headers["access-control-allow-headers"].lower().split(", ")


def test_cors_post_allows_approved_vite_origin() -> None:
    origin = "http://localhost:5173"
    response = client.post("/todos", headers={"Origin": origin}, json={"title": "CORS"})

    assert response.status_code == 201
    assert response.headers["access-control-allow-origin"] == origin


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
