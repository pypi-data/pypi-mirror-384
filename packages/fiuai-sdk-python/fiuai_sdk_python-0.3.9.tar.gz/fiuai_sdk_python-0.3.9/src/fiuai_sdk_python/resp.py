# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 10 Mo
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """API响应结构体"""
    http_success: bool = Field(description="HTTP是否成功")
    api_success: bool = Field(description="API业务是否成功")
    status_code: int = Field(description="HTTP状态码")
    data: Optional[Any] = Field(description="响应数据", default=None)
    error_code: Optional[str] = Field(description="精简的错误码", default=None)
    error: Optional[str] = Field(description="错误消息", default=None)
    
    def is_success(self) -> bool:
        """判断是否完全成功"""
        return self.http_success and self.api_success


def parse_response(response) -> ApiResponse:
    """
    解析HTTP响应，返回结构化的API响应
    
    Args:
        response: httpx响应对象
        
    Returns:
        ApiResponse: 结构化的API响应
    """
    # 检查响应是否存在
    if not response:
        return ApiResponse(
            http_success=False,
            api_success=False,
            status_code=504,
            error="Api no response",
            error_code="API_NO_RESPONSE",
        )
    
   
    # 解析JSON响应
    try:
         # 检查HTTP状态码
        http_success = 200 <= response.status_code < 300
    except Exception as e:
        return ApiResponse(
            http_success=False,
            api_success=False,
            status_code=response.status_code,
            error=f"Invalid JSON response: {e}",
            error_code="API_INVALID_JSON"
        )
    
    try:
        response_data = response.json()
    except Exception as e:
        return ApiResponse(
            http_success=True,
            api_success=False,
            status_code=response.status_code,
            error=f"Invalid JSON response: {e}",
            error_code="API_INVALID_JSON"
        )
    
    # 检查API业务是否成功
    api_success = _is_api_success(response_data)
    
    if api_success:
        # 成功响应，提取数据
        data = _extract_success_data(response_data)
        return ApiResponse(
            http_success=http_success,
            api_success=True,
            status_code=response.status_code,
            error=None,
            error_code=None,
            data=data
        )
    else:
        # 失败响应，提取错误信息
        error_msg, error_type = _extract_error_info(response_data)
        return ApiResponse(
            http_success=http_success,
            api_success=False,
            status_code=response.status_code,
            error=error_msg,
            error_code=error_type,
            data=None
        )


def _is_api_success(response_data: Dict[str, Any]) -> bool:
    """
    判断API业务是否成功
    
    Args:
        response_data: API响应数据
        
    Returns:
        bool: 是否成功
    """
    # 检查是否有错误
    errors = response_data.get("errors", None)
    if errors:
        return False
    
    # 检查是否有异常
    exc = response_data.get("exc", None)
    if exc:
        return False
    
    # 检查HTTP状态码
    http_status_code = response_data.get("http_status_code", None)
    if http_status_code is not None:
        return 200 <= http_status_code < 300
    
    # 默认认为有message或data字段就是成功
    return response_data.get("message", None) is not None or response_data.get("data", None) is not None


def _extract_success_data(response_data: Dict[str, Any]) -> Any:
    """
    从成功响应中提取数据
    
    Args:
        response_data: API响应数据
        
    Returns:
        Any: 提取的数据
    """
    return response_data.get("data", None)


def _extract_error_info(response_data: Dict[str, Any]) -> tuple[str, str]:
    """
    从响应中提取错误信息
    
    Args:
        response_data: API响应数据
        
    Returns:
        tuple[str, str]: (错误消息, 错误类型)
    """
    # 处理errors字段
    errors = response_data.get("errors", None)
    if errors and isinstance(errors, list):
        if errors:
            # 获取所有错误消息，用换行符分割
            error_messages = []
            error_codes = []
            for error in errors:
                if isinstance(error, dict):
                    error_msg = error.get("message", "Unknown error")
                    error_code = error.get("type", "UnknownError")
                    error_messages.append(error_msg)
                    error_codes.append(error_code)
            
            # 用换行符连接所有错误消息
            combined_error_msg = "\n".join(error_messages)
            # 使用第一个错误码作为主要错误码
            primary_error_code = error_codes[0] if error_codes else "UnknownError"
            return combined_error_msg, primary_error_code
    
    # 处理exc字段（V1 API格式）
    exc = response_data.get("exc", None)
    if exc:
        return str(exc), "API_EXCEPTION"
    
    # 处理message字段中的错误
    message = response_data.get("message", None)
    if message and isinstance(message, str):
        # 检查是否是错误消息
        if any(keyword in message.lower() for keyword in ["error", "failed", "invalid", "unauthorized"]):
            return message, "API_ERROR"
    
    return "Unknown error occurred", "UnknownError"


def is_auth_error(error_type: str) -> bool:
    """
    判断是否为认证相关错误
    
    Args:
        error_type: 错误类型
        
    Returns:
        bool: 是否为认证错误
    """
    auth_types = ["AuthenticationError", "PermissionError", "Unauthorized", "Forbidden"]
    return any(auth_type in error_type for auth_type in auth_types)


