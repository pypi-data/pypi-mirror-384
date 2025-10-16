from _typeshed import Incomplete
from fastapi.exceptions import RequestValidationError as RequestValidationError
from pydantic import ValidationError as ValidationError
from typing import Any

ERROR_MESSAGES: Incomplete

def format_request_validation_error(
    exc: RequestValidationError,
) -> list[dict[str, Any]]:
    """
    格式化 Pydantic V2 验证错误
    """

def format_pydantic_validation_error(exc: ValidationError) -> list[dict[str, Any]]:
    """
    格式化 Pydantic ValidationError，返回友好错误列表
    """
