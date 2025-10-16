from ..config.app_config import AppConfig as AppConfig
from ..engine.casbin_engine import PermissionEngine as PermissionEngine
from ..exception.service_exception import PermissionException as PermissionException
from ..logger.logging_ import logging as logging
from _typeshed import Incomplete

class PermissionService:
    """权限服务类，用于管理基于 Casbin 的 RBAC（基于角色的访问控制）权限体系。

    该类负责初始化权限规则、分配角色与权限、验证用户权限等功能，
    支持角色继承、用户-角色绑定，并与数据库持久化策略集成。
    """

    engine: Incomplete
    def __init__(self) -> None:
        """初始化 PermissionService 实例。

        创建 Casbin 引擎实例并获取异步 enforcer 对象。
        """
    async def initialize(self, permission_rules) -> None:
        """异步初始化权限策略。

        根据 AppConfig 配置决定是否重建权限规则。
        若不重建，则从存储加载现有策略；否则根据传入的 permission_rules
        动态构建角色权限、角色继承关系及用户-角色绑定，并持久化到数据库。

        Args:
            permission_rules (dict): 权限规则字典，格式为：
                {
                    "role_name": {
                        "object": ["action1", "action2", ...],
                        ...
                    },
                    ...
                }

        Raises:
            Exception: 若 Casbin 表检查或策略操作失败，可能抛出底层异常。
        """
    async def has_role(self, user, role):
        """检查用户是否拥有指定角色（包括隐式继承的角色）。

        Args:
            user (str): 用户标识。
            role (str): 角色名称。

        Returns:
            bool: 若用户拥有该角色（直接或间接），返回 True。

        Raises:
            PermissionException: 若用户不具有该角色，抛出权限异常。
        """
    def has_permission(self, user, obj, act):
        """同步检查用户是否对指定对象拥有指定操作权限。

        基于 Casbin enforce 机制，自动解析用户角色及继承关系。

        Args:
            user (str): 用户标识。
            obj (str): 资源对象（如 API 路径、数据表名等）。
            act (str): 操作类型（如 "read", "write", "delete" 等）。

        Returns:
            bool: 若有权限，返回 True。

        Raises:
            PermissionException: 若无权限，抛出权限异常。
        """
    async def add_permission(self, *, role, obj, act) -> None:
        """异步为角色添加对象-操作权限。

        Args:
            role (str): 角色名称。
            obj (str): 资源对象。
            act (str): 操作类型。
        """
    async def add_role_for_user(self, *, user, role) -> None:
        """异步将角色分配给用户。

        Args:
            user (str): 用户标识。
            role (str): 角色名称。
        """
    async def add_role_for_role(self, *, parent_role, child_role) -> None:
        """异步建立角色继承关系（父角色继承子角色权限）。

        Args:
            parent_role (str): 父角色（如 admin）。
            child_role (str): 子角色（如 editor）。
        """
    async def save_policy(self) -> None:
        """异步将当前内存中的策略持久化到数据库。"""
