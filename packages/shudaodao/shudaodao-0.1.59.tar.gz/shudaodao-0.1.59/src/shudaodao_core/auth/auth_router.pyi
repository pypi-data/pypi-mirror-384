from ..exception.service_exception import ServiceErrorException as ServiceErrorException
from ..services.auth_service import AuthService as AuthService
from ..services.db_engine_service import DBEngineService as DBEngineService
from .auth_data_rule import AuthDataRule as AuthDataRule
from _typeshed import Incomplete
from fastapi import APIRouter, Request as Request
from sqlmodel.ext.asyncio.session import AsyncSession

class AuthRouter(APIRouter):
    """增强版 APIRouter，支持自动注入权限校验依赖。

    在路由注册时自动绑定用户认证、角色检查、数据权限（Casbin）等依赖。
    同时收集权限规则用于后续初始化默认策略（如插入数据库）。

    Class Attributes:
        permission_rules (dict): 静态字典，用于收集所有默认角色的权限规则，
            格式：{role: {obj: [act1, act2, ...]}}，供应用启动时批量初始化 Casbin 策略。
    """

    permission_rules: Incomplete
    default_role: Incomplete
    auth_role: Incomplete
    auth_obj: Incomplete
    auth_act: Incomplete
    db_config: Incomplete
    data_rules: list[AuthDataRule]
    def __init__(
        self,
        default_role: str | None = None,
        auth_role: str | None = None,
        auth_obj: str | None = None,
        auth_act: str | None = None,
        db_config_name: str | None = None,
        *args,
        **kwargs,
    ) -> None:
        """初始化 AuthRouter 实例。

        Args:
            default_role (Optional[str]): 默认角色，用于自动收集权限规则。
            auth_role (Optional[str]): 默认角色校验规则（可被单个路由覆盖）。
            auth_obj (Optional[str]): 默认数据对象（Casbin 中的 obj）。
            auth_act (Optional[str]): 默认操作行为（Casbin 中的 act）。
            db_config_name (Optional[str]): 数据库配置名称，用于 get_async_session。
            *args: 透传给父类 APIRouter。
            **kwargs: 透传给父类 APIRouter。
        """
    async def get_async_session(self) -> AsyncSession:
        """提供依赖注入用的异步数据库会话。

        该方法设计为配合 FastAPI 的 Depends 使用，需在构造时指定 db_config_name。

        Yields:
            AsyncSession: 异步数据库会话对象。

        Raises:
            ServiceErrorException: 若未设置 db_config_name，则抛出服务异常。
        """
    def api_route(
        self,
        path: str,
        *,
        auth: bool = True,
        auth_role: str | None = None,
        auth_obj: str | None = None,
        auth_act: str | None = None,
        **kwargs,
    ):
        """注册路由并自动注入权限依赖。

        支持按需启用用户认证、角色校验、数据权限校验。

        Args:
            path (str): 路由路径。
            auth (bool): 是否启用认证（默认 True）。
            auth_role (Optional[str]): 指定角色校验（覆盖实例默认值）。
            auth_obj (Optional[str]): 指定数据对象（Casbin obj）。
            auth_act (Optional[str]): 指定操作行为（Casbin act）。
            **kwargs: 透传给父类 api_route。

        Returns:
            Callable: 路由装饰器。
        """
    def add_auth_data_rule(self, path: str, **kwargs):
        """将当前路由的权限规则加入 data_rules 列表，并更新全局 permission_rules。

        用于后续权限匹配和默认策略初始化。

        Args:
            path (str): 路由路径。
            **kwargs: 包含 methods 等路由元数据。
        """
    def get(
        self,
        path: str,
        *,
        auth: bool = True,
        auth_role: str | None = None,
        auth_obj: str | None = None,
        auth_act: str | None = None,
        **kwargs,
    ):
        """注册 GET 路由并自动注入权限依赖。

        Args:
            path (str): 路由路径。
            auth (bool): 是否启用认证。
            auth_role (Optional[str]): 角色校验。
            auth_obj (Optional[str]): 数据对象。
            auth_act (Optional[str]): 操作行为。
            **kwargs: 透传参数。

        Returns:
            Callable: 路由装饰器。
        """
    def post(
        self,
        path: str,
        *,
        auth: bool = True,
        auth_role: str | None = None,
        auth_obj: str | None = None,
        auth_act: str | None = None,
        **kwargs,
    ):
        """注册 POST 路由并自动注入权限依赖。

        Args:
            path (str): 路由路径。
            auth (bool): 是否启用认证。
            auth_role (Optional[str]): 角色校验。
            auth_obj (Optional[str]): 数据对象。
            auth_act (Optional[str]): 操作行为。
            **kwargs: 透传参数。

        Returns:
            Callable: 路由装饰器。
        """
    def put(
        self,
        path: str,
        *,
        auth: bool = True,
        auth_role: str | None = None,
        auth_obj: str | None = None,
        auth_act: str | None = None,
        **kwargs,
    ):
        """注册 PUT 路由并自动注入权限依赖。

        Args:
            path (str): 路由路径。
            auth (bool): 是否启用认证。
            auth_role (Optional[str]): 角色校验。
            auth_obj (Optional[str]): 数据对象。
            auth_act (Optional[str]): 操作行为。
            **kwargs: 透传参数。

        Returns:
            Callable: 路由装饰器。
        """
    def patch(
        self,
        path: str,
        *,
        auth: bool = True,
        auth_role: str | None = None,
        auth_obj: str | None = None,
        auth_act: str | None = None,
        **kwargs,
    ):
        """注册 PATCH 路由并自动注入权限依赖。

        Args:
            path (str): 路由路径。
            auth (bool): 是否启用认证。
            auth_role (Optional[str]): 角色校验。
            auth_obj (Optional[str]): 数据对象。
            auth_act (Optional[str]): 操作行为。
            **kwargs: 透传参数。

        Returns:
            Callable: 路由装饰器。
        """
    def delete(
        self,
        path: str,
        *,
        auth: bool = True,
        auth_role: str | None = None,
        auth_obj: str | None = None,
        auth_act: str | None = None,
        **kwargs,
    ):
        """注册 DELETE 路由并自动注入权限依赖。

        Args:
            path (str): 路由路径。
            auth (bool): 是否启用认证。
            auth_role (Optional[str]): 角色校验。
            auth_obj (Optional[str]): 数据对象。
            auth_act (Optional[str]): 操作行为。
            **kwargs: 透传参数。

        Returns:
            Callable: 路由装饰器。
        """

def get_data_rule_from_request(
    *, request: Request, data_rules: list[AuthDataRule]
) -> AuthDataRule | None:
    """根据当前请求匹配对应的权限规则。

    遍历已注册的 AuthDataRule 列表，查找方法和路径均匹配的规则。

    Args:
        request (Request): 当前 HTTP 请求。
        data_rules (list[AuthDataRule]): 已注册的权限规则列表。

    Returns:
        Optional[AuthDataRule]: 匹配的规则，若无匹配则返回 None。
    """
