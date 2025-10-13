"""
API v1 路由汇总
"""

from fastapi import APIRouter
from ..documents_core import router as documents_core_router
from ..mcp_core import router as mcp_core_router

api_router = APIRouter()

# 注册核心路由 - 专注AI代码生成系统的核心功能
api_router.include_router(documents_core_router, prefix="/documents", tags=["文档管理-核心"])
api_router.include_router(mcp_core_router, prefix="/mcp", tags=["MCP-核心"])