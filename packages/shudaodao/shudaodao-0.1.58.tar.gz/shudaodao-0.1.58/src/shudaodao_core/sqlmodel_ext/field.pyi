from sqlmodel import Field as SQLModelField
from typing import Any

def Field(*args: Any, **kwargs: Any) -> SQLModelField:
    """
    SQLModel 字段工厂函数，支持将 `description` 自动映射为数据库列注释（comment）。
    此函数是对 `sqlmodel.Field` 的封装，使得开发者可使用 `description="用户ID"` 语法，
    自动转换为 SQLAlchemy 的 `comment`，从而在数据库中生成列注释。
    """
