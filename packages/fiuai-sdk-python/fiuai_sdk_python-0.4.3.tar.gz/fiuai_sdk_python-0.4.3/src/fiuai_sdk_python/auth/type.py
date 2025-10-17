# -- coding: utf-8 --
# Project: auth
# Created Date: 2025 09 Th
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


from pydantic import BaseModel, Field
from typing import List

class AuthData(BaseModel):
    user_id: str = Field(description="用户ID")
    auth_tenant_id: str = Field(description="租户ID")
    current_company: str = Field(description="当前公司ID列表")
    impersonation: str = Field(description="当前代表的租户ID", default="")
    company_unique_no: str = Field(description="当前公司唯一编号,正常情况等于current_company")
    trace_id: str = Field(description="追踪ID", default="")
    client: str = Field(description="客户端标识", default="unknown")



    # edoc

class AuthHeader(BaseModel):
    """HTTP 认证头信息模型"""
    x_fiuai_user: str = Field(alias="x-fiuai-user", description="用户ID")
    x_fiuai_auth_tenant_id: str = Field(alias="x-fiuai-auth-tenant-id", description="租户ID")
    x_fiuai_current_company: str = Field(alias="x-fiuai-current-company", default="", description="当前公司ID列表（逗号分隔）")
    x_fiuai_unique_no: str = Field(alias="x-fiuai-unique-no", default="", description="当前公司唯一编号,正常情况等于current_company")
    x_fiuai_impersonation: str = Field(alias="x-fiuai-impersonation", default="", description="当前代表的租户ID")
    x_fiuai_lang: str = Field(alias="x-fiuai-lang", default="zh", description="用户当前语言")
    x_fiuai_trace_id: str = Field(alias="x-fiuai-trace-id", default="", description="追踪ID")
    x_fiuai_client: str = Field(alias="x-fiuai-client", default="unknown", description="客户端标识")
    accept_language: str = Field(alias="accept-language", default="zh", description="语言")
    
    class Config:
        populate_by_name = True