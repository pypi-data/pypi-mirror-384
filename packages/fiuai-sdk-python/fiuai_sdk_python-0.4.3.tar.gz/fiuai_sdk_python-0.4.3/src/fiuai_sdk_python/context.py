# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 01 09
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

import contextvars
import uuid
from typing import Dict, Any, Optional, Union, Literal
from .auth.type import AuthHeader


# 创建上下文变量来存储请求信息
_request_context: contextvars.ContextVar[Optional[Dict[str, Any]]] = contextvars.ContextVar('request_context', default=None)


class RequestContext:
    """请求上下文管理器"""
    
    def __init__(self, headers: Dict[str, Any]):
        """
        初始化请求上下文
        
        Args:
            headers: 请求头信息字典
        """
        self.headers = headers
        self._token = None
    
    def __enter__(self):
        """进入上下文"""
        self._token = _request_context.set(self.headers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self._token:
            _request_context.reset(self._token)
    
    @classmethod
    def from_fastapi_request(cls, request) -> 'RequestContext':
        """
        从 FastAPI 请求对象创建上下文
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            RequestContext: 请求上下文对象
        """
        headers = dict(request.headers)
        # 处理 company unique no 逻辑
        headers = cls._process_headers(headers)
        return cls(headers)
    
    @classmethod
    def from_dict(cls, headers: Dict[str, Any]) -> 'RequestContext':
        """
        从字典创建上下文
        
        Args:
            headers: 请求头信息字典
            
        Returns:
            RequestContext: 请求上下文对象
        """
        # 处理 company unique no 逻辑
        processed_headers = cls._process_headers(headers)
        return cls(processed_headers)
    
    @staticmethod
    def _process_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求头信息，确保 company unique no 有值，处理 trace id 和 client 信息
        
        Args:
            headers: 原始请求头信息
            
        Returns:
            Dict[str, Any]: 处理后的请求头信息
        """
        processed_headers = headers.copy()
        
        # 获取 current company 值
        current_company = processed_headers.get("x-fiuai-current-company", "")
        
        # 如果 company unique no 为空，使用 current company 的值
        unique_no = processed_headers.get("x-fiuai-unique-no", "")
        if not unique_no and current_company:
            processed_headers["x-fiuai-unique-no"] = current_company
        
        # 处理 trace id：优先使用 x-kong-request-id，如果没有则生成
        trace_id = processed_headers.get("x-fiuai-trace-id", "")
        if not trace_id:
            kong_request_id = processed_headers.get("x-kong-request-id", "")
            if kong_request_id:
                processed_headers["x-fiuai-trace-id"] = kong_request_id
            else:
                # 生成新的 trace id
                processed_headers["x-fiuai-trace-id"] = str(uuid.uuid4())
        
        # 确保 X-Fiuai-Client 字段存在（如果不存在则设为 "unknown"）
        if "x-fiuai-client" not in processed_headers:
            processed_headers["x-fiuai-client"] = "unknown"
        
        return processed_headers
    
    def validate(self, required_fields: list = None) -> tuple[bool, list]:
        """
        验证当前上下文是否包含 AuthHeader 所需的字段
        
        Args:
            required_fields: 必需字段列表，如果为None则使用默认的必需字段
            
        Returns:
            tuple[bool, list]: (是否有效, 缺失字段列表)
        """
        if required_fields is None:
            # AuthHeader 的必需字段
            required_fields = [
                "x-fiuai-user",
                "x-fiuai-auth-tenant-id", 
                "x-fiuai-current-company",
                "x-fiuai-client"
            ]
        
        missing_fields = []
        for field in required_fields:
            if field not in self.headers or not self.headers[field]:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    def get_missing_fields(self, required_fields: list = None) -> list:
        """
        获取缺失的字段列表
        
        Args:
            required_fields: 必需字段列表，如果为None则使用默认的必需字段
            
        Returns:
            list: 缺失字段列表
        """
        _, missing_fields = self.validate(required_fields)
        return missing_fields
    
    def is_valid(self, required_fields: list = None) -> bool:
        """
        检查当前上下文是否有效
        
        Args:
            required_fields: 必需字段列表，如果为None则使用默认的必需字段
            
        Returns:
            bool: 是否有效
        """
        is_valid, _ = self.validate(required_fields)
        return is_valid


def get_current_headers() -> Optional[Dict[str, Any]]:
    """
    获取当前上下文中的请求头信息
    
    Returns:
        Optional[Dict[str, Any]]: 当前请求头信息，如果不在上下文中则返回 None
    """
    return _request_context.get()


def validate_current_context(required_fields: list = None) -> tuple[bool, list]:
    """
    验证当前上下文是否包含必需的字段
    
    Args:
        required_fields: 必需字段列表，如果为None则使用默认的必需字段
        
    Returns:
        tuple[bool, list]: (是否有效, 缺失字段列表)
    """
    current_headers = get_current_headers()
    if not current_headers:
        if required_fields is None:
            required_fields = [
                "x-fiuai-user",
                "x-fiuai-auth-tenant-id", 
                "x-fiuai-current-company",
                "x-fiuai-client"
            ]
        return False, required_fields
    
    context = RequestContext(current_headers)
    return context.validate(required_fields)


def get_current_missing_fields(required_fields: list = None) -> list:
    """
    获取当前上下文中缺失的字段列表
    
    Args:
        required_fields: 必需字段列表，如果为None则使用默认的必需字段
        
    Returns:
        list: 缺失字段列表
    """
    _, missing_fields = validate_current_context(required_fields)
    return missing_fields


def is_current_context_valid(required_fields: list = None) -> bool:
    """
    检查当前上下文是否有效
    
    Args:
        required_fields: 必需字段列表，如果为None则使用默认的必需字段
        
    Returns:
        bool: 是否有效
    """
    is_valid, _ = validate_current_context(required_fields)
    return is_valid


def extract_auth_headers_from_context(
    username: str,
    auth_tenant_id: str,
    current_company: str,
    impersonation: str = "",
    unique_no: str = "",
    trace_id: str = "",
    client: str = "",
    lang: str = "zh",
    accept_language: str = "zh"
) -> AuthHeader:
    """
    从当前上下文中提取认证头信息，并合并用户提供的参数
    
    Args:
        username: 用户名
        auth_tenant_id: 租户ID
        current_company: 当前公司
        impersonation: 代理用户
        unique_no: 公司唯一编号
        trace_id: 追踪ID
        client: 客户端类型（小程序、web、app等）
        lang: 语言
        accept_language: 接受的语言
        
    Returns:
        AuthHeader: 合并后的认证头信息
    """
    # 获取当前上下文中的请求头
    context_headers = get_current_headers()
    
    # 如果不在上下文中，使用提供的参数
    if not context_headers:
        return AuthHeader(
            x_fiuai_user=username,
            x_fiuai_auth_tenant_id=auth_tenant_id,
            x_fiuai_current_company=current_company,
            x_fiuai_impersonation=impersonation,
            x_fiuai_unique_no=unique_no or current_company,
            x_fiuai_trace_id=trace_id or str(uuid.uuid4()),
            x_fiuai_client=client,
            x_fiuai_lang=lang,
            accept_language=accept_language
        )
    
    # 从上下文中提取信息，优先使用上下文中的值
    context_trace_id = context_headers.get("x-fiuai-trace-id", "")
    context_unique_no = context_headers.get("x-fiuai-unique-no", "")
    context_client = context_headers.get("x-fiuai-client", "")
    context_lang = context_headers.get("x-fiuai-lang", "")
    context_accept_language = context_headers.get("accept-language", "")
    
    return AuthHeader(
        x_fiuai_user=username,
        x_fiuai_auth_tenant_id=auth_tenant_id,
        x_fiuai_current_company=current_company,
        x_fiuai_impersonation=impersonation,
        x_fiuai_unique_no=context_unique_no or unique_no or current_company,
        x_fiuai_trace_id=context_trace_id or trace_id or str(uuid.uuid4()),
        x_fiuai_client=context_client or client,
        x_fiuai_lang=context_lang or lang,
        accept_language=context_accept_language or accept_language
    )

