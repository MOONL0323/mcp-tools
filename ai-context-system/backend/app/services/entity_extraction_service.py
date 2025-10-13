"""
实体提取服务
使用LLM从文档中提取实体和关系，构建知识图谱
"""

import json
from typing import List, Dict, Any, Tuple
from loguru import logger
from app.services.llm_client import llm_client
from app.services.neo4j_local import local_graph_client  # 使用本地图客户端
from app.services.chunking_service import DocumentChunk


class Entity:
    """实体数据结构"""
    def __init__(
        self,
        name: str,
        entity_type: str,
        description: str = "",
        properties: Dict[str, Any] = None
    ):
        self.name = name
        self.entity_type = entity_type
        self.description = description
        self.properties = properties or {}


class Relation:
    """关系数据结构"""
    def __init__(
        self,
        source: str,
        target: str,
        relation_type: str,
        properties: Dict[str, Any] = None
    ):
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.properties = properties or {}


class EntityExtractor:
    """实体和关系提取器"""
    
    async def extract_from_chunks(
        self,
        chunks: List[DocumentChunk],
        document_id: str,
        document_type: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """
        从文档块中提取实体和关系
        
        Args:
            chunks: 文档块列表
            document_id: 文档ID
            document_type: 文档类型
            
        Returns:
            (实体列表, 关系列表)
        """
        all_entities = []
        all_relations = []
        
        for i, chunk in enumerate(chunks):
            try:
                entities, relations = await self._extract_from_chunk(
                    chunk,
                    document_id,
                    document_type
                )
                all_entities.extend(entities)
                all_relations.extend(relations)
                
                logger.info(f"处理块 {i+1}/{len(chunks)}: 提取 {len(entities)} 个实体, {len(relations)} 个关系")
                
            except Exception as e:
                logger.error(f"提取块 {i} 失败: {e}")
                continue
        
        # 合并相似实体
        merged_entities = self._merge_similar_entities(all_entities)
        
        logger.info(f"总计提取: {len(merged_entities)} 个实体, {len(all_relations)} 个关系")
        return merged_entities, all_relations
    
    async def _extract_from_chunk(
        self,
        chunk: DocumentChunk,
        document_id: str,
        document_type: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """从单个chunk中提取实体和关系"""
        
        if document_type == "demo_code" or chunk.chunk_type == "code":
            return await self._extract_code_entities(chunk, document_id)
        else:
            return await self._extract_doc_entities(chunk, document_id)
    
    async def _extract_code_entities(
        self,
        chunk: DocumentChunk,
        document_id: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """提取代码相关实体"""
        prompt = f"""从以下代码片段中提取实体和关系：

代码：
{chunk.content}

请提取：
1. 实体类型：Class(类)、Function(函数)、Variable(变量)、Module(模块)、API(接口)
2. 关系类型：INHERITS(继承)、CALLS(调用)、USES(使用)、BELONGS_TO(属于)、IMPLEMENTS(实现)

返回JSON格式：
```json
{{
  "entities": [
    {{"name": "实体名", "type": "类型", "description": "简短描述"}}
  ],
  "relations": [
    {{"source": "源实体", "target": "目标实体", "type": "关系类型"}}
  ]
}}
```"""
        
        try:
            response = await llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            data = await llm_client.extract_json_from_text(response)
            
            entities = [
                Entity(
                    name=e["name"],
                    entity_type=e["type"],
                    description=e.get("description", ""),
                    properties={"document_id": document_id, "chunk_type": "code"}
                )
                for e in data.get("entities", [])
            ]
            
            relations = [
                Relation(
                    source=r["source"],
                    target=r["target"],
                    relation_type=r["type"],
                    properties={"document_id": document_id}
                )
                for r in data.get("relations", [])
            ]
            
            return entities, relations
            
        except Exception as e:
            logger.error(f"代码实体提取失败: {e}")
            return [], []
    
    async def _extract_doc_entities(
        self,
        chunk: DocumentChunk,
        document_id: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """提取文档相关实体"""
        prompt = f"""从以下文档内容中提取实体和关系：

内容：
{chunk.content}

请提取：
1. 实体类型：Concept(概念)、API(接口)、Component(组件)、Service(服务)、Database(数据库)、Feature(功能)
2. 关系类型：DEPENDS_ON(依赖)、PART_OF(包含)、RELATES_TO(相关)、IMPLEMENTS(实现)、USES(使用)

返回JSON格式：
```json
{{
  "entities": [
    {{"name": "实体名", "type": "类型", "description": "简短描述"}}
  ],
  "relations": [
    {{"source": "源实体", "target": "目标实体", "type": "关系类型"}}
  ]
}}
```"""
        
        try:
            response = await llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            data = await llm_client.extract_json_from_text(response)
            
            entities = [
                Entity(
                    name=e["name"],
                    entity_type=e["type"],
                    description=e.get("description", ""),
                    properties={"document_id": document_id, "chunk_type": "document"}
                )
                for e in data.get("entities", [])
            ]
            
            relations = [
                Relation(
                    source=r["source"],
                    target=r["target"],
                    relation_type=r["type"],
                    properties={"document_id": document_id}
                )
                for r in data.get("relations", [])
            ]
            
            return entities, relations
            
        except Exception as e:
            logger.error(f"文档实体提取失败: {e}")
            return [], []
    
    def _merge_similar_entities(self, entities: List[Entity]) -> List[Entity]:
        """合并相似实体"""
        # 简单的基于名称的去重
        seen = {}
        merged = []
        
        for entity in entities:
            key = f"{entity.entity_type}:{entity.name.lower()}"
            if key not in seen:
                seen[key] = entity
                merged.append(entity)
        
        return merged
    
    async def build_graph(
        self,
        entities: List[Entity],
        relations: List[Relation]
    ) -> None:
        """构建知识图谱"""
        # 创建实体节点
        entity_id_map = {}
        for entity in entities:
            try:
                node_id = await local_graph_client.create_entity_node(
                    entity_type=entity.entity_type,
                    entity_name=entity.name,
                    properties={
                        "description": entity.description,
                        **entity.properties
                    }
                )
                entity_id_map[entity.name] = node_id
            except Exception as e:
                logger.error(f"创建实体节点失败 {entity.name}: {e}")
        
        # 创建关系
        for relation in relations:
            try:
                source_id = entity_id_map.get(relation.source)
                target_id = entity_id_map.get(relation.target)
                
                if source_id and target_id:
                    await local_graph_client.create_relation(
                        source_id=source_id,
                        target_id=target_id,
                        relation_type=relation.relation_type,
                        properties=relation.properties
                    )
            except Exception as e:
                logger.error(f"创建关系失败 {relation.source}->{relation.target}: {e}")


# 全局实例
entity_extractor = EntityExtractor()
