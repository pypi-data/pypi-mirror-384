#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/8/28 下午2:02
# @Desc     ：

from typing import Optional

from pydantic import BaseModel


class Paging(BaseModel):
    total: Optional[int] = None
    page: int
    size: int
    pages: Optional[int] = None
    rows: Optional[list] = None

    def set_total(self, total):
        self.total = total
        self.pages = (total + self.size - 1) // self.size


