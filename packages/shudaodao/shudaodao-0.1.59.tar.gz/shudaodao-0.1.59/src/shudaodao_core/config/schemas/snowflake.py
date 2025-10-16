#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/8/24 下午10:56
# @Desc     ：


from pydantic import BaseModel, Field


class SnowflakeConfigSetting(BaseModel):
    instance_id: int = Field(..., description="实例ID（机器ID），用于区分不同的生成器实例")
    epoch_time: int = Field(1735689600000, description="自定义起始时间戳（毫秒), 默认2025-01-01")
