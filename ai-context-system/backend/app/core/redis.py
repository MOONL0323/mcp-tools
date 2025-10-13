"""
Redis连接和缓存管理
"""

from typing import Any, Optional, Union
import json
import pickle
from datetime import timedelta
import redis.asyncio as redis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# 全局Redis连接池
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """初始化Redis连接"""
    global redis_pool, redis_client
    
    if not settings.REDIS_ENABLED:
        logger.info("Redis已禁用，跳过初始化")
        return
    
    try:
        # 创建连接池
        redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=False,  # 关闭自动解码，手动处理
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        
        # 创建Redis客户端
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # 测试连接
        await redis_client.ping()
        
        logger.info("Redis连接初始化成功", redis_url=settings.REDIS_URL)
        
    except Exception as e:
        logger.error("Redis连接初始化失败", error=str(e))
        raise


async def close_redis() -> None:
    """关闭Redis连接"""
    global redis_pool, redis_client
    
    try:
        if redis_client:
            await redis_client.close()
        if redis_pool:
            await redis_pool.disconnect()
        
        logger.info("Redis连接已关闭")
        
    except Exception as e:
        logger.error("关闭Redis连接时出错", error=str(e))


async def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    if not settings.REDIS_ENABLED:
        raise RuntimeError("Redis已禁用")
    if redis_client is None:
        raise RuntimeError("Redis未初始化")
    return redis_client


async def check_redis_health() -> bool:
    """检查Redis健康状态"""
    try:
        client = await get_redis()
        response = await client.ping()
        return response is True
    except Exception as e:
        logger.error("Redis健康检查失败", error=str(e))
        return False


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, prefix: str = "ai_context"):
        self.prefix = prefix
    
    def _make_key(self, key: str) -> str:
        """生成缓存键"""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        try:
            client = await get_redis()
            value = await client.get(self._make_key(key))
            
            if value is None:
                return default
            
            # 尝试JSON解码
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 如果JSON解码失败，尝试pickle
                try:
                    return pickle.loads(value)
                except pickle.PickleError:
                    # 如果都失败，返回原始字符串
                    return value.decode('utf-8', errors='ignore')
                    
        except Exception as e:
            logger.error("获取缓存失败", key=key, error=str(e))
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None,
        serialize_method: str = "json"
    ) -> bool:
        """设置缓存值"""
        try:
            client = await get_redis()
            
            # 序列化值
            if serialize_method == "json":
                try:
                    serialized_value = json.dumps(value, ensure_ascii=False)
                except (TypeError, ValueError):
                    # JSON序列化失败，使用pickle
                    serialized_value = pickle.dumps(value)
            elif serialize_method == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # 设置TTL
            if ttl is None:
                ttl = settings.CACHE_TTL
            elif isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            await client.setex(self._make_key(key), ttl, serialized_value)
            return True
            
        except Exception as e:
            logger.error("设置缓存失败", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            client = await get_redis()
            result = await client.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error("删除缓存失败", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            client = await get_redis()
            result = await client.exists(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error("检查缓存存在失败", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """设置缓存过期时间"""
        try:
            client = await get_redis()
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            result = await client.expire(self._make_key(key), ttl)
            return result
        except Exception as e:
            logger.error("设置缓存过期时间失败", key=key, error=str(e))
            return False
    
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """批量获取缓存"""
        try:
            client = await get_redis()
            cache_keys = [self._make_key(key) for key in keys]
            values = await client.mget(cache_keys)
            
            result = {}
            for i, key in enumerate(keys):
                value = values[i]
                if value is not None:
                    try:
                        result[key] = json.loads(value.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        try:
                            result[key] = pickle.loads(value)
                        except pickle.PickleError:
                            result[key] = value.decode('utf-8', errors='ignore')
                else:
                    result[key] = None
            
            return result
            
        except Exception as e:
            logger.error("批量获取缓存失败", keys=keys, error=str(e))
            return {key: None for key in keys}
    
    async def set_many(
        self, 
        mapping: dict[str, Any], 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """批量设置缓存"""
        try:
            client = await get_redis()
            
            # 序列化所有值
            cache_mapping = {}
            for key, value in mapping.items():
                try:
                    cache_mapping[self._make_key(key)] = json.dumps(value, ensure_ascii=False)
                except (TypeError, ValueError):
                    cache_mapping[self._make_key(key)] = pickle.dumps(value)
            
            # 批量设置
            await client.mset(cache_mapping)
            
            # 设置过期时间
            if ttl is not None:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                
                pipe = client.pipeline()
                for cache_key in cache_mapping.keys():
                    pipe.expire(cache_key, ttl)
                await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error("批量设置缓存失败", keys=list(mapping.keys()), error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            client = await get_redis()
            pattern_key = self._make_key(pattern)
            
            # 使用SCAN避免阻塞
            deleted_count = 0
            async for key in client.scan_iter(match=pattern_key):
                await client.delete(key)
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error("清除模式缓存失败", pattern=pattern, error=str(e))
            return 0


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.cache = CacheManager("session")
    
    async def create_session(self, user_id: str, session_data: dict, ttl: int = 3600) -> str:
        """创建会话"""
        import uuid
        session_id = str(uuid.uuid4())
        session_key = f"user:{user_id}:{session_id}"
        
        await self.cache.set(session_key, session_data, ttl)
        return session_id
    
    async def get_session(self, user_id: str, session_id: str) -> Optional[dict]:
        """获取会话"""
        session_key = f"user:{user_id}:{session_id}"
        return await self.cache.get(session_key)
    
    async def update_session(self, user_id: str, session_id: str, session_data: dict) -> bool:
        """更新会话"""
        session_key = f"user:{user_id}:{session_id}"
        return await self.cache.set(session_key, session_data)
    
    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """删除会话"""
        session_key = f"user:{user_id}:{session_id}"
        return await self.cache.delete(session_key)
    
    async def clear_user_sessions(self, user_id: str) -> int:
        """清除用户所有会话"""
        pattern = f"user:{user_id}:*"
        return await self.cache.clear_pattern(pattern)


# 全局缓存管理器实例
cache = CacheManager()
session_manager = SessionManager()