# -- coding: utf-8 --
# Project: auth
# Created Date: 2025-01-09
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from typing import Dict, Optional, Union, Literal
from .type import AuthData
from fastapi import Request


def parse_auth_headers(headers: Dict[str, str]) -> Optional[AuthData]:
    """
    从 HTTP headers 中解析认证信息并转换为 AuthData
    
    Args:
        headers: HTTP headers 字典
        
    Returns:
        AuthData 对象，如果解析失败则返回 None
        
    Raises:
        ValueError: 当必需的头信息缺失或格式错误时
    """
    try:
        # 获取必需的头信息（注意：HTTP headers 会自动转换为小写）
        user_id = headers.get("x-fiuai-user")
        auth_tenant_id = headers.get("x-fiuai-auth-tenant-id")
        current_company_str = headers.get("x-fiuai-current-company", "")
        impersonation = headers.get("x-fiuai-impersonation", "")
        unique_no = headers.get("x-fiuai-unique-no", "")
        trace_id = headers.get("x-fiuai-trace-id", "")
        client = headers.get("x-fiuai-client", "unknown")
        
        # 验证必需字段
        if not user_id:
            raise ValueError("Missing required header: x-fiuai-user")
        if not auth_tenant_id:
            raise ValueError("Missing required header: x-fiuai-auth-tenant-id")
        
        # 解析当前公司列表（逗号分隔）
        current_company = []
        if current_company_str:
            current_company = [company.strip() for company in current_company_str.split(",") if company.strip()]
        
        # 检查是否有有效的公司信息
        if not current_company:
            raise ValueError("Missing required header: x-fiuai-current-company")
        
        # 如果没有提供 unique_no，使用第一个公司ID作为默认值
        if not unique_no:
            unique_no = current_company[0]
            
        return AuthData(
            user_id=user_id,
            auth_tenant_id=auth_tenant_id,
            current_company=current_company[0],
            impersonation=impersonation,
            company_unique_no=unique_no,
            trace_id=trace_id,
            client=client
        )
        
    except Exception as e:
        # 记录错误但不抛出异常，返回 None 表示解析失败
        
        raise


def extract_auth_from_request(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> Optional[AuthData]:
    """
    从请求对象中提取认证信息
    
    Args:
        request: FastAPI Request 对象或原生 headers 字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        AuthData 对象，如果解析失败则返回 None, 或抛出异常
        
    Raises:
        TypeError: 当 request 类型与 engine 不匹配时
    """
    if engine == "fastapi":
        if not isinstance(request, Request):
            raise TypeError("request must be a FastAPI Request object when engine='fastapi'")
        headers = dict(request.headers)
    elif engine == "dict":
        if not isinstance(request, dict):
            raise TypeError("request must be a dict when engine='dict'")
        headers = request
    else:
        raise ValueError("engine must be either 'fastapi' or 'dict'")
    
    return parse_auth_headers(headers)
