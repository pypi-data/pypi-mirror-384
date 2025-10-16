from dataclasses import dataclass
from typing import Pattern

@dataclass
class AuthDataRule:
    """表示一条数据权限控制规则。

    用于在接口层面绑定 Casbin 的数据权限策略（p 规则），
    包含 HTTP 方法、路径匹配模式及对应的数据权限三元组（obj, act, role）。

    Attributes:
        method (str): HTTP 方法，如 'GET', 'POST' 等。
        pattern (Pattern): 编译后的正则表达式，用于匹配请求路径。
        data_role (str): Casbin 中的角色标识（如 'admin', 'user'）。
        data_act (str): 操作行为（如 'read', 'write'）。
        data_obj (str): 数据对象类型（如 'order', 'user_profile'）。
    """

    method: str
    pattern: Pattern
    data_role: str
    data_act: str
    data_obj: str
    @staticmethod
    def convert_path_to_regex(path: str) -> Pattern:
        """将 FastAPI 路径模板转换为用于精确结尾匹配的正则表达式。

        支持 FastAPI 风格的路径参数，例如：
        - 输入: "/users/{user_id:int}" → 转换为正则: r\'/users/(?P<user_id>[^/]+)$\'
        - 输入: "/orders/{order_id}" → 转换为正则: r\'/orders/(?P<order_id>[^/]+)$\'

        转换规则：
        1. 移除类型注解（如 :int, :path），仅保留参数名。
        2. 将 {param} 替换为命名捕获组 (?P<param>[^/]+)。
        3. 在末尾添加 $ 确保完整路径匹配，防止前缀误匹配。

        Args:
            path (str): FastAPI 路由路径模板，如 "/api/v1/users/{uid}"。

        Returns:
            Pattern: 编译后的正则表达式对象，用于路径匹配。
        """
