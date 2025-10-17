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

from .. import get_table_schema, RegistryModel, get_foreign_schema
from ...sqlmodel_ext.field import Field
from ...schemas.response import BaseResponse
from ...utils.generate_unique_id import get_primary_id

if TYPE_CHECKING:
    from .policy_object import PolicyObject


class PolicyAction(RegistryModel, table=True):
    """ 数据模型 - 数据库表 t_policy_action 结构模型 """
    __tablename__ = "t_policy_action"
    __table_args__ = {"schema": get_table_schema(), "comment": "策略动作表"}

    action_id: Optional[int] = Field(
        default_factory=get_primary_id, primary_key=True, sa_type=BigInteger, description="内码")
    policy_object_id: Optional[int] = Field(
        sa_type=BigInteger, description="策略对象内码",
        foreign_key=f"{get_foreign_schema()}t_policy_object.policy_object_id"
    )
    # 动作:增删改查
    action_name: str = Field(unique=True, index=True, description="动作名称")
    # 通用字段
    is_active: bool = Field(default=True, sa_type=Boolean, description="启用状态")
    sort_order: int = Field(default=10, description="排序权重")
    description: Optional[str] = Field(default=None, nullable=True, sa_type=Text, description="描述")
    # -- 外键 --> 父对象 --
    policy_object: "PolicyObject" = Relationship(back_populates="policy_actions")


class PolicyActionBase(SQLModel):
    """ 创建、更新模型 共用字段 """
    object_id: int = Field(sa_type=BigInteger)
    action_name: str
    sort_order: Optional[int] = Field(default=10, description="排序权重")
    description: Optional[str] = Field(default=None, description="描述")


class PolicyActionCreate(PolicyActionBase):
    """ 前端创建模型 - 用于接口请求 """
    ...


class PolicyActionUpdate(PolicyActionBase):
    """ 前端更新模型 - 用于接口请求 """
    ...


class PolicyActionResponse(BaseResponse):
    """ 前端响应模型 - 用于接口响应 """
    action_id: int = Field(sa_type=BigInteger)
    action_name: str
    object_id: Optional[int] = Field(sa_type=BigInteger)
    sort_order: Optional[int] = Field(description="排序权重", default=None)
    description: Optional[str] = Field(description="描述", default=None)
