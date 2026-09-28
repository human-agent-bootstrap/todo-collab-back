from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Any, Literal, cast
from uuid import uuid4

import yaml
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.cors import CORSMiddleware

INVALID_TITLE_MESSAGE = "title must contain 1 to 100 characters after trimming"

app = FastAPI(title="TODO API — CHG-TODO-002", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
_todos: list["Todo"] = []

Title = Annotated[str, Field(min_length=1, max_length=100, pattern=r".*\S.*")]
StoredTitle = Annotated[str, Field(min_length=1, max_length=100)]


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    title: Title

    @field_validator("title", mode="before")
    @classmethod
    def trim_and_validate_title(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class Todo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(min_length=1)]
    title: StoredTitle
    completed: Literal[False]


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Literal["INVALID_TITLE"] = Field(
        json_schema_extra={"enum": ["INVALID_TITLE"]}
    )
    message: Annotated[str, Field(min_length=1)]


def invalid_title_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            code="INVALID_TITLE", message=INVALID_TITLE_MESSAGE
        ).model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _request: Request, _exception: RequestValidationError
) -> JSONResponse:
    return invalid_title_response()


CONTRACT_PATH = Path(__file__).parents[1] / "openapi" / "todo-api.openapi.yaml"


def custom_openapi() -> dict[str, object]:
    if app.openapi_schema:
        return app.openapi_schema

    with CONTRACT_PATH.open(encoding="utf-8") as contract_file:
        app.openapi_schema = cast(dict[str, object], yaml.safe_load(contract_file))
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.post(
    "/todos",
    response_model=Todo,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "The title is missing, blank after trimming, or longer than 100 characters.",
        }
    },
)
def create_todo(todo_create: TodoCreate) -> Todo:
    todo = Todo(id=str(uuid4()), title=todo_create.title, completed=False)
    _todos.append(todo)
    return todo


def todos_in_memory() -> Sequence[Todo]:
    return tuple(_todos)
