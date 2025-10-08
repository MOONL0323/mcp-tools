#!/usr/bin/env python3
"""
数据库验证脚本
验证所有数据库连接和功能
"""
import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from sqlalchemy import text
from database.connection import db_manager
from services.cache import cache_service, session_service, metrics_service


async def test_postgresql():
    """测试PostgreSQL功能"""
    logger.info("🧪 测试PostgreSQL功能...")
    
    try:
        async with db_manager.get_postgres_session() as session:
            # 测试基本查询
            result = await session.execute(text("SELECT 1 as test"))
            assert result.scalar() == 1
            logger.info("✅ PostgreSQL基本查询测试通过")
            
            # 测试pgvector
            await session.execute(text("SELECT '[1,2,3]'::vector"))
            logger.info("✅ pgvector扩展测试通过")
            
            # 测试表存在性
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'document_vectors'
            """))
            if result.scalar():
                logger.info("✅ document_vectors表存在")
            else:
                logger.warning("⚠️ document_vectors表不存在")
            
            # 测试向量相似度计算
            await session.execute(text("""
                SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector as distance
            """))
            logger.info("✅ 向量距离计算测试通过")
            
    except Exception as e:
        logger.error(f"❌ PostgreSQL测试失败: {e}")
        raise


async def test_neo4j():
    """测试Neo4j功能"""
    logger.info("🧪 测试Neo4j功能...")
    
    try:
        with db_manager.get_neo4j_session() as session:
            # 测试基本查询
            result = session.run("RETURN 1 as test")
            record = result.single()
            assert record["test"] == 1
            logger.info("✅ Neo4j基本查询测试通过")
            
            # 测试创建和删除节点
            session.run("CREATE (t:Test {name: 'test_node', created: $created})", 
                       created=datetime.now().isoformat())
            logger.info("✅ Neo4j节点创建测试通过")
            
            # 测试查询节点
            result = session.run("MATCH (t:Test {name: 'test_node'}) RETURN t")
            record = result.single()
            assert record is not None
            logger.info("✅ Neo4j节点查询测试通过")
            
            # 测试关系创建
            session.run("""
                MATCH (t:Test {name: 'test_node'})
                CREATE (t)-[:TESTED_BY]->(:TestResult {status: 'success'})
            """)
            logger.info("✅ Neo4j关系创建测试通过")
            
            # 清理测试数据
            session.run("MATCH (t:Test {name: 'test_node'}) DETACH DELETE t")
            session.run("MATCH (tr:TestResult {status: 'success'}) DELETE tr")
            logger.info("✅ Neo4j测试数据清理完成")
            
    except Exception as e:
        logger.error(f"❌ Neo4j测试失败: {e}")
        raise


async def test_redis():
    """测试Redis功能"""
    logger.info("🧪 测试Redis功能...")
    
    try:
        redis_client = await db_manager.get_redis_client()
        
        # 测试基本操作
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        assert value.decode() == "test_value"
        logger.info("✅ Redis基本操作测试通过")
        
        # 测试TTL
        await redis_client.setex("ttl_test", 1, "will_expire")
        exists_before = await redis_client.exists("ttl_test")
        await asyncio.sleep(1.1)
        exists_after = await redis_client.exists("ttl_test")
        assert exists_before and not exists_after
        logger.info("✅ Redis TTL测试通过")
        
        # 测试列表操作
        await redis_client.lpush("test_list", "item1", "item2", "item3")
        length = await redis_client.llen("test_list")
        assert length == 3
        logger.info("✅ Redis列表操作测试通过")
        
        # 清理测试数据
        await redis_client.delete("test_key", "test_list")
        
        await redis_client.close()
        logger.info("✅ Redis连接正常关闭")
        
    except Exception as e:
        logger.error(f"❌ Redis测试失败: {e}")
        raise


async def test_cache_service():
    """测试缓存服务"""
    logger.info("🧪 测试缓存服务...")
    
    try:
        # 测试基本缓存操作
        test_key = "cache_test_key"
        test_value = {"message": "hello", "timestamp": datetime.now().isoformat()}
        
        # 设置缓存
        success = await cache_service.set(test_key, test_value, ttl=60)
        assert success
        logger.info("✅ 缓存设置测试通过")
        
        # 获取缓存
        cached_value = await cache_service.get(test_key)
        assert cached_value == test_value
        logger.info("✅ 缓存获取测试通过")
        
        # 检查存在性
        exists = await cache_service.exists(test_key)
        assert exists
        logger.info("✅ 缓存存在性检查测试通过")
        
        # 删除缓存
        deleted = await cache_service.delete(test_key)
        assert deleted
        logger.info("✅ 缓存删除测试通过")
        
        # 测试搜索缓存
        search_results = [{"doc": "test1"}, {"doc": "test2"}]
        await cache_service.set_search_cache(
            "test query", 
            "vector", 
            {"top_k": 5}, 
            search_results
        )
        
        cached_results = await cache_service.get_search_cache(
            "test query",
            "vector",
            {"top_k": 5}
        )
        assert cached_results == search_results
        logger.info("✅ 搜索缓存测试通过")
        
        # 清理搜索缓存
        cleared = await cache_service.clear_search_cache()
        logger.info(f"✅ 搜索缓存清理完成，清理了 {cleared} 个键")
        
    except Exception as e:
        logger.error(f"❌ 缓存服务测试失败: {e}")
        raise


async def test_session_service():
    """测试会话服务"""
    logger.info("🧪 测试会话服务...")
    
    try:
        session_id = "test_session_123"
        user_data = {"user_id": "user123", "role": "admin"}
        
        # 创建会话
        success = await session_service.create_session(session_id, user_data)
        assert success
        logger.info("✅ 会话创建测试通过")
        
        # 获取会话
        session_data = await session_service.get_session(session_id)
        assert session_data is not None
        assert session_data["user_data"] == user_data
        logger.info("✅ 会话获取测试通过")
        
        # 更新会话
        update_data = {"last_action": "login"}
        success = await session_service.update_session(session_id, update_data)
        assert success
        logger.info("✅ 会话更新测试通过")
        
        # 验证更新
        updated_session = await session_service.get_session(session_id)
        assert "last_action" in updated_session["user_data"]
        assert updated_session["user_data"]["last_action"] == "login"
        logger.info("✅ 会话更新验证通过")
        
        # 删除会话
        deleted = await session_service.delete_session(session_id)
        assert deleted
        logger.info("✅ 会话删除测试通过")
        
        # 验证删除
        deleted_session = await session_service.get_session(session_id)
        assert deleted_session is None
        logger.info("✅ 会话删除验证通过")
        
    except Exception as e:
        logger.error(f"❌ 会话服务测试失败: {e}")
        raise


async def test_metrics_service():
    """测试指标服务"""
    logger.info("🧪 测试指标服务...")
    
    try:
        metric_name = "test_metric"
        
        # 测试计数器
        await metrics_service.increment_counter(metric_name, 5)
        count = await metrics_service.get_counter(metric_name)
        assert count == 5
        logger.info("✅ 指标计数器测试通过")
        
        # 测试时间记录
        timing_metric = "test_timing"
        durations = [100, 200, 150, 300, 250]
        
        for duration in durations:
            await metrics_service.record_timing(timing_metric, duration)
        
        stats = await metrics_service.get_timing_stats(timing_metric)
        assert stats["count"] == 5
        assert stats["avg"] == 200.0
        assert stats["min"] == 100
        assert stats["max"] == 300
        logger.info("✅ 指标时间记录测试通过")
        
    except Exception as e:
        logger.error(f"❌ 指标服务测试失败: {e}")
        raise


async def test_integration():
    """集成测试"""
    logger.info("🧪 执行集成测试...")
    
    try:
        # 模拟完整的数据流程
        
        # 1. 在PostgreSQL中存储文档向量
        async with db_manager.get_postgres_session() as session:
            from database.models import DocumentVector
            import numpy as np
            
            test_doc = DocumentVector(
                document_id="integration_test_doc",
                content="这是一个集成测试文档",
                content_hash="integration_test_hash",
                embedding=np.random.rand(768).tolist(),
                metadata={"test": "integration"},
                source="integration_test",
                source_type="test"
            )
            
            session.add(test_doc)
            await session.commit()
            doc_id = test_doc.id
            logger.info("✅ PostgreSQL文档存储测试通过")
        
        # 2. 在Neo4j中创建对应的图谱节点
        with db_manager.get_neo4j_session() as session:
            session.run("""
                CREATE (d:Document {
                    id: $doc_id,
                    content: $content,
                    source: $source
                })
                CREATE (k:Keyword {word: '集成测试'})
                CREATE (d)-[:CONTAINS_KEYWORD]->(k)
            """, doc_id=str(doc_id), content="这是一个集成测试文档", source="integration_test")
            logger.info("✅ Neo4j图谱节点创建测试通过")
        
        # 3. 缓存查询结果
        search_result = [{"id": str(doc_id), "score": 0.95}]
        await cache_service.set_search_cache(
            "集成测试", 
            "integration", 
            {"doc_id": str(doc_id)}, 
            search_result
        )
        logger.info("✅ 缓存查询结果测试通过")
        
        # 4. 记录指标
        await metrics_service.increment_counter("integration_test_queries")
        await metrics_service.record_timing("integration_test_duration", 150)
        logger.info("✅ 指标记录测试通过")
        
        # 5. 验证数据一致性
        # PostgreSQL查询
        async with db_manager.get_postgres_session() as session:
            result = await session.execute(text(
                "SELECT COUNT(*) FROM document_vectors WHERE document_id = :doc_id"
            ), {"doc_id": "integration_test_doc"})
            pg_count = result.scalar()
            assert pg_count == 1
        
        # Neo4j查询
        with db_manager.get_neo4j_session() as session:
            result = session.run(
                "MATCH (d:Document {id: $doc_id}) RETURN count(d) as count", 
                doc_id=str(doc_id)
            )
            neo4j_count = result.single()["count"]
            assert neo4j_count == 1
        
        # 缓存查询
        cached_result = await cache_service.get_search_cache(
            "集成测试", 
            "integration", 
            {"doc_id": str(doc_id)}
        )
        assert cached_result == search_result
        
        logger.info("✅ 数据一致性验证通过")
        
        # 清理测试数据
        async with db_manager.get_postgres_session() as session:
            await session.execute(text(
                "DELETE FROM document_vectors WHERE document_id = :doc_id"
            ), {"doc_id": "integration_test_doc"})
            await session.commit()
        
        with db_manager.get_neo4j_session() as session:
            session.run("MATCH (d:Document {id: $doc_id}) DETACH DELETE d", doc_id=str(doc_id))
            session.run("MATCH (k:Keyword {word: '集成测试'}) DELETE k")
        
        await cache_service.clear_search_cache()
        
        logger.info("✅ 集成测试数据清理完成")
        logger.info("🎉 集成测试全部通过！")
        
    except Exception as e:
        logger.error(f"❌ 集成测试失败: {e}")
        raise


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库验证脚本")
    parser.add_argument("--quick", action="store_true", help="快速验证，跳过集成测试")
    args = parser.parse_args()
    
    logger.info("🚀 开始数据库验证...")
    
    try:
        # 初始化数据库连接
        await db_manager.initialize()
        
        # 基础数据库测试
        await test_postgresql()
        await test_neo4j()
        await test_redis()
        
        # 服务层测试
        await test_cache_service()
        await test_session_service()
        await test_metrics_service()
        
        # 集成测试 (除非指定跳过)
        if not args.quick:
            await test_integration()
        
        logger.info("🎉 所有数据库验证测试通过！")
        logger.info("✨ 系统已准备就绪，可以开始使用")
        
    except Exception as e:
        logger.error(f"❌ 数据库验证失败: {e}")
        sys.exit(1)
        
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())