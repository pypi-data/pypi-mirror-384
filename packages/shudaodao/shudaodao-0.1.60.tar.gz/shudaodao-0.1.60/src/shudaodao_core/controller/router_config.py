#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/10/9 下午11:45
# @Desc     ：路由行为与权限配置类

from typing import Optional


class RouterConfig:
    """路由配置类，用于声明单个 CRUD 操作的行为与权限策略。

    该类作为 `GenericController` 中各操作（create/read/update/delete/query）的配置载体，
    支持动态启用/禁用路由、配置认证要求、定义 RBAC 权限三元组（对象-动作-角色），
    并提供 OpenAPI 文档所需的摘要（summary）和成功响应消息（message）。

    典型应用场景：
        - 禁用某资源的删除接口：`delete_router=RouterConfig(enabled=False)`
        - 为查询接口设置自定义成功消息：`message="查询成功"`
        - 配置细粒度权限：`auth_obj="user", auth_act="read", auth_role="admin"`

    注意：
        - 若 `auth=True`（默认），则路由受权限中间件保护；
        - `auth_role`、`auth_obj`、`auth_act` 通常用于基于属性的访问控制（ABAC）或 RBAC 系统；
        - 所有字段均为可选，未设置时使用默认值（如 `enabled=True`, `auth=True`）。
    """

    def __init__(
        self,
        *,
        enabled: Optional[bool] = True,
        auth: Optional[bool] = True,
        auth_role: Optional[str] = None,
        auth_obj: Optional[str] = None,
        auth_act: Optional[str] = None,
        message: Optional[str] = None,
        summary: Optional[str] = "",
    ):
        """初始化路由配置。

        Args:
            enabled (bool, optional): 是否启用该路由。默认为 True。
            auth (bool, optional): 是否需要认证。默认为 True。
            auth_role (str, optional): 允许访问的角色（如 "admin", "user"）。用于权限校验。
            auth_obj (str, optional): 权限控制的对象类型（如 "user", "order"）。通常对应资源名。
            auth_act (str, optional): 权限控制的动作（如 "create", "read", "delete"）。
            message (str, optional): 操作成功时返回的提示消息。
            summary (str, optional): OpenAPI 文档中该接口的简要描述。
        """
        self.enabled = enabled
        self.auth = auth
        self.auth_role = auth_role
        self.auth_obj = auth_obj
        self.auth_act = auth_act
        self.message = message
        self.summary = summary
