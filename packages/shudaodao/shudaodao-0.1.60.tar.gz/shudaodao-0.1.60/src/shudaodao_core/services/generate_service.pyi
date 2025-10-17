from ..generate.config import GeneratorConfig as GeneratorConfig
from ..generate.template_builder import TemplateBuilder as TemplateBuilder
from ..logger.logging_ import logging as logging
from .data_service import DataService as DataService
from .db_engine_service import DBEngineService as DBEngineService
from _typeshed import Incomplete

class GeneratorService:
    """代码生成服务类。

    基于数据库元数据（表和视图），结合模板配置，自动生成实体类（SQLModel）与控制器代码。
    支持按 schema 或整个数据库范围进行批量生成。
    """

    config: Incomplete
    builder: Incomplete
    enums: dict[str, list] | None
    def __init__(self, config: GeneratorConfig) -> None:
        """初始化代码生成服务。
        Args:
            config (GeneratorConfig): 代码生成的配置对象，包含输出路径、模板目录、数据库连接等信息。
        """
    def get_enums(self, schema_name: str) -> list: ...
    def generator_all(self) -> None:
        """生成所有 schema 下的表和视图对应的代码。

        若配置中存在多个 schema，则遍历每个 schema 并调用 `generator_schema`；
        否则直接生成默认 schema（或无 schema）下的所有对象。
        """
    def generator_schema(
        self, schema_name: str | None = None, enum_fields=None
    ) -> None:
        """生成指定 schema（或默认数据库）下所有表和视图的代码。

        Args:
            schema_name (str | None): 目标 schema 名称。若为 None，则处理默认数据库上下文。
            enum_fields:
        """
    def generator_table(
        self, table_name: str, schema_name: str | None, enum_fields=None
    ) -> None:
        """为单个数据库表生成实体类与控制器代码。

        Args:
            table_name (str): 表名称。
            schema_name (str | None): 所属 schema 名称，可能为 None（表示默认 schema）。
            enum_fields:
        """
    def generator_view(
        self, view_name: str, schema_name: str | None, enum_fields=None
    ) -> None:
        """为单个数据库视图生成实体类与控制器代码。

        Args:
            view_name (str): 视图名称。
            schema_name (str | None): 所属 schema 名称，可能为 None（表示默认 schema）。
            enum_fields:
        """
