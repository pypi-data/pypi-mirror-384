from .label_enum import LabelEnum as LabelEnum

def resolve_enum_field(data: dict, field_name: str, enum_cls: type[LabelEnum]) -> None:
    """
    从 data 中解析 field_name 和 field_name + \'_label\'，统一为整数值写回 data[field_name]。

    示例：
        resolve_enum_field(data, "status", UserStatus)
        # 会读取 data["status"], data["status_label"]
        # 写回 data["status"] = int | None
        # 删除 data["status_label"]

    :param data: 输入字典（会被原地修改）
    :param field_name: 字段名，如 "status"
    :param enum_cls: 枚举类，必须是 IntEnum 子类，且实现 .label 和 .from_label()
    :raises ValueError: 输入无效或不一致
    """
