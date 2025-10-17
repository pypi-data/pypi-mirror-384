#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/10/9 下午4:37
# @Desc     ：


from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, Text, Boolean
from sqlmodel import Relationship, SQLModel

from .. import get_table_schema, RegistryModel
from ...schemas.response import BaseResponse
from ...sqlmodel_ext.field import Field
from ...utils.generate_unique_id import get_primary_id

if TYPE_CHECKING:
    from .policy_action import PolicyAction


class PolicyObject(RegistryModel, table=True):
    """ 数据模型 - 数据库表 t_policy_object 结构模型 """
    __tablename__ = "t_policy_object"
    __table_args__ = {"schema": get_table_schema(), "comment": "策略对象表"}

    policy_object_id: Optional[int] = Field(
        default_factory=get_primary_id, primary_key=True, sa_type=BigInteger, description="策略对象内码")
    # 表: schema+table
    object_name: str = Field(unique=True, index=True, description="对象名称")
    is_active: bool = Field(default=True, sa_type=Boolean, description="启用状态")
    sort_order: int = Field(default=10, description="排序权重")
    description: Optional[str] = Field(default=None, nullable=True, sa_type=Text, description="描述")
    # -- 外键 --> 子对象 --
    policy_actions: list["PolicyAction"] = Relationship(back_populates="policy_object")


class PolicyObjectBase(SQLModel):
    """ 创建、更新模型 共用字段 """
    object_name: str
    sort_order: Optional[int] = Field(default=10, description="排序权重")
    description: Optional[str] = Field(default=None, description="描述")


class PolicyObjectCreate(PolicyObjectBase):
    """ 前端创建模型 - 用于接口请求 """
    ...


class PolicyObjectUpdate(PolicyObjectBase):
    """ 前端更新模型 - 用于接口请求 """
    ...


class PolicyObjectResponse(BaseResponse):
    """ 前端响应模型 - 用于接口响应 """
    policy_object_id: int = Field(sa_type=BigInteger, description="策略对象内码")
    object_name: str = Field(description="对象名称")
    sort_order: Optional[int] = Field(description="排序权重", default=None)
    description: Optional[str] = Field(description="描述", default=None)
