#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/6/29 下午10:17
# @Desc     ：

from typing import Literal

from pydantic import BaseModel, Field


class ContextConfigSetting(BaseModel):
    name: str = Field(..., description="应用唯一标识")
    enabled: bool = Field(True, description="是否启用")
    storage: Literal["disabled", "redis", "disk"] = Field(description="持久化方式")
    desc: str = Field("", description="描述")
    redis: str = Field("Default", description="Redis配置的id值")
    disk: str = Field("Default", description="文件存储配置的id值")
    database: str = Field("Default", description="数据库配置的id值")
