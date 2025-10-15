#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：Shudaodao Auto Generator
# @Software ：PyCharm
# @Date     ：2025/10/09 16:09:29
# @Desc     ：SQLModel classes for shudaodao_enum.t_enum_schema


from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, Text, Boolean
from sqlmodel import SQLModel, Relationship

from .. import RegistryModel, get_table_schema
from ...schemas.response import BaseResponse
from ...sqlmodel_ext.field import Field
from ...utils.generate_unique_id import get_primary_id

if TYPE_CHECKING:
    from .t_enum_field import EnumField


class EnumSchema(RegistryModel, table=True):
    """ 数据库对象模型 """
    __tablename__ = "t_enum_schema"
    __table_args__ = {"schema": get_table_schema(), "comment": "数据库模式"}

    schema_id: int = Field(default_factory=get_primary_id, primary_key=True, sa_type=BigInteger, description="主键ID")
    schema_label: str = Field(max_length=100, description="模式别名")
    schema_name: str = Field(unique=True, max_length=100, description="数据库模式")

    is_active: bool = Field(default=True, sa_type=Boolean, description="启用状态")
    sort_order: int = Field(default=10, description="排序权重")
    create_by: Optional[str] = Field(default=None, max_length=50, nullable=True, description="创建人")
    create_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), nullable=True, description="创建日期")
    update_by: Optional[str] = Field(default=None, max_length=50, nullable=True, description="修改人")
    update_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), nullable=True, description="修改日期")
    tenant_id: Optional[int] = Field(default=None, nullable=True, sa_type=BigInteger, description="租户内码")
    # -- 外键 --> 子对象 --
    enum_fields: list["EnumField"] = Relationship(back_populates="schema")


class EnumSchemaBase(SQLModel):
    """ 创建、更新模型 共用字段 """
    schema_label: str = Field(max_length=100, description="模式别名")
    schema_name: str = Field(max_length=100, description="数据库模式")
    sort_order: Optional[int] = Field(default=10, description="排序权重")
    description: Optional[str] = Field(default=None, description="描述")


class EnumSchemaCreate(EnumSchemaBase):
    """ 前端创建模型 - 用于接口请求 """
    ...


class EnumSchemaUpdate(EnumSchemaBase):
    """ 前端更新模型 - 用于接口请求 """
    ...


class EnumSchemaResponse(BaseResponse):
    """ 前端响应模型 - 用于接口响应 """
    schema_id: int = Field(description="主键ID", sa_type=BigInteger)
    schema_label: str = Field(description="模式别名")
    schema_name: str = Field(description="数据库模式")
    sort_order: Optional[int] = Field(description="排序权重", default=None)
    description: Optional[str] = Field(description="描述", default=None)
    create_by: Optional[str] = Field(description="创建人", default=None)
    create_at: Optional[datetime] = Field(description="创建日期", default=None)
    update_by: Optional[str] = Field(description="修改人", default=None)
    update_at: Optional[datetime] = Field(description="修改日期", default=None)
