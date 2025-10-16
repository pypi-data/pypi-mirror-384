from ..config.app_config import AppConfig as AppConfig
from ..logger.logging_ import logging as logging
from ..utils.core_utils import CoreUtil as CoreUtil
from pathlib import Path

class DiskEngine:
    """本地磁盘存储路径管理器，基于配置动态创建并缓存存储目录。

    功能：
        - 从 `AppConfig.storage.disk` 加载多个磁盘存储配置；
        - 为每个启用的存储项创建并缓存其绝对路径（自动创建目录）；
        - 提供便捷方法 `get_path(name, child_path)` 获取子路径（自动创建）；
        - 采用线程安全单例模式，确保全局唯一实例。

    典型用途：
        - 文件上传/下载根目录管理；
        - 日志、缓存、临时文件分区存储；
        - 多租户本地存储隔离（如 `tenant_a/files`, `tenant_b/files`）。

    注意：
        - 所有路径均基于项目根目录（`CoreUtil.get_root_path()`）；
        - 子路径（`child_path`）支持多级（如 `"user/123/avatar"`）；
        - 目录创建使用 `mkdir(parents=True, exist_ok=True)`，安全幂等。
    """
    def __new__(cls):
        """线程安全的单例构造器。

        首次调用时加载所有启用的磁盘存储配置并创建目录。
        """
    def get_path(self, name: str, child_path: str = "") -> Path:
        """获取指定存储项的完整路径，支持自动创建子目录。

        Args:
            name (str): 存储配置名称（需在配置中启用）。
            child_path (str, optional): 相对于根存储目录的子路径（如 "uploads/2025/10"）。

        Returns:
            Path: 绝对路径对象，对应目录已确保存在。

        Raises:
            KeyError: 若 `name` 未在配置中启用或不存在。
            ValueError: 若 `child_path` 包含非法字符（由 `pathlib` 自动处理）。
        """
    def close(self) -> None:
        """预留资源清理接口（当前无实际操作）。

        可用于未来扩展（如释放文件锁、关闭监控句柄等）。
        """
    def __del__(self) -> None:
        """析构函数：清理内部状态。

        注意：Path 对象本身无需显式关闭，此处仅重置引用。
        """
