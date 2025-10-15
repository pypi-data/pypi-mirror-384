from ..enum.label_enum import LabelEnum as LabelEnum
from ..enum.resolve_enum import resolve_enum_field as resolve_enum_field

class EnumService:
    """枚举解析服务类。
    提供统一接口，用于将字典中的原始字段值（如字符串或整数）解析为对应的枚举实例，
    通常用于数据反序列化、API 输入校验或数据库记录映射等场景。
    """
    @classmethod
    def resolve_field(
        cls, data: dict, field_name: str, enum_cls: type[LabelEnum]
    ) -> None:
        """将字典中指定字段的值解析为对应的 LabelEnum 枚举实例。"""
