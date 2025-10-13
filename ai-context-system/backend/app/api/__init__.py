"""
API 路由汇总
"""

from fastapi import APIRouter
from .v1 import api_router as v1_router

api_router = APIRouter()

# 注册版本路由
api_router.include_router(v1_router, prefix="/v1")