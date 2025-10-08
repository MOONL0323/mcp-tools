"""
Neo4j知识图谱实现
使用Neo4j专业图数据库进行知识图谱管理
"""
import json
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter, defaultdict
import asyncio
from neo4j import Transaction
from langchain.schema import Document
import numpy as np
from loguru import logger

from interfaces.knowledge_graph import KnowledgeGraphInterface
from interfaces.embedding_provider import EmbeddingProviderInterface
from database.connection import db_manager


class Neo4jKnowledgeGraph(KnowledgeGraphInterface):
    """Neo4j知识图谱实现"""
    
    def __init__(self):
        """初始化Neo4j知识图谱"""
        self.min_keyword_freq = 2
        self.max_keywords_per_doc = 20
        self.similarity_threshold = 0.7
        self.embedding_provider: Optional[EmbeddingProviderInterface] = None
        
        # 停用词
        self.stopwords = self._load_stopwords()
        
        logger.info("Neo4j知识图谱初始化完成")
    
    def set_embedding_provider(self, provider: EmbeddingProviderInterface):
        """设置嵌入提供者"""
        self.embedding_provider = provider
        logger.info("嵌入提供者设置完成")
    
    def _load_stopwords(self) -> Set[str]:
        """加载停用词表"""
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', 
            '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '对', '可以',
            '他', '她', '它', '们', '这个', '那个', '这些', '那些', '什么', '怎么', '为什么', '哪里',
            '如何', '所以', '因为', '但是', '然后', '而且', '或者', '以及', '等等', '比如', '例如'
        }
        return stopwords

    async def build_graph(self, documents: List[Document]) -> Dict[str, Any]:
        """构建知识图谱"""
        logger.info(f"开始构建知识图谱，文档数量: {len(documents)}")
        
        stats = {
            'documents_processed': 0,
            'entities_created': 0,
            'relationships_created': 0,
            'keywords_extracted': 0
        }
        
        with db_manager.get_neo4j_session() as session:
            # 清理现有数据 (可选)
            # session.run("MATCH (n) DETACH DELETE n")
            
            # 创建索引
            await self._create_indexes(session)
            
            # 处理每个文档
            for doc in documents:
                try:
                    doc_stats = await self._process_document(session, doc)
                    for key, value in doc_stats.items():
                        stats[key] += value
                    stats['documents_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"处理文档失败: {e}")
                    continue
            
            # 计算实体间关系
            relationship_stats = await self._compute_entity_relationships(session)
            stats['relationships_created'] += relationship_stats
        
        logger.info(f"知识图谱构建完成: {stats}")
        return stats

    async def _create_indexes(self, session):
        """创建Neo4j索引"""
        indexes = [
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX document_id_idx IF NOT EXISTS FOR (d:Document) ON (d.id)",
            "CREATE INDEX keyword_word_idx IF NOT EXISTS FOR (k:Keyword) ON (k.word)",
        ]
        
        for index_query in indexes:
            try:
                session.run(index_query)
            except Exception as e:
                logger.warning(f"创建索引失败: {e}")

    async def _process_document(self, session, doc: Document) -> Dict[str, int]:
        """处理单个文档"""
        content = doc.page_content
        metadata = doc.metadata
        doc_id = metadata.get('id', 'unknown')
        
        # 创建文档节点
        doc_params = {
            'id': doc_id,
            'content': content,
            'source': metadata.get('source', ''),
            'source_type': metadata.get('source_type', 'document'),
            'created_at': metadata.get('created_at', ''),
            'metadata': json.dumps(metadata)
        }
        
        session.run("""
            MERGE (d:Document {id: $id})
            SET d.content = $content,
                d.source = $source,
                d.source_type = $source_type,
                d.created_at = $created_at,
                d.metadata = $metadata
        """, **doc_params)
        
        # 提取关键词和实体
        keywords = await self._extract_keywords(content)
        entities = await self._extract_entities(content)
        
        stats = {
            'entities_created': 0,
            'keywords_extracted': len(keywords),
            'relationships_created': 0
        }
        
        # 创建关键词节点和关系
        for keyword, freq in keywords.items():
            session.run("""
                MERGE (k:Keyword {word: $word})
                SET k.frequency = COALESCE(k.frequency, 0) + $freq
                
                MERGE (d:Document {id: $doc_id})
                MERGE (d)-[r:CONTAINS_KEYWORD]->(k)
                SET r.frequency = $freq
            """, word=keyword, freq=freq, doc_id=doc_id)
        
        # 创建实体节点和关系
        for entity in entities:
            entity_params = {
                'name': entity['name'],
                'type': entity['type'],
                'confidence': entity.get('confidence', 1.0),
                'doc_id': doc_id
            }
            
            session.run("""
                MERGE (e:Entity {name: $name, type: $type})
                SET e.confidence = COALESCE(e.confidence, 0) + $confidence
                
                MERGE (d:Document {id: $doc_id})
                MERGE (d)-[r:MENTIONS]->(e)
                SET r.confidence = $confidence
            """, **entity_params)
            
            stats['entities_created'] += 1
        
        return stats

    async def _extract_keywords(self, text: str) -> Dict[str, int]:
        """提取关键词"""
        try:
            import jieba
            import jieba.analyse
            
            # 使用jieba提取关键词
            keywords = jieba.analyse.extract_tags(
                text, 
                topK=self.max_keywords_per_doc,
                withWeight=True
            )
            
            # 过滤停用词和短词
            filtered_keywords = {}
            for word, weight in keywords:
                if (len(word) > 1 and 
                    word not in self.stopwords and
                    not word.isdigit()):
                    filtered_keywords[word] = int(weight * 100)  # 转换为整数频率
            
            return filtered_keywords
            
        except ImportError:
            logger.warning("jieba未安装，使用简单分词")
            # 简单分词备选方案
            words = text.split()
            word_freq = Counter(words)
            return {w: f for w, f in word_freq.most_common(20) 
                   if len(w) > 1 and w not in self.stopwords}

    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取实体 (简化版本)"""
        entities = []
        
        # 简单的实体提取 (实际项目中可以使用NER模型)
        # 这里只是示例，提取可能的人名、地名等
        
        # 检测可能的人名 (以"先生"、"女士"等结尾的词)
        import re
        
        # 人名模式
        person_patterns = [
            r'([A-Za-z\u4e00-\u9fa5]{2,4})(先生|女士|教授|博士|老师)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)',  # 英文人名
        ]
        
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match[0] if isinstance(match, tuple) else match
                entities.append({
                    'name': name,
                    'type': 'PERSON',
                    'confidence': 0.8
                })
        
        # 检测可能的组织机构
        org_patterns = [
            r'([A-Za-z\u4e00-\u9fa5]{2,10})(公司|企业|集团|大学|学院|研究所)',
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match[0] + match[1]
                entities.append({
                    'name': name,
                    'type': 'ORGANIZATION',
                    'confidence': 0.7
                })
        
        return entities

    async def _compute_entity_relationships(self, session) -> int:
        """计算实体间关系"""
        relationships_created = 0
        
        # 计算共现关系
        cooccurrence_query = """
        MATCH (d:Document)-[:MENTIONS]->(e1:Entity),
              (d)-[:MENTIONS]->(e2:Entity)
        WHERE e1.name < e2.name
        WITH e1, e2, count(d) as cooccurrence
        WHERE cooccurrence >= 2
        MERGE (e1)-[r:RELATED_TO]-(e2)
        SET r.strength = cooccurrence,
            r.type = 'cooccurrence'
        RETURN count(r) as relationships
        """
        
        result = session.run(cooccurrence_query)
        record = result.single()
        if record:
            relationships_created += record['relationships']
        
        # 计算关键词相似性关系
        if self.embedding_provider:
            await self._compute_semantic_relationships(session)
        
        return relationships_created

    async def _compute_semantic_relationships(self, session):
        """计算语义相似性关系"""
        # 获取所有关键词
        keywords_result = session.run("MATCH (k:Keyword) RETURN k.word as word")
        keywords = [record['word'] for record in keywords_result]
        
        if len(keywords) < 2:
            return
        
        # 生成嵌入向量 (批量处理以提高效率)
        embeddings = await self.embedding_provider.get_embeddings(keywords)
        
        # 计算相似度并创建关系
        for i, keyword1 in enumerate(keywords):
            for j, keyword2 in enumerate(keywords[i+1:], i+1):
                # 计算余弦相似度
                similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                
                if similarity > self.similarity_threshold:
                    session.run("""
                        MATCH (k1:Keyword {word: $word1}),
                              (k2:Keyword {word: $word2})
                        MERGE (k1)-[r:SIMILAR_TO]-(k2)
                        SET r.similarity = $similarity,
                            r.type = 'semantic'
                    """, word1=keyword1, word2=keyword2, similarity=similarity)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)

    async def query_graph(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """查询知识图谱"""
        results = []
        
        with db_manager.get_neo4j_session() as session:
            # 实体查询
            entity_query = """
            MATCH (e:Entity)
            WHERE e.name CONTAINS $query
            OPTIONAL MATCH (e)-[r:RELATED_TO]-(related:Entity)
            RETURN e, collect(related) as related_entities
            LIMIT $limit
            """
            
            entity_results = session.run(entity_query, query=query, limit=max_results)
            
            for record in entity_results:
                entity = record['e']
                related = record['related_entities']
                
                results.append({
                    'type': 'entity',
                    'name': entity['name'],
                    'entity_type': entity['type'],
                    'confidence': entity.get('confidence', 0),
                    'related_entities': [r['name'] for r in related if r]
                })
            
            # 关键词查询
            keyword_query = """
            MATCH (k:Keyword)
            WHERE k.word CONTAINS $query
            OPTIONAL MATCH (k)-[r:SIMILAR_TO]-(similar:Keyword)
            RETURN k, collect(similar) as similar_keywords
            LIMIT $limit
            """
            
            keyword_results = session.run(keyword_query, query=query, limit=max_results)
            
            for record in keyword_results:
                keyword = record['k']
                similar = record['similar_keywords']
                
                results.append({
                    'type': 'keyword',
                    'word': keyword['word'],
                    'frequency': keyword.get('frequency', 0),
                    'similar_keywords': [s['word'] for s in similar if s]
                })
        
        logger.info(f"图谱查询完成: {len(results)} 个结果")
        return results

    async def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        with db_manager.get_neo4j_session() as session:
            stats_query = """
            MATCH (d:Document) WITH count(d) as doc_count
            MATCH (e:Entity) WITH doc_count, count(e) as entity_count
            MATCH (k:Keyword) WITH doc_count, entity_count, count(k) as keyword_count
            MATCH ()-[r:RELATED_TO]-() WITH doc_count, entity_count, keyword_count, count(r) as relation_count
            RETURN doc_count, entity_count, keyword_count, relation_count
            """
            
            result = session.run(stats_query)
            record = result.single()
            
            if record:
                return {
                    'documents': record['doc_count'],
                    'entities': record['entity_count'],
                    'keywords': record['keyword_count'],
                    'relationships': record['relation_count']
                }
            else:
                return {
                    'documents': 0,
                    'entities': 0,
                    'keywords': 0,
                    'relationships': 0
                }

    async def export_graph(self, format: str = 'json') -> Dict[str, Any]:
        """导出图谱数据"""
        with db_manager.get_neo4j_session() as session:
            if format == 'json':
                # 导出为JSON格式
                nodes_query = """
                MATCH (n)
                RETURN labels(n) as labels, properties(n) as properties
                """
                
                edges_query = """
                MATCH (a)-[r]->(b)
                RETURN labels(a) as source_labels, properties(a) as source_props,
                       type(r) as relationship_type, properties(r) as rel_props,
                       labels(b) as target_labels, properties(b) as target_props
                """
                
                nodes = [dict(record) for record in session.run(nodes_query)]
                edges = [dict(record) for record in session.run(edges_query)]
                
                return {
                    'nodes': nodes,
                    'edges': edges,
                    'format': 'json'
                }
        
        return {}

    async def save_graph(self, filepath: str):
        """保存图谱到文件"""
        graph_data = await self.export_graph()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"图谱已保存到: {filepath}")

    async def load_graph(self, filepath: str):
        """从文件加载图谱"""
        logger.info(f"从文件加载图谱功能需要根据具体需求实现: {filepath}")
        # 实现加载逻辑