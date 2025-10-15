#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技

from sqlalchemy.orm import registry
from sqlmodel import SQLModel

from ..config.running_config import RunningConfig
from ..engine.database_engine import DatabaseEngine

auth_registry = registry()


class RegistryModel(SQLModel, registry=auth_registry):
    ...


# 用于 Controller
def get_engine_name():
    return RunningConfig.get_engine_name("Auth", "shudaodao_auth")


# noinspection DuplicatedCode
setattr(auth_registry, "engine_name", get_engine_name())


# 用于 Controller
def get_schema_name():
    return RunningConfig.get_controller_schema("shudaodao_auth")


# SQLModel 类: __table_args__ = {"schema": "用于这里"}
def get_table_schema():
    if DatabaseEngine().support_schema(name=get_engine_name()):
        return RunningConfig.get_sqlmodel_schema("shudaodao_auth")
    return None


# SQLModel 类: foreign_key= 用于这里 -> schema_name.t_table_name.field_id"
def get_foreign_schema():
    table_schema = get_table_schema()
    return table_schema + "." if table_schema else ""
