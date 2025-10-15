from ..exception.service_exception import DataNotFoundException as DataNotFoundException
from ..schemas.element import Paging as Paging
from ..schemas.query_request import QueryRequest as QueryRequest
from ..tools.query_builder import QueryBuilder as QueryBuilder
from ..tools.tenant_checker import TenantManager as TenantManager
from ..type.var import (
    SQLModelCreate as SQLModelCreate,
    SQLModelDB as SQLModelDB,
    SQLModelResponse as SQLModelResponse,
    SQLModelUpdate as SQLModelUpdate,
)
from sqlalchemy import ColumnElement
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSession
from typing import Any

class DataService:
    """通用数据服务类，提供基于 SQLModel 的 CRUD 及高级查询能力。

    支持多租户隔离、自动字段填充（如创建人、租户ID）、分页/列表/树形查询格式，
    并可灵活指定响应模型（response_class）以实现数据脱敏或转换。
    """
    @classmethod
    def db_insert(
        cls,
        db: AsyncSession,
        *,
        db_model_class: type[SQLModelDB],
        create_model: SQLModelCreate | dict[str, Any],
    ) -> SQLModelDB:
        """在数据库会话中插入新记录（不提交事务）。

        此方法为底层插入操作，不自动提交，适用于事务组合场景。

        Args:
            db (AsyncSession): 异步数据库会话。
            db_model_class (Type[SQLModelDB]): 数据库模型类。
            create_model (SQLModelCreate | dict[str, Any]): 创建数据，可为 Pydantic 模型或字典。

        Returns:
            SQLModelDB: 已添加到会话但未提交的数据库模型实例。
        """
    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        *,
        model_class: type[SQLModelDB],
        create_model: SQLModelCreate | dict[str, Any],
        response_class: type[SQLModelResponse] = None,
        auto_commit: bool = True,
    ) -> SQLModelDB | SQLModelResponse:
        """创建新记录并可选自动提交。

        Args:
            db (AsyncSession): 异步数据库会话。
            model_class (Type[SQLModelDB]): 数据库模型类。
            create_model (SQLModelCreate | dict[str, Any]): 创建数据。
            response_class (Type[SQLModelResponse], optional): 响应模型类，用于返回转换后的数据。
            auto_commit (bool): 是否自动提交事务。默认为 True。

        Returns:
            SQLModelDB | SQLModelResponse: 创建成功的模型实例或其响应表示。
        """
    @classmethod
    async def db_get(
        cls, db: AsyncSession, primary_id: int, *, db_model_class: type[SQLModelDB]
    ) -> SQLModelDB | None:
        """根据主键 ID 获取数据库记录（不抛异常）。

        同时执行租户权限校验，若记录不属于当前租户则视为不存在。

        Args:
            db (AsyncSession): 异步数据库会话。
            primary_id (int): 主键 ID。
            db_model_class (Type[SQLModelDB]): 数据库模型类。

        Returns:
            SQLModelDB | None: 若存在且权限允许，返回模型实例；否则返回 None。
        """
    @classmethod
    async def read(
        cls,
        db: AsyncSession,
        primary_id: int,
        *,
        model_class: type[SQLModelDB],
        response_class: type[SQLModelResponse] = None,
    ) -> SQLModelDB | SQLModelResponse:
        """读取指定 ID 的记录，若不存在则抛出异常。

        Args:
            db (AsyncSession): 异步数据库会话。
            primary_id (int): 主键 ID。
            model_class (Type[SQLModelDB]): 数据库模型类。
            response_class (Type[SQLModelResponse], optional): 响应模型类。

        Returns:
            SQLModelDB | SQLModelResponse: 查询到的记录。

        Raises:
            DataNotFoundException: 若记录不存在或无权限访问。
        """
    @classmethod
    async def db_update(
        cls,
        db: AsyncSession,
        primary_id: int,
        *,
        model_class: type[SQLModelDB],
        update_model: SQLModelUpdate | dict[str, Any],
    ) -> SQLModelDB | None:
        """更新指定 ID 的记录（不提交事务，不抛异常）。

        Args:
            db (AsyncSession): 异步数据库会话。
            primary_id (int): 主键 ID。
            model_class (Type[SQLModelDB]): 数据库模型类。
            update_model (SQLModelUpdate | dict[str, Any]): 更新数据。

        Returns:
            SQLModelDB | None: 更新后的模型实例；若记录不存在，返回 None。
        """
    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        primary_id: int,
        *,
        model_class: type[SQLModelDB],
        update_model: SQLModelUpdate | dict[str, Any],
        response_class: type[SQLModelResponse] = None,
        auto_commit: bool = True,
    ) -> SQLModelDB | SQLModelResponse:
        """更新记录并可选自动提交。

        Args:
            db (AsyncSession): 异步数据库会话。
            primary_id (int): 主键 ID。
            model_class (Type[SQLModelDB]): 数据库模型类。
            update_model (SQLModelUpdate | dict[str, Any]): 更新数据。
            response_class (Type[SQLModelResponse], optional): 响应模型类。
            auto_commit (bool): 是否自动提交事务。默认为 True。

        Returns:
            SQLModelDB | SQLModelResponse: 更新后的记录。

        Raises:
            DataNotFoundException: 若记录不存在或无权限访问。
        """
    @classmethod
    async def db_delete(
        cls, db: AsyncSession, primary_id: int, *, db_model_class: type[SQLModelDB]
    ) -> bool:
        """删除指定 ID 的记录（不提交事务，不抛异常）。

        Args:
            db (AsyncSession): 异步数据库会话。
            primary_id (int): 主键 ID。
            db_model_class (Type[SQLModelDB]): 数据库模型类。

        Returns:
            bool: 若成功删除返回 True；若记录不存在或无权限，返回 False。
        """
    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        primary_id: int,
        *,
        model_class: type[SQLModelDB],
        auto_commit: bool = True,
    ) -> bool:
        """删除记录并可选自动提交。

        Args:
            db (AsyncSession): 异步数据库会话。
            primary_id (int): 主键 ID。
            model_class (Type[SQLModelDB]): 数据库模型类。
            auto_commit (bool): 是否自动提交事务。默认为 True。

        Returns:
            bool: 删除成功返回 True。

        Raises:
            DataNotFoundException: 若记录不存在或无权限访问。
        """
    @classmethod
    async def query_columns(
        cls,
        db: AsyncSession,
        *,
        model_class: type[SQLModelDB],
        condition: list[ColumnElement] | ColumnElement | Any,
    ) -> SQLModelDB:
        """根据列条件查询单条记录。

        自动附加租户过滤条件。

        Args:
            db (AsyncSession): 异步数据库会话。
            model_class (Type[SQLModelDB]): 数据库模型类。
            condition (Union[List[ColumnElement], ColumnElement, Any]): 查询条件。

        Returns:
            SQLModelDB: 查询到的第一条记录，若无则返回 None（但类型提示为模型，实际可能为 None）。
        """
    @classmethod
    async def query(
        cls,
        db: AsyncSession,
        query: QueryRequest,
        *,
        model_class: type[SQLModelDB],
        response_class: type[SQLModelResponse],
    ):
        """使用 QueryRequest 执行高级查询，支持分页、列表、树形三种格式。

        Args:
            db (AsyncSession): 异步数据库会话。
            query (QueryRequest): 查询请求对象，包含字段、条件、排序、分页等。
            model_class (Type[SQLModelDB]): 数据库模型类。
            response_class (Type[SQLModelResponse]): 响应模型类。

        Returns:
            Paging | list[SQLModelResponse] | dict: 根据 query.format 返回分页对象、列表或树形结构。
        """
    @classmethod
    def get_primary_key_name(
        cls, model_class: type[SQLModelDB]
    ) -> str | list[str] | None:
        """获取模型的主键字段名称。

        Args:
            model_class (type[SQLModelDB]): SQLModel 模型类。

        Returns:
            Union[str, list[str], None]:
                - 单个主键时返回字段名（str），
                - 复合主键时返回字段名列表（list[str]），
                - 无主键时返回 None。
        """
