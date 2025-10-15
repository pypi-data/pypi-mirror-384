from ..auth.auth_router import AuthRouter as AuthRouter
from ..config.app_config import AppConfig as AppConfig
from ..config.schemas.routers import RouterConfigSetting as RouterConfigSetting
from ..engine.casbin_engine import PermissionEngine as PermissionEngine
from ..engine.database_engine import DatabaseEngine as DatabaseEngine
from ..engine.disk_engine import DiskEngine as DiskEngine
from ..engine.redis_engine import RedisEngine as RedisEngine
from ..exception.register_handlers import (
    register_exception_handlers as register_exception_handlers,
)
from ..license.verify import verify_license as verify_license
from ..logger.logging_ import logging as logging
from ..services.auth_service import AuthService as AuthService
from ..services.casbin_service import PermissionService as PermissionService
from ..services.data_service import DataService as DataService
from ..services.db_engine_service import DBEngineService as DBEngineService
from ..tools.class_scaner import ClassScanner as ClassScanner
from ..tools.database_checker import DatabaseChecker as DatabaseChecker
from ..tools.tenant_checker import TenantManager as TenantManager
from ..utils.core_utils import CoreUtil as CoreUtil
from _typeshed import Incomplete
from abc import ABC
from typing import Callable

class Application(ABC):
    """应用核心类，负责初始化和管理FastAPI应用。

    该类封装了FastAPI应用的完整生命周期，包括环境初始化、许可验证、数据库检查、
    路由加载、中间件配置、异常处理以及服务启动/关闭等流程。
    子类必须实现抽象方法以完成自定义初始化逻辑。
    """

    fastapi: Incomplete
    def __init__(self) -> None:
        """初始化应用核心组件。

        执行顺序：
        1. 打印启动横幅
        2. 初始化环境信息日志
        3. 验证软件许可
        4. 初始化底层引擎（数据库、Redis等）
        5. 创建FastAPI实例
        6. 调用子类实现的 application_init() 配置中间件
        7. 加载路由
        8. 注册全局异常处理器
        """
    @classmethod
    def verify_license(cls) -> None: ...
    def run(self) -> None: ...
    def startup(self, func: Callable):
        """装饰器或直接注册启动回调"""
    def shutdown(self, func: Callable):
        """装饰器或直接注册关闭回调"""
