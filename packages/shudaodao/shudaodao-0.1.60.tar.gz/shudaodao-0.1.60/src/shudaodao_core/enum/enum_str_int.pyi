from pydantic import GetCoreSchemaHandler as GetCoreSchemaHandler
from pydantic_core import core_schema
from typing import Any

class EnumInt(int):
    def __new__(cls, value: int): ...
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema: ...

class EnumStr(str):
    def __new__(cls, value: str): ...
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema: ...
