# -- coding: utf-8 --
# Project: auth
# Created Date: 2025-01-09
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

"""
认证功能测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .header import parse_auth_headers, extract_auth_from_request
from .helper import (
    get_auth_data,
    get_current_user_id,
    get_current_tenant_id,
    get_current_company,
    get_company_unique_no,
    get_impersonation,
    is_impersonating
)
from .type import AuthData
from unittest.mock import Mock


def test_parse_auth_headers_success():
    """测试成功解析认证头信息"""
    headers = {
        "x-fiuai-user": "user123",
        "x-fiuai-auth-tenant-id": "tenant456",
        "x-fiuai-current-company": "company1,company2",
        "x-fiuai-impersonation": "imp_tenant789"
    }
    
    auth_data = parse_auth_headers(headers)
    
    assert auth_data is not None
    assert auth_data.user_id == "user123"
    assert auth_data.auth_tenant_id == "tenant456"
    assert auth_data.current_company == "company1"
    assert auth_data.company_unique_no == "company1"
    assert auth_data.impersonation == "imp_tenant789"


def test_parse_auth_headers_missing_required():
    """测试缺少必需头信息的情况"""
    headers = {
        "x-fiuai-user": "user123",
        # 缺少 x-fiuai-auth-tenant-id
        "x-fiuai-current-company": "company1",
    }
    
    try:
        auth_data = parse_auth_headers(headers)
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "Missing required header: x-fiuai-auth-tenant-id" in str(e)


def test_parse_auth_headers_empty_company():
    """测试空公司列表的情况"""
    headers = {
        "x-fiuai-user": "user123",
        "x-fiuai-auth-tenant-id": "tenant456",
        "x-fiuai-current-company": "",  # 空字符串
        "x-fiuai-impersonation": ""
    }
    
    try:
        auth_data = parse_auth_headers(headers)
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "Missing required header: x-fiuai-current-company" in str(e)


def test_parse_auth_headers_multiple_companies():
    """测试多个公司的情况"""
    headers = {
        "x-fiuai-user": "user123",
        "x-fiuai-auth-tenant-id": "tenant456",
        "x-fiuai-current-company": "company1,company2,company3",
        "x-fiuai-impersonation": ""
    }
    
    auth_data = parse_auth_headers(headers)
    
    assert auth_data is not None
    assert auth_data.current_company == "company1"  # 取第一个
    assert auth_data.company_unique_no == "company1"


def test_parse_auth_headers_with_spaces():
    """测试包含空格的公司列表"""
    headers = {
        "x-fiuai-user": "user123",
        "x-fiuai-auth-tenant-id": "tenant456",
        "x-fiuai-current-company": " company1 , company2 , company3 ",
        "x-fiuai-impersonation": ""
    }
    
    auth_data = parse_auth_headers(headers)
    
    assert auth_data is not None
    assert auth_data.current_company == "company1"  # 取第一个，已去除空格
    assert auth_data.company_unique_no == "company1"


def test_extract_auth_from_request_fastapi():
    """测试从 FastAPI Request 对象提取认证信息"""
    # 模拟 FastAPI Request 对象
    from fastapi import Request
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        "x-fiuai-user": "user123",
        "x-fiuai-auth-tenant-id": "tenant456",
        "x-fiuai-current-company": "company1,company2",
        "x-fiuai-impersonation": "imp_tenant789"
    }
    
    auth_data = extract_auth_from_request(mock_request, engine="fastapi")
    
    assert auth_data is not None
    assert auth_data.user_id == "user123"
    assert auth_data.auth_tenant_id == "tenant456"
    assert auth_data.current_company == "company1"
    assert auth_data.company_unique_no == "company1"
    assert auth_data.impersonation == "imp_tenant789"


def test_extract_auth_from_request_dict():
    """测试从原生字典提取认证信息"""
    headers_dict = {
        "x-fiuai-user": "user123",
        "x-fiuai-auth-tenant-id": "tenant456",
        "x-fiuai-current-company": "company1,company2",
        "x-fiuai-impersonation": "imp_tenant789"
    }
    
    auth_data = extract_auth_from_request(headers_dict, engine="dict")
    
    assert auth_data is not None
    assert auth_data.user_id == "user123"
    assert auth_data.auth_tenant_id == "tenant456"
    assert auth_data.current_company == "company1"
    assert auth_data.company_unique_no == "company1"
    assert auth_data.impersonation == "imp_tenant789"


def test_extract_auth_from_request_wrong_type():
    """测试类型错误的情况"""
    # 测试 FastAPI 引擎但传入字典
    try:
        extract_auth_from_request({"test": "value"}, engine="fastapi")
        assert False, "应该抛出 TypeError"
    except TypeError as e:
        assert "request must be a FastAPI Request object" in str(e)
    
    # 测试 dict 引擎但传入 Request 对象
    from fastapi import Request
    mock_request = Mock(spec=Request)
    try:
        extract_auth_from_request(mock_request, engine="dict")
        assert False, "应该抛出 TypeError"
    except TypeError as e:
        assert "request must be a dict" in str(e)


def test_helper_functions_fastapi():
    """测试 FastAPI 模式下的辅助函数"""
    # 模拟 FastAPI Request 对象，包含认证数据
    from fastapi import Request
    mock_request = Mock(spec=Request)
    auth_data = AuthData(
        user_id="user123",
        auth_tenant_id="tenant456",
        current_company="company1",
        impersonation="imp_tenant789",
        company_unique_no="company1"
    )
    mock_request.state.auth_data = auth_data
    
    # 测试各种辅助函数
    assert get_current_user_id(mock_request, engine="fastapi") == "user123"
    assert get_current_tenant_id(mock_request, engine="fastapi") == "tenant456"
    assert get_current_company(mock_request, engine="fastapi") == "company1"
    assert get_company_unique_no(mock_request, engine="fastapi") == "company1"
    assert get_impersonation(mock_request, engine="fastapi") == "imp_tenant789"
    assert is_impersonating(mock_request, engine="fastapi") == True


def test_helper_functions_dict():
    """测试 dict 模式下的辅助函数"""
    # 模拟包含认证数据的字典
    auth_data = AuthData(
        user_id="user123",
        auth_tenant_id="tenant456",
        current_company="company1",
        impersonation="imp_tenant789",
        company_unique_no="company1"
    )
    request_dict = {"auth_data": auth_data}
    
    # 测试各种辅助函数
    assert get_current_user_id(request_dict, engine="dict") == "user123"
    assert get_current_tenant_id(request_dict, engine="dict") == "tenant456"
    assert get_current_company(request_dict, engine="dict") == "company1"
    assert get_company_unique_no(request_dict, engine="dict") == "company1"
    assert get_impersonation(request_dict, engine="dict") == "imp_tenant789"
    assert is_impersonating(request_dict, engine="dict") == True


def test_helper_functions_missing_auth_data():
    """测试缺少认证数据的情况"""
    # 测试 FastAPI 模式
    from fastapi import Request
    mock_request = Mock(spec=Request)
    mock_request.state.auth_data = None
    
    try:
        get_auth_data(mock_request, engine="fastapi")
        assert False, "应该抛出 HTTPException"
    except Exception as e:
        assert "Authentication data not found" in str(e)
    
    # 测试 dict 模式
    request_dict = {}
    try:
        get_auth_data(request_dict, engine="dict")
        assert False, "应该抛出 ValueError"
    except ValueError as e:
        assert "Authentication data not found" in str(e)


def test_is_impersonating_false():
    """测试非代表模式的情况"""
    auth_data = AuthData(
        user_id="user123",
        auth_tenant_id="tenant456",
        current_company="company1",
        impersonation="",  # 空字符串
        company_unique_no="company1"
    )
    request_dict = {"auth_data": auth_data}
    
    assert is_impersonating(request_dict, engine="dict") == False
    
    # 测试 impersonation 等于 auth_tenant_id 的情况
    auth_data.impersonation = "tenant456"
    assert is_impersonating(request_dict, engine="dict") == False


if __name__ == "__main__":
    # 运行原有测试
    test_parse_auth_headers_success()
    test_parse_auth_headers_missing_required()
    test_parse_auth_headers_empty_company()
    test_parse_auth_headers_multiple_companies()
    test_parse_auth_headers_with_spaces()
    
    # 运行新增的测试
    test_extract_auth_from_request_fastapi()
    test_extract_auth_from_request_dict()
    test_extract_auth_from_request_wrong_type()
    test_helper_functions_fastapi()
    test_helper_functions_dict()
    test_helper_functions_missing_auth_data()
    test_is_impersonating_false()
    
    print("所有测试通过！")
