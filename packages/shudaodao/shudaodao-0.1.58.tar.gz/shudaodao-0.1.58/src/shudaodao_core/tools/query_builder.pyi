from ..exception.service_exception import (
    raise_request_validation_error as raise_request_validation_error,
)
from ..schemas.query_request import (
    Condition as Condition,
    QueryLogicOperation as QueryLogicOperation,
    QueryRequest as QueryRequest,
    QuerySimpleCondition as QuerySimpleCondition,
)
from ..type.var import SQLModelDB as SQLModelDB, SQLModelResponse as SQLModelResponse
from .query_field import (
    convert_datetime_iso_to_standard as convert_datetime_iso_to_standard,
    get_class_fields_with_sa_type as get_class_fields_with_sa_type,
)
from .tenant_checker import TenantManager as TenantManager
from sqlmodel import SQLModel as SQLModel
from typing import Any

class QueryBuilder:
    """将 QueryRequest 转换为 SQLModel 查询条件"""
    @classmethod
    def build_list(
        cls,
        query_fields,
        items,
        model_class: type[SQLModelDB],
        response_class: type[SQLModelResponse] = None,
    ): ...
    @staticmethod
    def get_order_by(query: QueryRequest, model_class: type[SQLModel]) -> Any: ...
    @classmethod
    def get_fields(cls, query: QueryRequest, model_class: type[SQLModel]) -> Any: ...
    @classmethod
    def get_where(cls, condition: Condition, model_class: type[SQLModel]) -> Any: ...
    @staticmethod
    def get_condition_python_value(field, field_type, field_value): ...
    @classmethod
    def method_name(cls, fields, item, tag) -> None: ...
    @classmethod
    def build_tree(cls, items, *, query: QueryRequest, model_class, response_class): ...
    @classmethod
    def check_query_request(cls, query) -> None: ...
