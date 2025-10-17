from ..engine.database_engine import DatabaseEngine as DatabaseEngine
from _typeshed import Incomplete
from collections.abc import Generator
from sqlalchemy import Engine as Engine
from sqlalchemy.ext.asyncio import AsyncEngine as AsyncEngine

class DBEngineService:
    """数据库引擎与会话管理服务类。

    提供统一接口用于获取同步/异步数据库引擎及会话，
    支持多数据库配置（如 Auth、Common 等），便于在不同模块中复用。
    """
    @classmethod
    def get_async_engine(cls, database_config_name: str) -> AsyncEngine:
        """获取指定配置名称的异步数据库引擎实例。

        Args:
            database_config_name (str): 数据库配置名称（对应配置文件中的 database.name）。

        Returns:
            AsyncEngine :: 异步模式的数据库引擎封装对象。
        """
    @classmethod
    def get_engine(cls, database_config_name: str) -> Engine:
        """获取指定配置名称的同步数据库引擎实例。

        Args:
            database_config_name (str): 数据库配置名称（对应配置文件中的 database.name）。

        Returns:
            DatabaseEngine: 同步模式的数据库引擎封装对象。
        """
    @classmethod
    async def get_async_session(cls, database_config_name: str):
        """异步上下文管理器：获取指定数据库的异步会话。

        使用 `async with` 调用，自动管理会话生命周期（begin/commit/rollback/close）。

        Args:
            database_config_name (str): 数据库配置名称。

        Yields:
            AsyncSession: SQLAlchemy 异步数据库会话对象。
        """
    @classmethod
    def get_auth_async_engine(cls) -> AsyncEngine:
        """获取名为 'Auth' 的认证数据库的异步引擎。

        适用于用户、权限、租户等认证相关数据操作。

        Returns:
            AsyncEngine:: Auth 数据库的异步引擎实例。
        """
    @classmethod
    def get_auth_engine(cls):
        """获取名为 'Auth' 的认证数据库的同步引擎。

        Returns:
            DatabaseEngine: Auth 数据库的同步引擎实例。
        """
    @classmethod
    async def get_auth_async_session(cls) -> Generator[Incomplete]:
        """异步上下文管理器：获取 'Auth' 数据库的异步会话。

        配置需在 .yaml 文件中定义：
            storage:
              database:
                - name: Auth
                  ...

        Yields:
            AsyncSession: Auth 数据库的异步会话对象。
        """
