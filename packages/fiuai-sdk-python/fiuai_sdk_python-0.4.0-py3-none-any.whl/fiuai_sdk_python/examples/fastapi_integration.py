# -- coding: utf-8 --
# Project: fiuai_sdk_python
# Created Date: 2025 01 09
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI

from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Callable
from ..context import RequestContext


class FiuaiContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 中间件，自动将请求头信息注入到上下文中
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，将请求头信息注入到上下文中
        
        Args:
            request: FastAPI 请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP 响应
        """
        # 创建请求上下文
        with RequestContext.from_fastapi_request(request):
            # 继续处理请求
            response = await call_next(request)
            return response


def setup_fiuai_context(app: FastAPI):
    """
    为 FastAPI 应用设置 Fiuai 上下文中间件
    
    Args:
        app: FastAPI 应用实例
        
    使用示例:
    from fastapi import FastAPI
    from fiuai_sdk_python.examples.fastapi_integration import setup_fiuai_context
    from fiuai_sdk_python import create_contextual_client
    
    app = FastAPI()
    setup_fiuai_context(app)
    
    @app.get("/api/test")
    async def test():
        # 不需要任何装饰器，直接使用即可
        client = create_contextual_client("user", "tenant", "company")
        return client.get_user_profile_info()
    """
    app.add_middleware(FiuaiContextMiddleware)