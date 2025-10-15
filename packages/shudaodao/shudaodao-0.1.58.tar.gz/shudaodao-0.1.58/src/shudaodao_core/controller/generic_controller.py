#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/10/9 下午10:54
# @Desc     ：泛型控制器基类，自动注册标准 CRUD 和查询路由


from typing import Type, Generic

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from .router_config import RouterConfig
from ..auth.auth_router import AuthRouter
from ..schemas.query_request import QueryRequest
from ..services.data_service import DataService
from ..type.var import SQLModelDB, SQLModelCreate, SQLModelUpdate, SQLModelResponse
from ..utils.response_utils import ResponseUtil


class GenericController(Generic[SQLModelDB, SQLModelCreate, SQLModelUpdate, SQLModelResponse]):
    """泛型路由控制器基类，自动注册标准 CRUD 与分页查询路由。

    该类通过泛型参数绑定数据模型与 Schema，结合 `RouterConfig` 控制各操作的启用状态、
    权限策略和响应消息，实现“声明式”资源控制器。

    泛型参数说明：
        SQLModelDB: 对应数据库模型类（继承自 SQLModel）。
        SQLModelCreate: 用于创建资源的请求 Schema。
        SQLModelUpdate: 用于更新资源的请求 Schema。
        SQLModelResponse: 用于响应的输出 Schema（通常排除敏感字段）。

    路由注册行为：
        - 每个操作（create/read/update/delete/query）是否注册，由对应的 `RouterConfig.enabled` 控制；
        - 所有路由均挂载到传入的 `AuthRouter` 实例上；
        - 权限控制（auth/auth_role/auth_obj/auth_act）由 `RouterConfig` 提供；
        - 数据操作委托给 `DataService`，响应统一由 `ResponseUtil` 包装。
    """

    def __init__(
            self,
            *,
            auth_router: AuthRouter,
            model_class: Type[SQLModelDB],
            create_schema: Type[SQLModelCreate],
            update_schema: Type[SQLModelUpdate],
            response_schema: Type[SQLModelResponse],

            create_router: RouterConfig,
            update_router: RouterConfig,
            read_router: RouterConfig,
            delete_router: RouterConfig,
            query_router: RouterConfig,
    ):
        """初始化泛型控制器并自动注册路由。

        Args:
            auth_router (AuthRouter): 已配置的认证路由容器，所有子路由将注册到此实例。
            model_class (Type[SQLModelDB]): 数据库模型类。
            create_schema (Type[SQLModelCreate]): 创建请求的 Pydantic 模型。
            update_schema (Type[SQLModelUpdate]): 更新请求的 Pydantic 模型。
            response_schema (Type[SQLModelResponse]): 响应返回的 Pydantic 模型。

            create_router (RouterConfig): 创建操作的路由配置。
            update_router (RouterConfig): 更新操作的路由配置。
            read_router (RouterConfig): 读取单个资源的路由配置。
            delete_router (RouterConfig): 删除操作的路由配置。
            query_router (RouterConfig): 分页/条件查询操作的路由配置。
        """
        self._router = auth_router
        self._model_class = model_class
        self._create_schema = create_schema
        self._update_schema = update_schema
        self._response_schema = response_schema

        self._create_router = create_router
        self._update_router = update_router
        self._read_router = read_router
        self._delete_router = delete_router
        self._query_router = query_router

        self._register_crud_routes()

    def _register_crud_routes(self):
        """注册标准的 CRUD 和 Query 路由到 AuthRouter。

        为避免 FastAPI 在闭包中捕获 `self` 导致的类型推断问题，
        在路由函数内部使用局部变量引用 Schema 类型（如 `create_schema_type`）。
        """
        # 在方法内部获取类型引用，避免 self._xxx 在闭包中引发类型或作用域问题
        create_schema_type = self._create_schema
        update_schema_type = self._update_schema

        if self._query_router.enabled:
            @self._router.post(
                path="/query",
                auth=self._query_router.auth,
                auth_role=self._query_router.auth_role,
                auth_obj=self._query_router.auth_obj,
                auth_act=self._query_router.auth_act,
                summary=self._query_router.summary
            )
            async def query_route(
                    *, query_request: QueryRequest,
                    db: AsyncSession = Depends(self._router.get_async_session)
            ):
                """分页或条件查询资源列表。

                Args:
                    query_request (QueryRequest): 查询参数（含分页、过滤、排序等）。
                    db (AsyncSession): 异步数据库会话。

                Returns:
                    Response: 成功响应，包含查询结果列表及元信息。
                """
                query_result = await DataService.query(
                    db, query_request, model_class=self._model_class,
                    response_class=self._response_schema
                )
                return ResponseUtil.success(
                    message=self._query_router.message, data=query_result,
                )

        if self._create_router.enabled:
            @self._router.post(
                path="",
                auth=self._create_router.auth,
                auth_role=self._create_router.auth_role,
                auth_obj=self._create_router.auth_obj,
                auth_act=self._create_router.auth_act,
                summary=self._create_router.summary
            )
            async def create_route(
                    *, create_model: create_schema_type,
                    db: AsyncSession = Depends(self._router.get_async_session)
            ):
                """创建新资源。

                Args:
                    create_model (SQLModelCreate): 创建请求体。
                    db (AsyncSession): 异步数据库会话。

                Returns:
                    Response: 成功响应，包含创建后的资源数据。
                """
                data_create = await DataService.create(
                    db, model_class=self._model_class,
                    create_model=create_model,
                    response_class=self._response_schema
                )
                return ResponseUtil.success(
                    data=data_create, message=self._create_router.message
                )

        if self._read_router.enabled:
            @self._router.get(
                path="/{primary_id}",
                auth=self._read_router.auth,
                auth_role=self._read_router.auth_role,
                auth_obj=self._read_router.auth_obj,
                auth_act=self._read_router.auth_act,
                summary=self._read_router.summary
            )
            async def read_route(
                    *, primary_id: int,
                    db: AsyncSession = Depends(self._router.get_async_session)
            ):
                """根据主键获取单个资源。

                Args:
                    primary_id (int): 资源主键 ID。
                    db (AsyncSession): 异步数据库会话。

                Returns:
                    Response: 成功响应，包含资源详情。
                """
                data_read = await DataService.read(
                    db, primary_id, model_class=self._model_class,
                    response_class=self._response_schema
                )
                return ResponseUtil.success(
                    data=data_read, message=self._read_router.message
                )

        if self._update_router.enabled:
            @self._router.patch(
                path="/{primary_id}",
                auth=self._update_router.auth,
                auth_role=self._update_router.auth_role,
                auth_obj=self._update_router.auth_obj,
                auth_act=self._update_router.auth_act,
                summary=self._update_router.summary
            )
            async def update_route(
                    *, primary_id: int, update_model: update_schema_type,
                    db: AsyncSession = Depends(self._router.get_async_session)
            ):
                """根据主键部分更新资源。

                Args:
                    primary_id (int): 资源主键 ID。
                    update_model (SQLModelUpdate): 更新字段（部分更新）。
                    db (AsyncSession): 异步数据库会话。

                Returns:
                    Response: 成功响应，包含更新后的资源数据。
                """
                data_update = await DataService.update(
                    db, primary_id, model_class=self._model_class,
                    update_model=update_model,
                    response_class=self._response_schema
                )
                return ResponseUtil.success(
                    data=data_update, message=self._update_router.message
                )

        if self._delete_router.enabled:
            @self._router.delete(
                path="/{primary_id}",
                auth=self._delete_router.auth,
                auth_role=self._delete_router.auth_role,
                auth_obj=self._delete_router.auth_obj,
                auth_act=self._delete_router.auth_act,
                summary=self._delete_router.summary
            )
            async def delete_route(
                    *, primary_id: int,
                    db: AsyncSession = Depends(self._router.get_async_session)
            ):
                """根据主键删除资源。

                Args:
                    primary_id (int): 资源主键 ID。
                    db (AsyncSession): 异步数据库会话。

                Returns:
                    Response: 成功响应，无返回数据体。
                """
                await DataService.delete(db, primary_id, model_class=self._model_class)
                return ResponseUtil.success(
                    message=self._delete_router.message
                )
