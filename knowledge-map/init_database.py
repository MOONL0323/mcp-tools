#!/usr/bin/env python3
"""
数据库初始化脚本
创建PostgreSQL表结构和Neo4j约束
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from sqlalchemy import text
from database.connection import db_manager, Base
from database.models import DocumentVector, DocumentChunk, SearchLog


async def init_postgresql():
    """初始化PostgreSQL数据库"""
    logger.info("正在初始化PostgreSQL数据库...")
    
    try:
        # 创建数据库引擎并建立连接
        async with db_manager.get_postgres_session() as session:
            # 检查pgvector扩展
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await session.commit()
            logger.info("pgvector扩展已启用")
        
        # 创建所有表
        async with db_manager._postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("PostgreSQL表结构创建完成")
        
        # 创建额外的索引
        async with db_manager.get_postgres_session() as session:
            # 创建GIN索引用于全文搜索
            try:
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_document_vectors_content_gin 
                    ON document_vectors 
                    USING gin(to_tsvector('jiebacfg', content));
                """))
                logger.info("全文搜索索引创建完成")
            except Exception as e:
                logger.warning(f"创建全文搜索索引失败: {e}")
            
            # 创建复合索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_document_vectors_source_type_created 
                ON document_vectors (source_type, created_at DESC);
            """))
            
            await session.commit()
            logger.info("额外索引创建完成")
        
        logger.info("PostgreSQL初始化完成")
        
    except Exception as e:
        logger.error(f"PostgreSQL初始化失败: {e}")
        raise


async def init_neo4j():
    """初始化Neo4j数据库"""
    logger.info("正在初始化Neo4j数据库...")
    
    try:
        with db_manager.get_neo4j_session() as session:
            # 创建约束
            constraints = [
                "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE",
                "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT keyword_word_unique IF NOT EXISTS FOR (k:Keyword) REQUIRE k.word IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"约束创建成功: {constraint.split()[2]}")
                except Exception as e:
                    logger.warning(f"创建约束失败: {e}")
            
            # 创建索引
            indexes = [
                "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                "CREATE INDEX document_source_idx IF NOT EXISTS FOR (d:Document) ON (d.source)",
                "CREATE INDEX document_source_type_idx IF NOT EXISTS FOR (d:Document) ON (d.source_type)",
                "CREATE INDEX keyword_frequency_idx IF NOT EXISTS FOR (k:Keyword) ON (k.frequency)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"索引创建成功: {index.split()[2]}")
                except Exception as e:
                    logger.warning(f"创建索引失败: {e}")
        
        logger.info("Neo4j初始化完成")
        
    except Exception as e:
        logger.error(f"Neo4j初始化失败: {e}")
        raise


async def verify_connections():
    """验证数据库连接"""
    logger.info("正在验证数据库连接...")
    
    # 验证PostgreSQL
    try:
        async with db_manager.get_postgres_session() as session:
            result = await session.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"PostgreSQL连接成功: {version.split()[0]} {version.split()[1]}")
            
            # 验证pgvector
            result = await session.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector';"))
            vector_version = result.scalar()
            if vector_version:
                logger.info(f"pgvector版本: {vector_version}")
            else:
                logger.warning("pgvector扩展未安装")
                
    except Exception as e:
        logger.error(f"PostgreSQL连接验证失败: {e}")
        raise
    
    # 验证Neo4j
    try:
        with db_manager.get_neo4j_session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            for record in result:
                logger.info(f"Neo4j组件: {record['name']} - {record['version']}")
                
    except Exception as e:
        logger.error(f"Neo4j连接验证失败: {e}")
        raise
    
    # 验证Redis
    try:
        redis_client = await db_manager.get_redis_client()
        info = await redis_client.info()
        await redis_client.close()
        
        logger.info(f"Redis连接成功: {info['redis_version']}")
        
    except Exception as e:
        logger.error(f"Redis连接验证失败: {e}")
        raise
    
    logger.info("所有数据库连接验证成功")


async def create_sample_data():
    """创建示例数据 (可选)"""
    logger.info("正在创建示例数据...")
    
    try:
        # 在PostgreSQL中创建示例向量
        async with db_manager.get_postgres_session() as session:
            from database.models import DocumentVector
            import numpy as np
            
            # 创建一个示例文档
            sample_embedding = np.random.rand(768).tolist()  # 随机768维向量
            
            sample_doc = DocumentVector(
                document_id="sample_doc_001",
                content="这是一个示例文档，用于验证系统功能。",
                content_hash="sample_hash_001",
                embedding=sample_embedding,
                metadata={"type": "sample", "created_by": "init_script"},
                source="init_script",
                source_type="sample"
            )
            
            session.add(sample_doc)
            await session.commit()
            
            logger.info("PostgreSQL示例数据创建完成")
        
        # 在Neo4j中创建示例节点
        with db_manager.get_neo4j_session() as session:
            session.run("""
                CREATE (d:Document {
                    id: 'sample_doc_001',
                    content: '这是一个示例文档，用于验证系统功能。',
                    source: 'init_script',
                    source_type: 'sample'
                })
                CREATE (k:Keyword {word: '示例', frequency: 1})
                CREATE (k2:Keyword {word: '文档', frequency: 1})
                CREATE (e:Entity {name: '系统', type: 'CONCEPT'})
                CREATE (d)-[:CONTAINS_KEYWORD]->(k)
                CREATE (d)-[:CONTAINS_KEYWORD]->(k2)
                CREATE (d)-[:MENTIONS]->(e)
            """)
            
            logger.info("Neo4j示例数据创建完成")
        
        logger.info("示例数据创建完成")
        
    except Exception as e:
        logger.warning(f"创建示例数据失败: {e}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument("--skip-sample", action="store_true", help="跳过创建示例数据")
    parser.add_argument("--verify-only", action="store_true", help="仅验证连接")
    args = parser.parse_args()
    
    try:
        # 初始化数据库连接
        await db_manager.initialize()
        
        if args.verify_only:
            await verify_connections()
            return
        
        # 初始化各个数据库
        await init_postgresql()
        await init_neo4j()
        
        # 验证连接
        await verify_connections()
        
        # 创建示例数据 (可选)
        if not args.skip_sample:
            await create_sample_data()
        
        logger.info("🎉 数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)
        
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())