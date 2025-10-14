"""
知识图谱服务
支持两种后端：
1. NetworkX内存图（开发/测试）
2. Neo4j图数据库（生产环境）
"""
from typing import List, Dict, Optional
import structlog

logger = structlog.get_logger()

# 尝试导入Neo4j，如果失败则使用NetworkX
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j_not_available", msg="使用NetworkX内存图存储")

# NetworkX用于内存图存储
try:
    import networkx as nx
    import json
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.error("networkx_not_available", msg="需要安装: pip install networkx")


class GraphService:
    """
    统一图存储服务接口
    自动选择可用的后端：Neo4j（生产）或NetworkX（开发）
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", 
                 password: str = "ai-context-pass123",
                 use_memory: bool = None):
        """
        初始化图存储服务
        
        Args:
            uri: Neo4j连接URI
            user: Neo4j用户名
            password: Neo4j密码
            use_memory: 强制使用内存存储（None=自动检测）
        """
        # 自动选择后端
        if use_memory is None:
            use_memory = not NEO4J_AVAILABLE
        
        self.use_memory = use_memory
        self.driver = None
        self.graph = None
        
        if use_memory:
            # 使用NetworkX内存图
            if not NETWORKX_AVAILABLE:
                raise ImportError("NetworkX未安装，请运行: pip install networkx")
            self.graph = nx.MultiDiGraph()
            logger.info("graph_backend_initialized", backend="NetworkX (Memory)")
        else:
            # 使用Neo4j
            if not NEO4J_AVAILABLE:
                raise ImportError("Neo4j驱动未安装，请运行: pip install neo4j")
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info("graph_backend_initialized", backend="Neo4j", uri=uri)
    
    def close(self):
        """关闭连接"""
        self.driver.close()
        logger.info("neo4j_closed")
    
    def create_indexes(self):
        """创建索引以提高查询性能"""
        with self.driver.session() as session:
            # 实体名称索引
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")
            # 类索引
            session.run("CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name)")
            # 函数索引
            session.run("CREATE INDEX function_name IF NOT EXISTS FOR (f:Function) ON (f.name)")
            # 文档索引
            session.run("CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.document_id)")
            logger.info("neo4j_indexes_created")
    
    def store_python_entities(self, document_id: int, entities: Dict, relationships: List[Dict]):
        """
        存储Python代码实体到Neo4j
        
        Args:
            document_id: 文档ID
            entities: 实体字典 {classes: [...], functions: [...], imports: [...]}
            relationships: 关系列表
        """
        with self.driver.session() as session:
            # 1. 创建文档节点
            session.run(
                """
                MERGE (d:Document {document_id: $doc_id})
                SET d.type = 'python_code'
                """,
                doc_id=document_id
            )
            
            # 2. 创建类节点
            for cls in entities.get("classes", []):
                session.run(
                    """
                    MERGE (c:Class:Entity {name: $name, document_id: $doc_id})
                    SET c.line = $line,
                        c.docstring = $docstring,
                        c.methods = $methods,
                        c.bases = $bases
                    WITH c
                    MATCH (d:Document {document_id: $doc_id})
                    MERGE (d)-[:CONTAINS]->(c)
                    """,
                    name=cls["name"],
                    doc_id=document_id,
                    line=cls.get("line", 0),
                    docstring=cls.get("docstring", ""),
                    methods=cls.get("methods", []),
                    bases=cls.get("bases", [])
                )
            
            # 3. 创建函数节点
            for func in entities.get("functions", []):
                session.run(
                    """
                    MERGE (f:Function:Entity {name: $name, document_id: $doc_id})
                    SET f.line = $line,
                        f.params = $params,
                        f.docstring = $docstring,
                        f.return_type = $return_type
                    WITH f
                    MATCH (d:Document {document_id: $doc_id})
                    MERGE (d)-[:CONTAINS]->(f)
                    """,
                    name=func["name"],
                    doc_id=document_id,
                    line=func.get("line", 0),
                    params=func.get("params", []),
                    docstring=func.get("docstring", ""),
                    return_type=func.get("return_type", "")
                )
            
            # 4. 创建导入节点
            for imp in entities.get("imports", []):
                module = imp.get("module", "unknown")
                for name in imp.get("names", []):
                    session.run(
                        """
                        MERGE (m:Module:Entity {name: $name})
                        WITH m
                        MATCH (d:Document {document_id: $doc_id})
                        MERGE (d)-[:IMPORTS]->(m)
                        """,
                        name=name,
                        doc_id=document_id
                    )
            
            # 5. 创建关系
            for rel in relationships:
                source = rel["source"]
                target = rel["target"]
                relation = rel["relation"].upper()
                
                session.run(
                    f"""
                    MATCH (s:Entity {{name: $source, document_id: $doc_id}})
                    MATCH (t:Entity {{name: $target}})
                    MERGE (s)-[r:{relation}]->(t)
                    SET r.type = $rel_type
                    """,
                    source=source,
                    target=target,
                    doc_id=document_id,
                    rel_type=rel.get("type", "")
                )
            
            logger.info("python_entities_stored", 
                       document_id=document_id,
                       classes=len(entities.get("classes", [])),
                       functions=len(entities.get("functions", [])),
                       relationships=len(relationships))
    
    def store_keywords(self, document_id: int, keywords: List[Dict]):
        """
        存储文本关键词到Neo4j
        
        Args:
            document_id: 文档ID
            keywords: 关键词列表 [{"term": "...", "score": ..., "frequency": ...}]
        """
        with self.driver.session() as session:
            # 创建文档节点
            session.run(
                """
                MERGE (d:Document {document_id: $doc_id})
                SET d.type = 'text'
                """,
                doc_id=document_id
            )
            
            # 创建关键词节点和关系
            for kw in keywords:
                session.run(
                    """
                    MERGE (k:Keyword:Entity {term: $term})
                    WITH k
                    MATCH (d:Document {document_id: $doc_id})
                    MERGE (d)-[r:HAS_KEYWORD]->(k)
                    SET r.score = $score,
                        r.frequency = $frequency
                    """,
                    term=kw["term"],
                    doc_id=document_id,
                    score=kw.get("score", 0.0),
                    frequency=kw.get("frequency", 0)
                )
            
            logger.info("keywords_stored", document_id=document_id, count=len(keywords))
    
    def query_entity_by_name(self, name: str) -> Optional[Dict]:
        """根据名称查询实体"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity {name: $name})
                OPTIONAL MATCH (e)-[r]->(related)
                RETURN e, collect({rel: type(r), target: related.name}) as relationships
                """,
                name=name
            )
            record = result.single()
            if record:
                entity = dict(record["e"])
                entity["relationships"] = record["relationships"]
                return entity
            return None
    
    def query_document_entities(self, document_id: int) -> Dict:
        """查询文档的所有实体"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Document {document_id: $doc_id})-[:CONTAINS]->(e:Entity)
                RETURN labels(e) as labels, properties(e) as props
                """,
                doc_id=document_id
            )
            
            entities = {"classes": [], "functions": [], "keywords": []}
            for record in result:
                labels = record["labels"]
                props = record["props"]
                
                if "Class" in labels:
                    entities["classes"].append(props)
                elif "Function" in labels:
                    entities["functions"].append(props)
                elif "Keyword" in labels:
                    entities["keywords"].append(props)
            
            return entities
    
    def find_related_entities(self, entity_name: str, max_depth: int = 2) -> List[Dict]:
        """
        查找与实体相关的其他实体（图遍历）
        
        Args:
            entity_name: 实体名称
            max_depth: 最大遍历深度
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (e:Entity {name: $name})-[*1..$depth]-(related:Entity)
                RETURN DISTINCT related.name as name, 
                       labels(related) as labels,
                       length(path) as distance
                ORDER BY distance
                LIMIT 50
                """,
                name=entity_name,
                depth=max_depth
            )
            
            return [{"name": r["name"], "labels": r["labels"], "distance": r["distance"]} 
                    for r in result]
    
    def get_graph_stats(self) -> Dict:
        """获取图数据库统计信息"""
        with self.driver.session() as session:
            # 节点统计
            node_result = session.run(
                """
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                """
            )
            nodes = {r["label"]: r["count"] for r in node_result}
            
            # 关系统计
            rel_result = session.run(
                """
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                """
            )
            relationships = {r["type"]: r["count"] for r in rel_result}
            
            return {
                "nodes": nodes,
                "relationships": relationships,
                "total_nodes": sum(nodes.values()),
                "total_relationships": sum(relationships.values())
            }


# 全局单例
_neo4j_service = None


def get_neo4j_service() -> Neo4jService:
    """获取Neo4j服务单例"""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
        _neo4j_service.create_indexes()
    return _neo4j_service
