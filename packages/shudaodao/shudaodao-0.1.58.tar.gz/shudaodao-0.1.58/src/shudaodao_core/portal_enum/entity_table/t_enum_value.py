#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：Shudaodao Auto Generator
# @Software ：PyCharm
# @Date     ：2025/10/09 16:09:29
# @Desc     ：SQLModel classes for shudaodao_enum.t_enum_value


from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, Text, Boolean
from sqlmodel import SQLModel, Relationship

from .. import RegistryModel, get_table_schema, get_foreign_schema
from ...sqlmodel_ext.field import Field
from ...schemas.response import BaseResponse
from ...utils.generate_unique_id import get_primary_id

if TYPE_CHECKING:
    from .t_enum_field import EnumField


class EnumValue(RegistryModel, table=True):
    """ 数据库对象模型 """
    __tablename__ = "t_enum_value"
    __table_args__ = {"schema": get_table_schema(), "comment": "枚举值表"}

    enum_id: int = Field(default_factory=get_primary_id, primary_key=True, sa_type=BigInteger, description="枚举内码")
    field_id: int = Field(
        sa_type=BigInteger, description="字段内码", foreign_key=f"{get_foreign_schema()}t_enum_field.field_id")
    enum_pid: int = Field(default=-1, sa_type=BigInteger, description="上级枚举")
    enum_label: str = Field(max_length=100, description="枚举名")
    enum_name: str = Field(max_length=100, description="枚举值")
    enum_value: int = Field(description="枚举中文")
    is_active: bool = Field(default=True, sa_type=Boolean, description="启用状态")
    sort_order: int = Field(default=10, description="排序权重")
    description: Optional[str] = Field(default=None, nullable=True, max_length=500, description="描述")
    create_by: Optional[str] = Field(default=None, max_length=50, nullable=True, description="创建人")
    create_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), nullable=True, description="创建日期")
    update_by: Optional[str] = Field(default=None, max_length=50, nullable=True, description="修改人")
    update_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), nullable=True, description="修改日期")
    # -- 外键 --> 父对象 --
    field: "EnumField" = Relationship(back_populates="enum_values")


class EnumValueBase(SQLModel):
    """ 创建、更新模型 共用字段 """
    field_id: int = Field(sa_type=BigInteger, description="字段内码")
    enum_pid: int = Field(default=-1, sa_type=BigInteger, description="上级枚举")
    enum_label: str = Field(max_length=100, description="枚举名")
    enum_name: str = Field(max_length=100, description="枚举值")
    enum_value: int = Field(description="枚举中文")
    sort_order: Optional[int] = Field(default=10, description="字段索引")
    is_active: Optional[bool] = Field(default=None, description="是否启用")
    description: Optional[str] = Field(default=None, description="描述")


class EnumValueCreate(EnumValueBase):
    """ 前端创建模型 - 用于接口请求 """
    ...


class EnumValueUpdate(EnumValueBase):
    """ 前端更新模型 - 用于接口请求 """
    ...


class EnumValueResponse(BaseResponse):
    """ 前端响应模型 - 用于接口响应 """
    enum_id: int = Field(description="枚举内码", sa_type=BigInteger)
    field_id: int = Field(description="字段内码", sa_type=BigInteger)
    enum_pid: int = Field(description="上级枚举", sa_type=BigInteger)
    enum_label: str = Field(description="枚举名")
    enum_name: str = Field(description="枚举值")
    enum_value: int = Field(description="枚举中文")
    sort_order: Optional[int] = Field(description="字段索引", default=None)
    is_active: Optional[bool] = Field(description="是否启用", default=None)
    description: Optional[str] = Field(description="描述", default=None)
    create_by: Optional[str] = Field(description="创建人", default=None)
    create_at: Optional[datetime] = Field(description="创建日期", default=None)
    update_by: Optional[str] = Field(description="修改人", default=None)
    update_at: Optional[datetime] = Field(description="修改日期", default=None)
