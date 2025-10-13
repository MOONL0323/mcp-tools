"""
数据库连接和会话管理
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
from sqlalchemy import text
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# 数据库引擎
engine: Optional[object] = None
replica_engine: Optional[object] = None
async_session: Optional[async_sessionmaker] = None

# 基础模型类
Base = declarative_base()


async def init_db() -> None:
    """初始化数据库连接"""
    global engine, replica_engine, async_session
    
    try:
        # 主数据库引擎
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # 只读副本引擎 (如果配置了)
        # 简化版本暂时不使用副本数据库
        replica_engine = None
        
        # 创建会话工厂
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("数据库连接初始化成功",
                   database_url=settings.DATABASE_URL,
                   has_replica=replica_engine is not None)
        
    except Exception as e:
        logger.error("数据库连接初始化失败", error=str(e))
        raise


async def close_db() -> None:
    """关闭数据库连接"""
    global engine, replica_engine
    
    try:
        if engine:
            await engine.dispose()
            logger.info("主数据库连接已关闭")
        
        if replica_engine:
            await replica_engine.dispose()
            logger.info("副本数据库连接已关闭")
            
    except Exception as e:
        logger.error("关闭数据库连接时出错", error=str(e))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话 - 主数据库 (读写)"""
    if async_session is None:
        raise RuntimeError("数据库未初始化")
    
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("数据库会话异常", error=str(e))
            raise
        finally:
            await session.close()


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """获取只读数据库会话 - 副本数据库 (只读)"""
    global replica_engine
    
    # 如果没有配置副本，使用主数据库
    if replica_engine is None:
        async for session in get_db():
            yield session
        return
    
    # 使用副本数据库的会话
    replica_session = async_sessionmaker(
        replica_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with replica_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error("只读数据库会话异常", error=str(e))
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """检查数据库健康状态"""
    try:
        async for session in get_db():
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error("数据库健康检查失败", error=str(e))
        return False


class DatabaseManager:
    """数据库管理器 - 单例模式"""
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def execute_transaction(self, operations: list, use_replica: bool = False):
        """执行事务操作"""
        get_session = get_read_db if use_replica else get_db
        
        async for session in get_session():
            try:
                async with session.begin():
                    results = []
                    for operation in operations:
                        result = await operation(session)
                        results.append(result)
                    return results
            except Exception as e:
                logger.error("事务执行失败", error=str(e))
                raise
    
    async def execute_raw_sql(self, sql: str, params: dict = None, use_replica: bool = False):
        """执行原生SQL"""
        get_session = get_read_db if use_replica else get_db
        
        async for session in get_session():
            try:
                result = await session.execute(text(sql), params or {})
                if sql.strip().upper().startswith('SELECT'):
                    return result.fetchall()
                else:
                    await session.commit()
                    return result.rowcount
            except Exception as e:
                logger.error("原生SQL执行失败", sql=sql, error=str(e))
                raise


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def create_tables():
    """创建数据库表"""
    global engine
    
    if not engine:
        await init_db()
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error("数据库表创建失败", error=str(e))
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    if not async_session:
        await init_db()
    
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("数据库会话异常", error=str(e))
            raise
        finally:
            await session.close()