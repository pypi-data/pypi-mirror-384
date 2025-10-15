from ..config.app_config import AppConfig as AppConfig
from ..logger.logging_ import logging as logging
from sqlalchemy.engine import Engine as Engine
from sqlalchemy.ext.asyncio import AsyncEngine as AsyncEngine

class DatabaseEngine:
    """多数据源数据库引擎管理器，支持同步与异步双模式，采用线程安全单例模式。

    功能：
        - 从 `AppConfig.storage.database` 加载多个数据库配置；
        - 为每个启用的数据源创建同步（`Engine`）和异步（`AsyncEngine`）引擎；
        - 提供统一访问接口：`get_engine(name)` / `get_async_engine(name)`；
        - 支持运行时判断数据源是否支持 schema（如排除 SQLite）；
        - 提供资源释放方法：`close()`（同步）与 `async_close()`（异步）。

    注意：
        - 本类为 **线程安全单例**，但 **非异步安全单例**（初始化为同步）；
        - 首次实例化时会加载所有启用的数据库配置；
        - `__new__` 方法支持便捷调用：`DatabaseEngine("auth", async_engine=True)` 直接返回引擎。

    典型用法：
        # 获取异步引擎
        auth_engine = DatabaseEngine("auth", async_engine=True)
        # 或先获取实例再调用方法
        db_mgr = DatabaseEngine()
        engine = db_mgr.get_async_engine("main")
    """
    def __new__(cls, name: str = None, async_engine: bool = True):
        """线程安全单例构造器，支持快捷返回指定引擎。

        Args:
            name (str, optional): 数据源名称。若提供，则直接返回对应引擎。
            async_engine (bool): 当 `name` 提供时，指定返回异步（True）或同步（False）引擎。

        Returns:
            DatabaseEngine | AsyncEngine | Engine:
                - 若 `name` 为 None：返回 `DatabaseEngine` 单例；
                - 若 `name` 非 None：返回对应的 `AsyncEngine` 或 `Engine` 实例。
        """
    def get_async_engine(self, name: str) -> AsyncEngine:
        """获取指定名称的异步数据库引擎。

        Args:
            name (str): 数据源名称（需在配置中启用）。

        Returns:
            AsyncEngine: SQLAlchemy 异步引擎实例。

        Raises:
            KeyError: 若指定名称的引擎未加载（如未启用或名称错误）。
        """
    def get_engine(self, name: str) -> Engine:
        """获取指定名称的同步数据库引擎。

        Args:
            name (str): 数据源名称（需在配置中启用）。

        Returns:
            Engine: SQLAlchemy 同步引擎实例。

        Raises:
            KeyError: 若指定名称的引擎未加载。
        """
    def support_schema(self, name: str) -> bool:
        """判断指定数据源是否支持 schema（如 SQLite 不支持）。

        Args:
            name (str): 数据源名称。

        Returns:
            bool: 支持 schema 返回 True，否则 False（如 SQLite）。
        """
    def close(self) -> None:
        """关闭所有同步数据库引擎连接池。

        调用每个 `Engine.dispose()` 释放底层连接资源。
        """
    async def async_close(self) -> None:
        """异步关闭所有异步数据库引擎连接池。

        使用 `asyncio.gather` 并发释放所有 `AsyncEngine` 资源。
        应在应用关闭阶段（如 FastAPI 的 lifespan 事件中）调用。
        """
    def __del__(self) -> None:
        """析构函数：尝试关闭同步引擎资源。

        注意：异步资源（`_async_pools`）**不能在此安全关闭**，
        因为 `__del__` 是同步上下文，且事件循环可能已结束。
        异步资源应通过显式调用 `await async_close()` 释放。
        """
