from ..logger.logging_ import logging as logging
from typing import Any, Callable

class ClassScanner:
    """
    通用类扫描器：递归扫描包，找出满足条件的类
    """
    @classmethod
    def find_classes(
        cls,
        package_name: str,
        base_class: type = ...,
        predicate: Callable[[type], bool] | None = None,
    ) -> dict[str, type]:
        """
        扫描指定包，找出所有继承自 base_class 且满足 predicate 条件的类
        :param package_name: 要扫描的包名（如 "myapp.models"）
        :param base_class: 基类（默认 object，即所有类）
        :param predicate: 额外筛选条件（函数，接收类对象，返回 bool）
        :return: {完整类名: 类对象} 的字典
        """
    @classmethod
    def find_classes_instances(
        cls,
        package_name: str,
        base_class: type = ...,
        predicate: Callable[[Any], bool] | None = None,
    ) -> dict[str, Any]:
        """
        扫描包中所有模块，找出所有类型的实例对象
        可选 predicate 用于进一步筛选实例（如根据 .prefix 属性）
        返回: {变量名（完整路径）: 实例对象}
        """
