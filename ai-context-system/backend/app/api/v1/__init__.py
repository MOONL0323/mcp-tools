"""
API v1 路由汇总
"""

from fastapi import APIRouter
from ..documents_core import router as documents_core_router
from ..mcp_core import router as mcp_core_router
from ..stats import router as stats_router
from ..auth_simple import router as auth_router
from ..classifications import router as classifications_router
from ..search import router as search_router
from ..entities import router as entities_router
from ..graph import router as graph_router

api_router = APIRouter()

# 注册核心路由 - 专注AI代码生成系统的核心功能  
# 认证路由
api_router.include_router(auth_router, tags=["认证"])
# 分类管理
api_router.include_router(classifications_router, tags=["分类管理"])
# 文档管理
api_router.include_router(documents_core_router, prefix="/documents", tags=["文档管理-核心"])
# 语义搜索
api_router.include_router(search_router, tags=["语义搜索"])
# 实体提取
api_router.include_router(entities_router, tags=["实体提取"])
# 知识图谱
api_router.include_router(graph_router, tags=["知识图谱"])
# MCP工具
api_router.include_router(mcp_core_router, prefix="/mcp", tags=["MCP-核心"])
# 统计信息
api_router.include_router(stats_router, prefix="/stats", tags=["统计信息"])