# -- coding: utf-8 --
# Project: auth
# Created Date: 2025-01-09
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from fastapi import Request, HTTPException
from typing import Optional, Union, Dict, Literal
from .type import AuthData


def get_auth_data(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> AuthData:
    """
    从请求中获取认证数据
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        AuthData: 认证数据
        
    Raises:
        HTTPException: 当认证数据不存在时抛出 401 错误（仅限 FastAPI）
        ValueError: 当使用 dict 引擎且认证数据不存在时
    """
    if engine == "fastapi":
        if not isinstance(request, Request):
            raise TypeError("request must be a FastAPI Request object when engine='fastapi'")
        auth_data = getattr(request.state, 'auth_data', None)
        if not auth_data:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Unauthorized",
                    "message": "Authentication data not found",
                    "code": "AUTH_NOT_FOUND"
                }
            )
        return auth_data
    elif engine == "dict":
        if not isinstance(request, dict):
            raise TypeError("request must be a dict when engine='dict'")
        auth_data = request.get('auth_data')
        if not auth_data:
            raise ValueError("Authentication data not found in request dict")
        return auth_data
    else:
        raise ValueError("engine must be either 'fastapi' or 'dict'")


def get_current_user_id(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> str:
    """
    获取当前用户ID
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        str: 用户ID
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.user_id


def get_current_tenant_id(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> str:
    """
    获取当前租户ID
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        str: 租户ID
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.auth_tenant_id


def get_current_company(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> str:
    """
    获取当前公司ID
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        str: 公司ID
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.current_company


def get_company_unique_no(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> str:
    """
    获取当前公司唯一编号
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        str: 公司唯一编号
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.company_unique_no


def get_impersonation(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> str:
    """
    获取当前代表的租户ID
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        str: 代表的租户ID
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.impersonation


def get_current_client(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> str:
    """
    获取当前客户端标识
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        str: 客户端标识
    """
    auth_data = get_auth_data(request, engine)
    return auth_data.client


def is_impersonating(
    request: Union[Request, Dict[str, str]], 
    engine: Literal["fastapi", "dict"] = "fastapi"
) -> bool:
    """
    检查是否正在代表其他租户
    
    Args:
        request: FastAPI Request 对象或包含认证数据的字典
        engine: 请求引擎类型，默认为 "fastapi"
        
    Returns:
        bool: 是否正在代表其他租户
    """
    auth_data = get_auth_data(request, engine)
    return bool(auth_data.impersonation and auth_data.impersonation != auth_data.auth_tenant_id)
