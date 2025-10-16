from dataclasses import dataclass

@dataclass
class MetaForeignColumn:
    schema_name: str
    alias_index: str
    constrained_table: str
    constrained_class: str
    constrained_column: str
    constrained_name: str
    referred_table: str
    referred_class: str
    referred_column: str
    referred_name: str
    @staticmethod
    def get_plural_name(source) -> str: ...
    @classmethod
    def get_property_name(cls, source: str) -> str: ...
