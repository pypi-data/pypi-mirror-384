#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/8/29 下午5:15
# @Desc     ：


from typing import List, Union, Literal, Optional

from pydantic import BaseModel, field_validator, Field

# 定义前向引用类型
Condition = Union['QueryLogicOperation', 'QuerySimpleCondition']


class QuerySimpleCondition(BaseModel):
    """ 查询条件 """
    field: str = Field(..., description="要查询的字段名")
    op: str = Field(..., description="逻辑运算符")
    val: Union[str, int, float, bool, List, None] = Field(..., description="要查询的值")

    class Config:
        extra = "forbid"


class QueryLogicOperation(BaseModel):
    """ 逻辑操作（AND 或 OR）"""
    type: str = Field(..., description="逻辑操作符，'AND' 或 'OR'")
    conditions: List[Condition] = Field(None, description="子条件列表")

    @classmethod
    @field_validator("type")
    def validate_type(cls, v: str) -> str:
        if v.upper() not in ("AND", "OR"):
            raise ValueError("QueryRequest的type必须是'AND'或'OR'")
        return v

    class Config:
        extra = "forbid"


# 解决前向引用
QueryLogicOperation.model_rebuild()
QuerySimpleCondition.model_rebuild()


# 排序条件模型
class QuerySortCondition(BaseModel):
    """ 排序条件 """
    field: str = Field(..., description="排序字段")
    order: Literal["asc", "desc"] = Field("asc", description="排序方向")


class TreeConfig(BaseModel):
    field_id: Optional[str] = Field(None, description="当前节点的ID，用于PID型树")
    field_pid: Optional[str] = Field(None, description="当前节点的PID，用于PID型树")
    field_tag: Optional[str] = Field(None, description="当前的标签")

    # 子节点，外键约束
    field_children: Optional[str] = Field(None, description="用于 外键约束 的Tree")

    children_fields: Optional[List[str]] = Field(None, description="子节点字段")
    children_orderby: Optional[str] = Field(None, description="子节点排序")
    # 子节点 PID 处理
    children_tag: Optional[str] = Field(None, description="子节点标签")
    children_id: Optional[str] = Field(None, description="子节点的ID，用于PID型树")
    children_pid: Optional[str] = Field(None, description="子节点的PID，用于PID型树")


class QueryRequest(QueryLogicOperation):
    """ 顶层查询模型 """
    fields: Optional[List[str]] = Field(None, description="指定要返回的字段")
    type: Optional[str] = Field("AND", description="逻辑操作类型，'AND' 或 'OR'")
    conditions: List[Condition] = Field(None, description="子条件列表")
    orderby: List[QuerySortCondition] = Field(None, description="排序条件列表")
    page: Optional[int] = Field(None, ge=1, description="第几页")
    size: Optional[int] = Field(None, ge=1, le=1000, description="每页多少个")
    # paging: Optional[bool] = Field(True, description="返回分页")
    format: Optional[Literal["list", "page", "tree"]] = Field(None, description="返回格式")
    tree: Optional[TreeConfig] = Field(None, description="树型格式的配置项")
