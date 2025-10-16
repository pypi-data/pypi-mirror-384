#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# @License  ：(C)Copyright 2025, 数道智融科技
# @Author   ：李锋
# @Software ：PyCharm
# @Date     ：2025/6/22 下午6:32
# @Desc     ：

from typing import Literal, Optional, Dict, Any, List

from pydantic import BaseModel, Field

from .context import ContextConfigSetting


class LocalConfigSetting(BaseModel):
    engine: Literal["transformers", "vllm", "sentence_transformers"] = "transformers"
    engine_options: Dict[str, Any] = {}
    path: str = ""
    method_kwargs: Dict[str, Any] = {}


class RemoteConfigSetting(BaseModel):
    model: str = ""
    url: str = ""
    key: str = ""
    method_kwargs: Dict[str, Any] = {}


class ModelConfigSetting(BaseModel):
    name: str = Field(..., description="唯一标识")
    enabled: bool = Field(True, description="是否启用")
    proxy: Literal["local", "remote"] = "local"
    field_think: Optional[str] = Field("", description="思考模型的标签字段")
    local: LocalConfigSetting = LocalConfigSetting()
    remote: Optional[RemoteConfigSetting] = RemoteConfigSetting()


class ModelCollectionConfigSetting(BaseModel):
    context: Optional[List[ContextConfigSetting]] = Field(None, description="上下文配置")
    language_models: list[ModelConfigSetting] = Field(None, description="语言模型")
    embedding_models: list[ModelConfigSetting] = Field(None, description="嵌入模型")
    reranker_models: list[ModelConfigSetting] = Field(None, description="重排序模型")
