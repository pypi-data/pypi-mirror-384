import redis
from ..config.app_config import AppConfig as AppConfig
from ..logger.logging_ import logging as logging

class RedisEngine:
    """Redis 多实例连接池管理器，基于配置动态创建连接池，采用线程安全单例模式。

    功能：
        - 从 `AppConfig.storage.redis` 加载多个 Redis 配置；
        - 为每个启用的 Redis 实例创建独立的 `redis.ConnectionPool`；
        - 提供 `get_connection(name)` 获取线程安全的 `redis.Redis` 客户端；
        - 支持统一资源释放（`close()` / 析构函数）。

    设计说明：
        - 每个 `redis.Redis` 实例是轻量级的，底层共享连接池，可安全用于多线程；
        - 连接池参数（如 `max_connections`, `password`, `ssl` 等）通过 `config.kwargs` 传入；
        - 自动跳过 `enabled: false` 的配置项。

    典型用法：
        redis_client = RedisEngine().get_connection("cache")
        value = redis_client.get("user:123")
    """
    def __new__(cls):
        """线程安全的单例构造器。

        首次调用时加载所有启用的 Redis 配置并初始化连接池。
        """
    def get_connection(self, pool_name: str) -> redis.Redis:
        """获取指定 Redis 实例的客户端连接。

        每次调用返回一个新的 `redis.Redis` 实例，但底层共享同一个连接池，
        因此是线程安全且高效的。

        Args:
            pool_name (str): Redis 配置名称（需在配置中启用）。

        Returns:
            redis.Redis: 可直接使用的 Redis 客户端。

        Raises:
            KeyError: 若 `pool_name` 未配置或未启用。
            redis.ConnectionError: 首次实际操作时可能抛出（连接池懒连接）。
        """
    def close(self) -> None:
        """关闭所有 Redis 连接池中的连接。

        调用每个 `ConnectionPool.disconnect()` 主动断开所有底层连接。
        适用于应用优雅关闭场景。
        """
    def __del__(self) -> None:
        """析构函数：尝试释放所有 Redis 连接资源。

        注意：依赖 `__del__` 不可靠（Python 垃圾回收时机不确定），
        建议在应用生命周期结束时显式调用 `close()`。
        """
