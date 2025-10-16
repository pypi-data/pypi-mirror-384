#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/9/21 下午3:11
# @Desc     ：
# !/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/6/22 下午6:32
# @Desc     ：

from typing import List

from pydantic import BaseModel, Field


class RouterConfigSetting(BaseModel):
    name: str = Field(..., description="包名")
    enabled: bool = Field(True, description="是否启用")
    prefix: str = Field("", description="url前缀")
    tags: List[str] = Field(None, description="文档分类标签")
