from enum import IntEnum
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

class LabelEnum(IntEnum):
    def __new__(cls, value: int, label: str, description: str = ""): ...
    @classmethod
    def from_label(cls, label: str):
        """根据 label 查找枚举成员"""
    @classmethod
    def labels(cls) -> list[str]:
        """获取所有标签"""
    @property
    def label(self) -> str: ...
    @property
    def description(self) -> str: ...
