#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/7/20 下午1:21
# @Desc     ：

from pydantic import BaseModel


class FastAPIConfigSetting(BaseModel):
    """FastAPI 配置

    Attributes:
        host (str): 监听主机，默认 0.0.0.0
        port (int): 监听端口，默认 8000
        page (str): 默认页面路径，默认为 pages/index.html
    """
    host: str = "0.0.0.0"
    port: int = 8000
    page: str = "pages/index.html"
    workers: int = 5
    reload: bool = True
    name: str = "数道智融科技Web应用平台"
    version: str = "0.1.0"
