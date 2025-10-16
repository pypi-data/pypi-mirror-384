#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/9/26 下午12:21
# @Desc     ：
from pydantic import BaseModel


class EnumDisplay(BaseModel):
    value: int
    label: str
    description: str
