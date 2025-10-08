"""
数据库连接管理器
统一管理所有数据库连接
"""
import asyncio
from typing import Optional, Any
from contextlib import asynccontextmanager
import asyncpg
from neo4j import GraphDatabase
import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from .config import db_settings

# SQLAlchemy基类
Base = declarative_base()


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self._postgres_engine = None
        self._postgres_session_factory = None
        self._neo4j_driver = None
        self._redis_pool = None
        self._elasticsearch_client = None
        self._initialized = False
    
    async def initialize(self):
        """初始化所有数据库连接"""
        if self._initialized:
            return
            
        logger.info("正在初始化数据库连接...")
        
        try:
            # 初始化PostgreSQL
            await self._init_postgres()
            
            # 初始化Neo4j
            await self._init_neo4j()
            
            # 初始化Redis
            await self._init_redis()
            
            # 初始化Elasticsearch (可选)
            await self._init_elasticsearch()
            
            self._initialized = True
            logger.info("所有数据库连接初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def _init_postgres(self):
        """初始化PostgreSQL连接"""
        try:
            self._postgres_engine = create_async_engine(
                db_settings.postgres_url,
                echo=False,  # 生产环境设置为False
                pool_size=db_settings.postgres_max_connections,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            self._postgres_session_factory = async_sessionmaker(
                self._postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 测试连接
            async with self._postgres_engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            logger.info("PostgreSQL连接初始化成功")
            
        except Exception as e:
            logger.error(f"PostgreSQL连接初始化失败: {e}")
            raise
    
    async def _init_neo4j(self):
        """初始化Neo4j连接"""
        try:
            self._neo4j_driver = GraphDatabase.driver(
                db_settings.neo4j_uri,
                auth=(db_settings.neo4j_user, db_settings.neo4j_password),
                max_connection_pool_size=db_settings.neo4j_max_connection_pool_size,
                connection_timeout=db_settings.neo4j_connection_timeout
            )
            
            # 测试连接
            self._neo4j_driver.verify_connectivity()
            
            logger.info("Neo4j连接初始化成功")
            
        except Exception as e:
            logger.error(f"Neo4j连接初始化失败: {e}")
            raise
    
    async def _init_redis(self):
        """初始化Redis连接"""
        try:
            self._redis_pool = redis.ConnectionPool.from_url(
                db_settings.redis_url,
                max_connections=db_settings.redis_max_connections,
                socket_timeout=db_settings.redis_socket_timeout,
                retry_on_timeout=True
            )
            
            # 测试连接
            redis_client = redis.Redis(connection_pool=self._redis_pool)
            await redis_client.ping()
            await redis_client.close()
            
            logger.info("Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"Redis连接初始化失败: {e}")
            raise
    
    async def _init_elasticsearch(self):
        """初始化Elasticsearch连接 (可选)"""
        try:
            self._elasticsearch_client = AsyncElasticsearch(
                [db_settings.elasticsearch_url],
                timeout=db_settings.elasticsearch_timeout,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # 测试连接
            info = await self._elasticsearch_client.info()
            logger.info(f"Elasticsearch连接成功: {info['version']['number']}")
            
        except Exception as e:
            logger.warning(f"Elasticsearch连接失败 (可选组件): {e}")
            self._elasticsearch_client = None
    
    @asynccontextmanager
    async def get_postgres_session(self):
        """获取PostgreSQL会话"""
        if not self._postgres_session_factory:
            raise RuntimeError("PostgreSQL未初始化")
        
        async with self._postgres_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    def get_neo4j_session(self):
        """获取Neo4j会话"""
        if not self._neo4j_driver:
            raise RuntimeError("Neo4j未初始化")
        return self._neo4j_driver.session()
    
    async def get_redis_client(self):
        """获取Redis客户端"""
        if not self._redis_pool:
            raise RuntimeError("Redis未初始化")
        return redis.Redis(connection_pool=self._redis_pool)
    
    def get_elasticsearch_client(self):
        """获取Elasticsearch客户端"""
        if not self._elasticsearch_client:
            raise RuntimeError("Elasticsearch未初始化或连接失败")
        return self._elasticsearch_client
    
    async def close(self):
        """关闭所有数据库连接"""
        logger.info("正在关闭数据库连接...")
        
        if self._postgres_engine:
            await self._postgres_engine.dispose()
            
        if self._neo4j_driver:
            self._neo4j_driver.close()
            
        if self._redis_pool:
            await self._redis_pool.disconnect()
            
        if self._elasticsearch_client:
            await self._elasticsearch_client.close()
        
        self._initialized = False
        logger.info("所有数据库连接已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def init_databases():
    """初始化数据库连接"""
    await db_manager.initialize()


async def close_databases():
    """关闭数据库连接"""
    await db_manager.close()