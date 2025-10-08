"""
Redis缓存服务
提供高性能的缓存和会话管理
"""
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from loguru import logger

from database.connection import db_manager
from database.config import db_settings


class CacheService:
    """Redis缓存服务"""
    
    def __init__(self):
        self.default_ttl = db_settings.redis_cache_ttl
        logger.info("Redis缓存服务初始化完成")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            redis_client = await db_manager.get_redis_client()
            value = await redis_client.get(key)
            await redis_client.close()
            
            if value:
                return pickle.loads(value)
            return None
            
        except Exception as e:
            logger.warning(f"获取缓存失败 {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            redis_client = await db_manager.get_redis_client()
            ttl = ttl or self.default_ttl
            
            serialized_value = pickle.dumps(value)
            await redis_client.setex(key, ttl, serialized_value)
            await redis_client.close()
            
            return True
            
        except Exception as e:
            logger.warning(f"设置缓存失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            redis_client = await db_manager.get_redis_client()
            result = await redis_client.delete(key)
            await redis_client.close()
            
            return result > 0
            
        except Exception as e:
            logger.warning(f"删除缓存失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            redis_client = await db_manager.get_redis_client()
            result = await redis_client.exists(key)
            await redis_client.close()
            
            return result > 0
            
        except Exception as e:
            logger.warning(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清理匹配模式的缓存"""
        try:
            redis_client = await db_manager.get_redis_client()
            keys = await redis_client.keys(pattern)
            
            if keys:
                deleted = await redis_client.delete(*keys)
                await redis_client.close()
                return deleted
            
            await redis_client.close()
            return 0
            
        except Exception as e:
            logger.warning(f"清理缓存模式失败 {pattern}: {e}")
            return 0
    
    def _make_search_key(self, query: str, search_type: str, params: Dict[str, Any]) -> str:
        """生成搜索缓存键"""
        import hashlib
        
        # 创建唯一的缓存键
        key_data = {
            'query': query,
            'type': search_type,
            'params': sorted(params.items())
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"search:{search_type}:{key_hash}"
    
    async def get_search_cache(
        self, 
        query: str, 
        search_type: str, 
        params: Dict[str, Any]
    ) -> Optional[List[Any]]:
        """获取搜索结果缓存"""
        cache_key = self._make_search_key(query, search_type, params)
        return await self.get(cache_key)
    
    async def set_search_cache(
        self, 
        query: str, 
        search_type: str, 
        params: Dict[str, Any],
        results: List[Any],
        ttl: Optional[int] = None
    ) -> bool:
        """设置搜索结果缓存"""
        cache_key = self._make_search_key(query, search_type, params)
        return await self.set(cache_key, results, ttl)
    
    async def clear_search_cache(self) -> int:
        """清理所有搜索缓存"""
        return await self.clear_pattern("search:*")


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        self.session_ttl = 24 * 3600  # 24小时
        logger.info("会话管理服务初始化完成")
    
    async def create_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """创建会话"""
        try:
            redis_client = await db_manager.get_redis_client()
            session_key = f"session:{session_id}"
            
            session_data = {
                'user_data': user_data,
                'created_at': str(datetime.utcnow()),
                'last_accessed': str(datetime.utcnow())
            }
            
            await redis_client.setex(
                session_key, 
                self.session_ttl, 
                json.dumps(session_data)
            )
            await redis_client.close()
            
            return True
            
        except Exception as e:
            logger.error(f"创建会话失败 {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        try:
            redis_client = await db_manager.get_redis_client()
            session_key = f"session:{session_id}"
            
            session_data = await redis_client.get(session_key)
            if session_data:
                # 更新最后访问时间
                data = json.loads(session_data)
                data['last_accessed'] = str(datetime.utcnow())
                
                await redis_client.setex(
                    session_key,
                    self.session_ttl,
                    json.dumps(data)
                )
                await redis_client.close()
                
                return data
            
            await redis_client.close()
            return None
            
        except Exception as e:
            logger.warning(f"获取会话失败 {session_id}: {e}")
            return None
    
    async def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """更新会话数据"""
        try:
            redis_client = await db_manager.get_redis_client()
            session_key = f"session:{session_id}"
            
            # 获取现有会话数据
            existing_data = await redis_client.get(session_key)
            if existing_data:
                data = json.loads(existing_data)
                data['user_data'].update(user_data)
                data['last_accessed'] = str(datetime.utcnow())
                
                await redis_client.setex(
                    session_key,
                    self.session_ttl,
                    json.dumps(data)
                )
                await redis_client.close()
                
                return True
            
            await redis_client.close()
            return False
            
        except Exception as e:
            logger.error(f"更新会话失败 {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            redis_client = await db_manager.get_redis_client()
            session_key = f"session:{session_id}"
            
            result = await redis_client.delete(session_key)
            await redis_client.close()
            
            return result > 0
            
        except Exception as e:
            logger.error(f"删除会话失败 {session_id}: {e}")
            return False


class MetricsService:
    """指标统计服务"""
    
    def __init__(self):
        logger.info("指标统计服务初始化完成")
    
    async def increment_counter(self, metric_name: str, value: int = 1) -> bool:
        """增加计数器"""
        try:
            redis_client = await db_manager.get_redis_client()
            key = f"metrics:counter:{metric_name}"
            
            await redis_client.incrby(key, value)
            await redis_client.close()
            
            return True
            
        except Exception as e:
            logger.warning(f"增加计数器失败 {metric_name}: {e}")
            return False
    
    async def get_counter(self, metric_name: str) -> int:
        """获取计数器值"""
        try:
            redis_client = await db_manager.get_redis_client()
            key = f"metrics:counter:{metric_name}"
            
            value = await redis_client.get(key)
            await redis_client.close()
            
            return int(value) if value else 0
            
        except Exception as e:
            logger.warning(f"获取计数器失败 {metric_name}: {e}")
            return 0
    
    async def record_timing(self, metric_name: str, duration_ms: int) -> bool:
        """记录时间指标"""
        try:
            redis_client = await db_manager.get_redis_client()
            key = f"metrics:timing:{metric_name}"
            
            # 使用Redis列表存储最近的时间记录
            await redis_client.lpush(key, duration_ms)
            await redis_client.ltrim(key, 0, 999)  # 只保留最近1000条记录
            await redis_client.close()
            
            return True
            
        except Exception as e:
            logger.warning(f"记录时间指标失败 {metric_name}: {e}")
            return False
    
    async def get_timing_stats(self, metric_name: str) -> Dict[str, float]:
        """获取时间指标统计"""
        try:
            redis_client = await db_manager.get_redis_client()
            key = f"metrics:timing:{metric_name}"
            
            values = await redis_client.lrange(key, 0, -1)
            await redis_client.close()
            
            if not values:
                return {}
            
            timings = [float(v) for v in values]
            
            return {
                'count': len(timings),
                'avg': sum(timings) / len(timings),
                'min': min(timings),
                'max': max(timings),
                'p95': sorted(timings)[int(len(timings) * 0.95)] if len(timings) > 0 else 0
            }
            
        except Exception as e:
            logger.warning(f"获取时间指标统计失败 {metric_name}: {e}")
            return {}


# 全局服务实例
cache_service = CacheService()
session_service = SessionService()
metrics_service = MetricsService()

from datetime import datetime