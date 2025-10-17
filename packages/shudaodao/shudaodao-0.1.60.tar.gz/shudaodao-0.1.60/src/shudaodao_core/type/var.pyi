from sqlmodel import SQLModel
from typing import TypeVar

T = TypeVar("T")
SQLModelDB = TypeVar("SQLModelDB", bound=SQLModel)
SQLModelCreate = TypeVar("SQLModelCreate", bound=SQLModel)
SQLModelUpdate = TypeVar("SQLModelUpdate", bound=SQLModel)
SQLModelResponse = TypeVar("SQLModelResponse", bound=SQLModel)
