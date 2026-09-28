# TODO collaboration API

A create-only FastAPI service for CHG-TODO-002. TODOs are stored in process memory and disappear when the server restarts.

## Requirements

- Python 3.12+
- `uv` (recommended) or `pip`

## Setup and run

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

The API listens at `http://127.0.0.1:8000`. The approved OpenAPI contract is in `openapi/todo-api.openapi.yaml`.

## API

`POST /todos` accepts:

```json
{"title":"  Buy milk  "}
```

It returns `201` with a server-generated non-empty `id`, trimmed `title`, and `completed: false`.

Missing, blank, non-string, or post-trim titles longer than 100 characters return `400`:

```json
{"code":"INVALID_TITLE","message":"title must contain 1 to 100 characters after trimming"}
```

## Verification

```bash
uv run python -m pytest
uv run python -m ruff check .
uv run python -m mypy app
```
