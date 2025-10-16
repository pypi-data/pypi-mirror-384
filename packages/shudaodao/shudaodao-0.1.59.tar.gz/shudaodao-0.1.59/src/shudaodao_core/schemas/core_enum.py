#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/9/26 上午11:57
# @Desc     ：

from ..enum.label_enum import LabelEnum


class UserStatus(LabelEnum):
    """用户状态枚举"""
    ACTIVE = (1, "活跃", "账号正常")
    INACTIVE = (2, "停用", "账号已禁用")
    PENDING = (3, "待激活", "注册后未激活")


class Gender(LabelEnum):
    """性别枚举"""
    UNKNOWN = (0, "未知", "未设置性别")
    MALE = (1, "男", "男性用户")
    FEMALE = (2, "女", "女性用户")


class AccountType(LabelEnum):
    """账户类型枚举"""
    PERSONAL = (1, "个人", "个人用户账户")
    ENTERPRISE = (2, "企业", "企业用户账户")
    ADMIN = (99, "管理员", "系统管理员账户")
