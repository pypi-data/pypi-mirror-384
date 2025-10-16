from ..config.app_config import AppConfig as AppConfig
from _typeshed import Incomplete

class UserInfo:
    """封装当前请求上下文中的用户与租户信息。

    用于在多租户系统中传递用户身份和所属租户。
    当租户功能被禁用时，tenant_id 将被强制置为 None。
    """

    username: Incomplete
    tenant_id: Incomplete
    tenant_enabled: Incomplete
    def __init__(
        self,
        username: str | None = None,
        tenant_id: int | None = None,
        tenant_enabled: bool | None = None,
    ) -> None:
        """初始化用户上下文信息。

        Args:
            username (Optional[str]): 当前用户名。默认为 None。
            tenant_id (Optional[int]): 当前租户ID。若租户功能关闭，则会被忽略并设为 None。
            tenant_enabled (Optional[bool]): 是否启用租户隔离。
                若未提供，则从 AppConfig.auth.tenant.enabled 自动读取。
        """

def get_current_user_info() -> UserInfo:
    """获取当前请求上下文中的用户信息。

    该函数应在认证中间件设置上下文后调用。
    若尚未设置（如未登录或中间件未执行），则抛出 401 未授权异常。

    Returns:
        UserInfo: 当前用户的上下文信息对象。

    Raises:
        HTTPException: 状态码 401，提示“多租户模式，未设置用户或租户信息”。
    """

def set_current_user_info(user_info: UserInfo):
    """将用户信息绑定到当前请求上下文中。

    通常由认证中间件（如 JWT 验证后）调用，用于后续业务逻辑访问用户身份。

    Args:
        user_info (UserInfo): 要绑定的用户上下文对象。
    """
