"""
数据库配置管理
支持PostgreSQL、Neo4j、Redis和Elasticsearch
"""
import os
from typing import Optional
from pydantic import BaseSettings
from loguru import logger


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    
    # PostgreSQL配置
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "knowledge_graph"
    postgres_user: str = "kg_user"
    postgres_password: str = "your_password"
    postgres_max_connections: int = 20
    postgres_min_connections: int = 5
    
    # Neo4j配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "your_neo4j_password"
    neo4j_max_connection_pool_size: int = 50
    neo4j_connection_timeout: int = 30
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10
    redis_cache_ttl: int = 3600
    redis_socket_timeout: int = 30
    
    # Elasticsearch配置 (可选)
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_prefix: str = "kg_"
    elasticsearch_timeout: int = 30
    
    # 向量配置
    vector_dimension: int = 768
    vector_index_type: str = "hnsw"  # hnsw 或 ivfflat
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def postgres_url(self) -> str:
        """PostgreSQL连接URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def postgres_sync_url(self) -> str:
        """PostgreSQL同步连接URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


# 全局配置实例
db_settings = DatabaseSettings()

logger.info(f"数据库配置加载完成: PostgreSQL={db_settings.postgres_host}:{db_settings.postgres_port}")