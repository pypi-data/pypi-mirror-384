from ..config.app_config import AppConfig as AppConfig
from ..schemas.response import (
    ErrorResponse as ErrorResponse,
    SuccessResponse as SuccessResponse,
)
from fastapi.responses import Response as Response
from typing import Any

class ResponseUtil:
    """
    响应工具类
    """
    @classmethod
    def success(cls, *, message: str = "操作成功", data: Any | None = None) -> Response:
        """
        成功响应方法
        :param message: 可选，成功响应结果中属性为 message 的值
        :param data: 可选，成功响应结果中属性为 data 的值
        :return: 成功响应结果
        """
    @classmethod
    def error(
        cls, *, message: str = "服务器异常", error: Any | None, code: int = 500
    ) -> Response:
        """
        错误响应方法
        :param message: 可选，错误响应结果中属性为 message 的值
        :param code: 可选，错误响应结果中属性为 code 的值
        :param error: 可选，错误响应结果中属性为 data 的值
        :return: 错误响应结果
        """
