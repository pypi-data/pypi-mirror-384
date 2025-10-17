from ..config.app_config import AppConfig as AppConfig
from ..logger.logging_ import logging as logging
from ..portal_auth.entity_table.auth_rule import AuthRule as AuthRule
from ..services.db_engine_service import DBEngineService as DBEngineService
from ..utils.core_utils import CoreUtil as CoreUtil
from casbin import AsyncEnforcer

class PermissionEngine:
    """Casbin 异步权限引擎的线程安全单例管理器。

    负责：
        - 初始化 Casbin 的 AsyncEnforcer；
        - 绑定 SQLAlchemy 异步适配器（持久化策略到 `AuthRule` 表）；
        - 支持自动保存策略、自动构建角色继承关系；
        - 提供表结构检查与重建能力（用于开发/测试环境）。

    注意：
        - 本类使用 **双重检查锁（DCL）** 实现线程安全的单例模式；
        - `_load()` 在首次实例化时同步执行，因此应避免在异步上下文中首次触发；

    典型用法：
        enforcer = PermissionEngine().get_async_enforcer()
        allowed = await enforcer.enforce("admin", "user", "read")
    """
    def __new__(cls):
        """线程安全的单例构造器。

        使用双重检查锁确保多线程环境下仅创建一个实例。
        注意：`_load()` 是同步方法，首次调用会阻塞当前线程。
        """
    def get_async_enforcer(self) -> AsyncEnforcer:
        """获取已初始化的异步 Casbin Enforcer 实例。

        Returns:
            AsyncEnforcer: 可用于 `await enforcer.enforce(...)` 的权限校验器。
        """
    async def check_table(self) -> None:
        """检查并按需重建权限策略表。

        若配置 `AppConfig.auth.rebuild_auth_rule` 为 True：
            - 表不存在：创建表；
            - 表存在：清空现有策略（调用 `clear_policy()` 并保存空策略）。

        适用于开发/测试环境重置权限规则。
        """
