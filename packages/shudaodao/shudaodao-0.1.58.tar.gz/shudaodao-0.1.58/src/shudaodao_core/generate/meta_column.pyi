from .meta_foreign import MetaForeignColumn as MetaForeignColumn
from dataclasses import dataclass
from typing import Any

@dataclass
class MetaColumn:
    """列 元数据"""

    name: str
    type: Any
    sa_type: str | None
    nullable: bool
    default: str | None
    is_primary: bool
    comment: str = ...
    max_length: int | None = ...
    precision: int | None = ...
    scale: int | None = ...
    foreign_key: MetaForeignColumn | None = ...
