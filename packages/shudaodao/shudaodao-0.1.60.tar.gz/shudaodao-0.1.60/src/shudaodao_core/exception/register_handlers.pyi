from ..utils.response_utils import ResponseUtil as ResponseUtil
from .format_valid_error import (
    format_pydantic_validation_error as format_pydantic_validation_error,
    format_request_validation_error as format_request_validation_error,
)
from .service_exception import (
    AuthException as AuthException,
    ShudaodaoException as ShudaodaoException,
)
from fastapi import FastAPI as FastAPI, Request as Request

def register_exception_handlers(app: FastAPI):
    """
    全局异常处理
    """
