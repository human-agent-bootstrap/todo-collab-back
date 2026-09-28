from collections.abc import Sequence
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator

INVALID_TITLE_MESSAGE = "title must contain 1 to 100 characters after trimming"

app = FastAPI(title="TODO API — CHG-TODO-002", version="0.1.0")
_todos: list["Todo"] = []


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    title: str

    @field_validator("title")
    @classmethod
    def trim_and_validate_title(cls, value: str) -> str:
        title = value.strip()
        if not 1 <= len(title) <= 100:
            raise ValueError(INVALID_TITLE_MESSAGE)
        return title


class Todo(BaseModel):
    id: str
    title: str
    completed: bool = False


class ErrorResponse(BaseModel):
    code: str = "INVALID_TITLE"
    message: str = INVALID_TITLE_MESSAGE


def invalid_title_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse().model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _request: Request, _exception: RequestValidationError
) -> JSONResponse:
    return invalid_title_response()


def custom_openapi() -> dict[str, object]:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    del schema["paths"]["/todos"]["post"]["responses"]["422"]
    app.openapi_schema = schema
    return schema


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
    todo = Todo(id=str(uuid4()), title=todo_create.title)
    _todos.append(todo)
    return todo


def todos_in_memory() -> Sequence[Todo]:
    return tuple(_todos)
