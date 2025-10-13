"""
Neo4j 图数据库客户端
用于知识图谱的构建和查询
"""

from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.graphrag_config import graph_rag_settings


class Neo4jClient:
    """Neo4j图数据库客户端"""
    
    def __init__(self):
        self.driver = None
        self.database = graph_rag_settings.neo4j_database
        self._initialized = False
        
    async def _ensure_connected(self):
        """延迟初始化连接"""
        if not self._initialized:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    graph_rag_settings.neo4j_uri,
                    auth=(
                        graph_rag_settings.neo4j_user,
                        graph_rag_settings.neo4j_password
                    )
                )
                # 测试连接
                async with self.driver.session(database=self.database) as session:
                    await session.run("RETURN 1")
                self._initialized = True
                logger.info(f"Neo4j connected: {graph_rag_settings.neo4j_uri}")
            except Exception as e:
                logger.error(f"Neo4j connection failed: {e}")
                raise
    
    async def create_entity_node(
        self,
        entity_type: str,
        entity_name: str,
        properties: Dict[str, Any]
    ) -> str:
        """创建实体节点"""
        await self._ensure_connected()
        async with self.driver.session(database=self.database) as session:
            query = f"""
            MERGE (e:{entity_type} {{name: $name}})
            SET e += $properties
            RETURN elementId(e) as id
            """
            result = await session.run(
                query,
                name=entity_name,
                properties=properties
            )
            record = await result.single()
            return record["id"] if record else None
    
    async def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """创建关系边"""
        await self._ensure_connected()
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (a), (b)
            WHERE elementId(a) = $source_id AND elementId(b) = $target_id
            MERGE (a)-[r:%s]->(b)
            SET r += $properties
            """ % relation_type
            
            await session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                properties=properties or {}
            )
    
    async def query_neighbors(
        self,
        entity_id: str,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """查询邻居节点"""
        await self._ensure_connected()
        async with self.driver.session(database=self.database) as session:
            query = f"""
            MATCH path = (start)-[*1..{depth}]-(neighbor)
            WHERE elementId(start) = $entity_id
            RETURN neighbor, relationships(path) as relations
            LIMIT 50
            """
            result = await session.run(query, entity_id=entity_id)
            records = await result.data()
            return records
    
    async def search_entities(
        self,
        entity_type: Optional[str] = None,
        name_pattern: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索实体"""
        await self._ensure_connected()
        async with self.driver.session(database=self.database) as session:
            conditions = []
            params = {"limit": limit}
            
            if entity_type:
                label_clause = f":{entity_type}"
            else:
                label_clause = ""
            
            if name_pattern:
                conditions.append("e.name CONTAINS $name_pattern")
                params["name_pattern"] = name_pattern
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"""
            MATCH (e{label_clause})
            {where_clause}
            RETURN elementId(e) as id, labels(e) as types, properties(e) as properties
            LIMIT $limit
            """
            
            result = await session.run(query, **params)
            return await result.data()
    
    async def delete_document_graph(self, document_id: str) -> None:
        """删除文档相关的图谱数据"""
        await self._ensure_connected()
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (n {document_id: $document_id})
            DETACH DELETE n
            """
            await session.run(query, document_id=document_id)
    
    async def close(self):
        """关闭连接"""
        if self.driver:
            await self.driver.close()


# 全局实例
neo4j_client = Neo4jClient()
