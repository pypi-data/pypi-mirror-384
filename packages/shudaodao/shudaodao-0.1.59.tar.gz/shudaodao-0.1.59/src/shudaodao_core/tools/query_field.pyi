def get_class_fields_with_sa_type(model_class, sa_type): ...
def convert_datetime_iso_to_standard(dt_str):
    """
    将 ISO 8601 格式（含T）的时间字符串转换为 'YYYY-MM-DD HH:MM:SS' 格式
    支持：2025-09-22T10:30:00, 2025-09-22T10:30:00Z, 2025-09-22T10:30:00+08:00 等
    """
