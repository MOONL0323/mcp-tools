"""
知识图谱服务 - 支持双后端
1. NetworkX内存图（开发/测试环境）
2. Neo4j图数据库（生产环境K8s部署）
"""
from typing import List, Dict, Optional
import structlog
import os

logger = structlog.get_logger()

# 尝试导入Neo4j
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j_unavailable", msg="将使用NetworkX内存存储")

# 导入NetworkX（内存图）
try:
    import networkx as nx
    import json
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class GraphService:
    """统一图存储服务 - 自动选择可用后端"""
    
    def __init__(self, backend: str = "auto"):
        """
        初始化图服务
        
        Args:
            backend: "auto" | "networkx" | "neo4j"
        """
        if backend == "auto":
            # 优先使用Neo4j（如果配置了URI）
            neo4j_uri = os.getenv("NEO4J_URI")
            if neo4j_uri and NEO4J_AVAILABLE:
                backend = "neo4j"
            elif NETWORKX_AVAILABLE:
                backend = "networkx"
            else:
                raise RuntimeError("没有可用的图存储后端")
        
        self.backend = backend
        
        if backend == "networkx":
            self._init_networkx()
        elif backend == "neo4j":
            self._init_neo4j()
        else:
            raise ValueError(f"未知后端: {backend}")
    
    def _init_networkx(self):
        """初始化NetworkX内存图"""
        if not NETWORKX_AVAILABLE:
            raise ImportError("需要安装: pip install networkx")
        
        self.graph = nx.MultiDiGraph()
        self.driver = None
        logger.info("graph_initialized", backend="NetworkX (Memory)")
    
    def _init_neo4j(self):
        """初始化Neo4j连接"""
        if not NEO4J_AVAILABLE:
            raise ImportError("需要安装: pip install neo4j")
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "ai-context-pass123")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.graph = None
        logger.info("graph_initialized", backend="Neo4j", uri=uri)
    
    def close(self):
        """关闭连接"""
        if self.backend == "neo4j" and self.driver:
            self.driver.close()
            logger.info("neo4j_closed")
    
    def create_indexes(self):
        """创建索引"""
        if self.backend == "neo4j":
            self._create_neo4j_indexes()
        # NetworkX不需要索引
    
    def _create_neo4j_indexes(self):
        """创建Neo4j索引"""
        with self.driver.session() as session:
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")
            session.run("CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name)")
            session.run("CREATE INDEX function_name IF NOT EXISTS FOR (f:Function) ON (f.name)")
            session.run("CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.document_id)")
            logger.info("neo4j_indexes_created")
    
    # ==================== 实体存储 ====================
    
    def store_python_entities(self, document_id: int, entities: Dict, relationships: List[Dict]):
        """存储Python代码实体"""
        if self.backend == "networkx":
            self._store_python_entities_nx(document_id, entities, relationships)
        else:
            self._store_python_entities_neo4j(document_id, entities, relationships)
    
    def _store_python_entities_nx(self, doc_id: int, entities: Dict, relationships: List[Dict]):
        """NetworkX存储"""
        # 添加文档节点
        doc_node = f"doc_{doc_id}"
        self.graph.add_node(doc_node, type="document", document_id=doc_id, content_type="python")
        
        # 添加类节点
        for cls in entities.get("classes", []):
            node_id = f"class_{doc_id}_{cls['name']}"
            self.graph.add_node(
                node_id,
                type="class",
                name=cls["name"],
                document_id=doc_id,
                line=cls.get("line", 0),
                docstring=cls.get("docstring", ""),
                methods=json.dumps(cls.get("methods", [])),
                bases=json.dumps(cls.get("bases", []))
            )
            self.graph.add_edge(doc_node, node_id, relation="CONTAINS")
        
        # 添加函数节点
        for func in entities.get("functions", []):
            node_id = f"func_{doc_id}_{func['name']}"
            self.graph.add_node(
                node_id,
                type="function",
                name=func["name"],
                document_id=doc_id,
                line=func.get("line", 0),
                params=json.dumps(func.get("params", [])),
                docstring=func.get("docstring", ""),
                return_type=func.get("return_type", "")
            )
            self.graph.add_edge(doc_node, node_id, relation="CONTAINS")
        
        # 添加导入节点
        for imp in entities.get("imports", []):
            for name in imp.get("names", []):
                node_id = f"module_{name}"
                if not self.graph.has_node(node_id):
                    self.graph.add_node(node_id, type="module", name=name)
                self.graph.add_edge(doc_node, node_id, relation="IMPORTS")
        
        # 添加关系
        for rel in relationships:
            source_id = self._find_node_by_name(doc_id, rel["source"])
            target_id = self._find_node_by_name(doc_id, rel["target"])
            if source_id and target_id:
                self.graph.add_edge(
                    source_id, 
                    target_id, 
                    relation=rel["relation"].upper(),
                    rel_type=rel.get("type", "")
                )
        
        logger.info("entities_stored_nx", document_id=doc_id, 
                   nodes=self.graph.number_of_nodes(),
                   edges=self.graph.number_of_edges())
    
    def _find_node_by_name(self, doc_id: int, name: str) -> Optional[str]:
        """在NetworkX图中查找节点"""
        for node, data in self.graph.nodes(data=True):
            if data.get("name") == name and (
                data.get("document_id") == doc_id or data.get("type") == "module"
            ):
                return node
        return None
    
    def _store_python_entities_neo4j(self, doc_id: int, entities: Dict, relationships: List[Dict]):
        """Neo4j存储"""
        with self.driver.session() as session:
            # 创建文档节点
            session.run(
                "MERGE (d:Document {document_id: $doc_id}) SET d.type = 'python_code'",
                doc_id=doc_id
            )
            
            # 创建类节点
            for cls in entities.get("classes", []):
                session.run(
                    """
                    MERGE (c:Class:Entity {name: $name, document_id: $doc_id})
                    SET c.line = $line, c.docstring = $docstring, 
                        c.methods = $methods, c.bases = $bases
                    WITH c
                    MATCH (d:Document {document_id: $doc_id})
                    MERGE (d)-[:CONTAINS]->(c)
                    """,
                    name=cls["name"], doc_id=doc_id, line=cls.get("line", 0),
                    docstring=cls.get("docstring", ""), methods=cls.get("methods", []),
                    bases=cls.get("bases", [])
                )
            
            # 创建函数节点
            for func in entities.get("functions", []):
                session.run(
                    """
                    MERGE (f:Function:Entity {name: $name, document_id: $doc_id})
                    SET f.line = $line, f.params = $params, f.docstring = $docstring,
                        f.return_type = $return_type
                    WITH f
                    MATCH (d:Document {document_id: $doc_id})
                    MERGE (d)-[:CONTAINS]->(f)
                    """,
                    name=func["name"], doc_id=doc_id, line=func.get("line", 0),
                    params=func.get("params", []), docstring=func.get("docstring", ""),
                    return_type=func.get("return_type", "")
                )
            
            # 创建关系
            for rel in relationships:
                session.run(
                    f"""
                    MATCH (s:Entity {{name: $source, document_id: $doc_id}})
                    MATCH (t:Entity {{name: $target}})
                    MERGE (s)-[r:{rel["relation"].upper()}]->(t)
                    SET r.type = $rel_type
                    """,
                    source=rel["source"], target=rel["target"], 
                    doc_id=doc_id, rel_type=rel.get("type", "")
                )
            
            logger.info("entities_stored_neo4j", document_id=doc_id)
    
    def store_keywords(self, document_id: int, keywords: List[Dict]):
        """存储文本关键词"""
        if self.backend == "networkx":
            self._store_keywords_nx(document_id, keywords)
        else:
            self._store_keywords_neo4j(document_id, keywords)
    
    def _store_keywords_nx(self, doc_id: int, keywords: List[Dict]):
        """NetworkX存储关键词"""
        doc_node = f"doc_{doc_id}"
        self.graph.add_node(doc_node, type="document", document_id=doc_id, content_type="text")
        
        for kw in keywords:
            node_id = f"keyword_{kw['term']}"
            if not self.graph.has_node(node_id):
                self.graph.add_node(node_id, type="keyword", term=kw["term"])
            
            self.graph.add_edge(
                doc_node, node_id,
                relation="HAS_KEYWORD",
                score=kw.get("score", 0.0),
                frequency=kw.get("frequency", 0)
            )
        
        logger.info("keywords_stored_nx", document_id=doc_id, count=len(keywords))
    
    def _store_keywords_neo4j(self, doc_id: int, keywords: List[Dict]):
        """Neo4j存储关键词"""
        with self.driver.session() as session:
            session.run(
                "MERGE (d:Document {document_id: $doc_id}) SET d.type = 'text'",
                doc_id=doc_id
            )
            
            for kw in keywords:
                session.run(
                    """
                    MERGE (k:Keyword:Entity {term: $term})
                    WITH k
                    MATCH (d:Document {document_id: $doc_id})
                    MERGE (d)-[r:HAS_KEYWORD]->(k)
                    SET r.score = $score, r.frequency = $frequency
                    """,
                    term=kw["term"], doc_id=doc_id,
                    score=kw.get("score", 0.0), frequency=kw.get("frequency", 0)
                )
            
            logger.info("keywords_stored_neo4j", document_id=doc_id, count=len(keywords))
    
    # ==================== 查询 ====================
    
    def query_entity_by_name(self, name: str) -> Optional[Dict]:
        """根据名称查询实体"""
        if self.backend == "networkx":
            return self._query_entity_nx(name)
        else:
            return self._query_entity_neo4j(name)
    
    def _query_entity_nx(self, name: str) -> Optional[Dict]:
        """NetworkX查询"""
        for node, data in self.graph.nodes(data=True):
            if data.get("name") == name or data.get("term") == name:
                result = dict(data)
                # 查询关系
                relationships = []
                for _, target, edge_data in self.graph.out_edges(node, data=True):
                    target_data = self.graph.nodes[target]
                    relationships.append({
                        "relation": edge_data.get("relation"),
                        "target": target_data.get("name") or target_data.get("term")
                    })
                result["relationships"] = relationships
                return result
        return None
    
    def _query_entity_neo4j(self, name: str) -> Optional[Dict]:
        """Neo4j查询"""
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
    
    def find_related_entities(self, entity_name: str, max_depth: int = 2) -> List[Dict]:
        """查找相关实体"""
        if self.backend == "networkx":
            return self._find_related_nx(entity_name, max_depth)
        else:
            return self._find_related_neo4j(entity_name, max_depth)
    
    def _find_related_nx(self, name: str, max_depth: int) -> List[Dict]:
        """NetworkX查找相关实体"""
        # 找到起始节点
        start_node = None
        for node, data in self.graph.nodes(data=True):
            if data.get("name") == name or data.get("term") == name:
                start_node = node
                break
        
        if not start_node:
            return []
        
        # BFS遍历
        related = []
        visited = {start_node}
        queue = [(start_node, 0)]
        
        while queue:
            node, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            
            # 遍历邻居
            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    node_data = self.graph.nodes[neighbor]
                    related.append({
                        "name": node_data.get("name") or node_data.get("term"),
                        "type": node_data.get("type"),
                        "distance": depth + 1
                    })
                    queue.append((neighbor, depth + 1))
        
        return related[:50]
    
    def _find_related_neo4j(self, name: str, max_depth: int) -> List[Dict]:
        """Neo4j查找相关实体"""
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
                name=name, depth=max_depth
            )
            return [{"name": r["name"], "labels": r["labels"], "distance": r["distance"]} 
                    for r in result]
    
    def get_graph_stats(self) -> Dict:
        """获取图统计信息"""
        if self.backend == "networkx":
            return self._get_stats_nx()
        else:
            return self._get_stats_neo4j()
    
    def _get_stats_nx(self) -> Dict:
        """NetworkX统计"""
        node_types = {}
        for _, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        relation_types = {}
        for _, _, data in self.graph.edges(data=True):
            rel_type = data.get("relation", "unknown")
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        return {
            "backend": "NetworkX (Memory)",
            "nodes": node_types,
            "relationships": relation_types,
            "total_nodes": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges()
        }
    
    def _get_stats_neo4j(self) -> Dict:
        """Neo4j统计"""
        with self.driver.session() as session:
            node_result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
            nodes = {r["label"]: r["count"] for r in node_result}
            
            rel_result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            relationships = {r["type"]: r["count"] for r in rel_result}
            
            return {
                "backend": "Neo4j",
                "nodes": nodes,
                "relationships": relationships,
                "total_nodes": sum(nodes.values()),
                "total_relationships": sum(relationships.values())
            }


# 全局单例
_graph_service = None


def get_graph_service() -> GraphService:
    """获取图服务单例"""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService(backend="auto")
        _graph_service.create_indexes()
    return _graph_service
