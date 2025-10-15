# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 09 Th
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


# -- coding: utf-8 --
# Project: response
# Created Date: 2025 05 Tu
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI


from pydantic import BaseModel, Field
from typing import List, Literal


class UserCompanyInfo(BaseModel):
    name: str = Field(description="公司id")
    full_name: str = Field(description="公司名称")

class UserBaseInfo(BaseModel):
    name: str = Field(description="用户名id")
    email: str = Field(description="邮箱")
    first_name: str = Field(description="名")
    full_name: str = Field(description="全名")
    language: str = Field(description="语言")
    time_zone: str = Field(description="时区")
    auth_tenant_id: str = Field(description="租户id")
    current_company: str = Field(description="当前公司")
    available_companies: List[UserCompanyInfo] = Field(description="用户在租户下可以访问的公司列表", default_factory=list)


class UserPermissionInfo(BaseModel):
    can_select: List[str] = Field(description="可以查询的文档", default_factory=list)
    can_read: List[str] = Field(description="可以读取的文档", default_factory=list)
    can_write: List[str] = Field(description="可以写入的文档", default_factory=list)
    can_create: List[str] = Field(description="可以创建的文档", default_factory=list)
    can_delete: List[str] = Field(description="可以删除的文档", default_factory=list)
    can_submit: List[str] = Field(description="可以提交的文档", default_factory=list)
    can_cancel: List[str] = Field(description="可以取消的文档", default_factory=list)
    can_search: List[str] = Field(description="可以搜索的文档", default_factory=list)

    # def __init__(self, user: str):
    #     super().__init__()
    
    # def can_select(self, doctype: str) -> bool:
    #     return doctype in self.can_select
    
    # def can_read(self, doctype: str) -> bool:
    #     return doctype in self.can_read
    
    # def can_write(self, doctype: str) -> bool:
    #     return doctype in self.can_write
    
    # def can_create(self, doctype: str) -> bool:
    #     return doctype in self.can_create
    
    # def can_delete(self, doctype: str) -> bool:
    #     return doctype in self.can_delete
    
    # def can_submit(self, doctype: str) -> bool:
    #     return doctype in self.can_submit
    
    # def can_cancel(self, doctype: str) -> bool:
    #     return doctype in self.can_cancel
    
    # def can_search(self, doctype: str) -> bool:
    #     return doctype in self.can_search
    
class UserTenantInfo(BaseModel):
    name: str = Field(description="租户id")
    tenant_name: str = Field(description="租户名称")


class UserCurrentCompanyInfo(BaseModel):
    name: str = Field(description="公司id")
    full_name: str = Field(description="公司名称")
    unique_no: str = Field(description="公司唯一编号")
    country_region: str = Field(description="国家")
    default_currency: str = Field(description="货币")
    company_size: str = Field(description="公司规模")
    entity_type: Literal["Enterprise", "Individual", "Other"] = Field(description="公司类型")
    company_profile: str = Field(description="公司业务特点提示词", default="")
    
class UserProfileInfo(BaseModel):
    user_base_info: UserBaseInfo = Field(description="用户基础信息")
    user_permissions: UserPermissionInfo = Field(description="用户权限")
    user_tenant_info: UserTenantInfo = Field(description="用户租户信息")
    user_current_company_info: UserCurrentCompanyInfo = Field(description="用户当前公司信息")
    
    