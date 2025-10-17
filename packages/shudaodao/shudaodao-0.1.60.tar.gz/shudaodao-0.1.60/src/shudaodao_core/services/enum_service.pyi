from ..logger.logging_ import logging as logging
from _typeshed import Incomplete
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSession

class EnumService:
    """枚举解析服务类。
    提供统一接口，用于将字典中的原始字段值（如字符串或整数）解析为对应的枚举实例，
    通常用于数据反序列化、API 输入校验或数据库记录映射等场景。
    """

    enums: Incomplete
    @classmethod
    def resolve_field(cls, schema, field, value) -> str:
        """将字典中指定字段的值解析为对应的 LabelEnum 枚举实例。"""
    @classmethod
    async def load(cls, db: AsyncSession, schema_class, field_class, value_class): ...
