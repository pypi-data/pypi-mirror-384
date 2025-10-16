from ..engine.database_engine import DatabaseEngine as DatabaseEngine
from ..logger.logging_ import logging as logging
from ..utils.core_utils import CoreUtil as CoreUtil
from .config import GeneratorConfig as GeneratorConfig
from .meta_column import MetaColumn as MetaColumn
from .meta_foreign import MetaForeignColumn as MetaForeignColumn
from .meta_table import MetaTable as MetaTable
from .meta_view import MetaView as MetaView
from _typeshed import Incomplete
from pathlib import Path

class TemplateBuilder:
    """模版工具"""

    default_factory: bool
    support_schema: Incomplete
    output: Path
    def __init__(self, *, config: GeneratorConfig) -> None: ...
    @staticmethod
    def format_column_child(column: MetaForeignColumn) -> str: ...
    @staticmethod
    def format_column_parent(column: MetaForeignColumn) -> str: ...
    @classmethod
    def format_column_base(cls, column: MetaColumn) -> str:
        """格式化列定义"""
    @classmethod
    def format_column_table(cls, column: MetaColumn) -> str: ...
    @classmethod
    def format_column_response(cls, column: MetaColumn) -> str:
        """格式化 response 类 列定义"""
    @classmethod
    def format_column(cls, column: MetaColumn) -> str:
        """格式化列定义"""
    def render_template(
        self, *, meta_model: MetaTable, template_name: str, child_path: str
    ):
        """生成单个表的代码"""
    def save_init_file(self, meta_model: MetaTable): ...
    def get_table_meta(
        self, table_name, schema_name, default_schema_name
    ) -> MetaTable: ...
    def get_view_meta(
        self, view_name, schema_name, default_schema_name
    ) -> MetaView: ...
    def get_table_names(self, *, schema_name): ...
    def get_view_names(self, *, schema_name): ...
    def get_schema_names(self): ...
