from .meta_column import MetaColumn as MetaColumn
from .meta_table import MetaTable as MetaTable
from dataclasses import dataclass

@dataclass
class MetaView(MetaTable):
    def __init__(self, *args, **kwargs) -> None: ...
    def get_columns(self) -> list[MetaColumn]:
        """从数据库视图获取字段信息"""
    def get_import_shudaodao_core(self) -> str: ...
    def get_import_sqlmodel(self): ...
