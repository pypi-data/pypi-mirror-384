#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/9/2 下午4:24
# @Desc     ：

from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import BigInteger, Boolean
from sqlmodel import SQLModel

from .. import get_table_schema, RegistryModel
from ...schemas.response import BaseResponse
from ...sqlmodel_ext.field import Field
from ...utils.generate_unique_id import get_primary_id


class AuthUser(RegistryModel, table=True):
    """ 数据模型 - 数据库表 T_Auth_User 结构模型 """
    __tablename__ = "t_auth_user"
    __table_args__ = {"schema": get_table_schema(), "comment": "鉴权账户"}

    user_id: Optional[int] = Field(
        default_factory=get_primary_id, primary_key=True, sa_type=BigInteger, description="内码"
    )
    # --- 核心字段 ---
    username: str = Field(unique=True, index=True, max_length=50, description="账户名")
    name: str = Field(default=None, nullable=True, description="姓名")
    password: str = Field(description="密码")
    is_active: bool = Field(default=True, sa_type=Boolean, description="启用状态")

    last_login_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), description="最后登录时间")
    # --- 可修改字段 ---
    nickname: str = Field(default=None, nullable=True, description="昵称")
    picture: Optional[str] = Field(default=None, nullable=True, description="头像URL地址")
    email: Optional[EmailStr] = Field(default=None, nullable=True, description="邮件")
    # --- 用户验证增强 ---
    email_verified: Optional[bool] = Field(default=None, nullable=True, description="邮箱是否已验证")
    # --- 用户验证增强 ---
    totp_verified: bool = Field(default=True, nullable=True, description="启用身份验证器")
    # --- 内容源自业务 ---
    role: Optional[str] = Field(default=None, nullable=True, description="用户角色")
    roles: Optional[str] = Field(default=None, nullable=True, description="角色列表")
    groups: Optional[str] = Field(default=None, nullable=True, description="部门列表")
    permissions: Optional[str] = Field(default=None, nullable=True, description="权限列表")
    organization: Optional[str] = Field(default=None, nullable=True, description="所属组织")
    department: Optional[str] = Field(default=None, nullable=True, description="所在部门")
    job_title: Optional[str] = Field(default=None, nullable=True, description="职务职称")
    # --- 内部管理字段 ---
    create_by: Optional[str] = Field(default=None, nullable=True, description="创建人")
    create_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), nullable=True, description="创建日期")
    update_by: Optional[str] = Field(default=None, nullable=True, description="修改人")
    update_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), nullable=True, description="修改日期")
    tenant_id: Optional[int] = Field(default=None, nullable=True, sa_type=BigInteger, description="默认租户")
    staff_id: Optional[int] = Field(default=None, nullable=True, sa_type=BigInteger, description="默认用户")


class AuthUserRegister(SQLModel):
    """ 注册模型 """
    username: str = Field(min_length=5, max_length=50)
    password: str = Field(min_length=5)
    # --- 核心字段 ---
    name: str = Field(default=None, nullable=True, description="姓名")
    last_login_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), description="最后登录时间")
    # --- 可修改字段 ---
    nickname: str = Field(default=None, nullable=True, description="昵称")
    picture: Optional[str] = Field(default=None, nullable=True, description="头像URL地址")
    email: Optional[EmailStr] = Field(default=None, nullable=True, description="邮件")
    # --- 用户验证增强 ---
    email_verified: Optional[bool] = Field(default=None, nullable=True, description="邮箱是否已验证")
    # --- 内部管理字段 ---
    tenant_id: Optional[int] = Field(default=None, nullable=True, sa_type=BigInteger, description="默认租户")


class AuthLogin(SQLModel):
    """ 登录模型 """
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=5)


class AuthPassword(SQLModel):
    """ 修改密码模型 """
    old_password: str
    new_password: str = Field(min_length=6, max_length=50)


class AuthUserResponse(BaseResponse):
    """ 用户响应模型 """
    # --- 核心字段 ---
    user_id: Optional[int] = Field(sa_type=BigInteger, description="内码")
    sub: Optional[str] = Field(default=None)
    username: str = Field(..., description="用户名")
    name: Optional[str] = Field(default=None, description="姓名")
    nickname: Optional[str] = Field(default=None, description="昵称")
    email: Optional[EmailStr] = Field(default=None, description="邮件")
    email_verified: Optional[bool] = Field(default=None, description="邮箱是否已验证")
    # totp_verified: Optional[bool] = Field(default=None, description="启用身份验证器")
    picture: Optional[str] = Field(default=None, description="头像URL地址")
    last_login_at: Optional[datetime] = Field(default=None, description="最后登录时间")
    # --- 内容源自业务 ---
    # role: Optional[str] = Field(default=None, description="用户角色")
    # roles: Optional[str] = Field(default=None, description="角色列表")
    # groups: Optional[str] = Field(default=None, description="部门列表")
    # permissions: Optional[str] = Field(default=None, description="权限列表")
    # organization: Optional[str] = Field(default=None, description="所属组织")
    # department: Optional[str] = Field(default=None, description="所在部门")
    # job_title: Optional[str] = Field(default=None, description="职务职称")
