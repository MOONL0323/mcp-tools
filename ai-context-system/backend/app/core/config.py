"""
应用配置管理
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    DEBUG: bool = Field(default=True, description="调试模式")
    ENVIRONMENT: str = Field(default="development", description="运行环境")
    SECRET_KEY: str = Field(default="dev-secret-key", description="应用密钥")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="服务器地址")
    PORT: int = Field(default=8000, description="服务器端口")
    WORKERS: int = Field(default=1, description="工作进程数")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机列表")
    
    # 数据库配置
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./ai_context.db", description="数据库连接URL")
    DATABASE_POOL_SIZE: int = Field(default=10, description="数据库连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="数据库连接池溢出")
    
    # Redis配置
    REDIS_ENABLED: bool = Field(default=False, description="是否启用Redis")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis连接池大小")
    
    # JWT认证配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间(分钟)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="刷新令牌过期时间(天)")
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    
    # 文件上传配置
    UPLOAD_DIR: str = Field(default="./uploads", description="文件上传目录")
    MAX_FILE_SIZE: int = Field(default=104857600, description="最大文件大小(字节)")  # 100MB
    ALLOWED_MIME_TYPES: List[str] = Field(
        default=[
            "text/plain",
            "text/markdown", 
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ],
        description="允许的文件类型"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件路径")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略额外字段


# 全局配置实例
_settings = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings