"""
数据库快捷导入模块
简化导入路径，统一数据库访问
"""

from app.core.database import get_db, init_db, create_tables, Base

__all__ = ["get_db", "init_db", "create_tables", "Base"]
