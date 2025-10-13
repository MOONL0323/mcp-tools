"""
本地图数据库实现（基于NetworkX）
用于无Docker环境的轻量级替代方案
"""

import networkx as nx
import json
import os
from typing import List, Dict, Any, Optional
from loguru import logger
from pathlib import Path


class LocalGraphClient:
    """本地图数据库客户端（NetworkX实现）"""
    
    def __init__(self, storage_path: str = "./graph_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.storage_path / "knowledge_graph.json"
        self.graph = nx.MultiDiGraph()
        self._load_graph()
        self._initialized = True
        logger.info(f"Local graph database initialized: {self.storage_path}")
        
    def _load_graph(self):
        """从文件加载图"""
        if self.graph_file.exists():
            try:
                data = json.loads(self.graph_file.read_text(encoding='utf-8'))
                self.graph = nx.node_link_graph(data, directed=True, multigraph=True)
                logger.info(f"Loaded graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
                self.graph = nx.MultiDiGraph()
    
    def _save_graph(self):
        """保存图到文件"""
        try:
            data = nx.node_link_data(self.graph)
            self.graph_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
    
    async def _ensure_connected(self):
        """确保连接（本地实现总是连接的）"""
        pass
    
    async def create_entity_node(
        self,
        entity_type: str,
        entity_name: str,
        properties: Dict[str, Any]
    ) -> str:
        """创建实体节点"""
        await self._ensure_connected()
        
        # 生成节点ID
        node_id = f"{entity_type}:{entity_name}"
        
        # 添加节点
        self.graph.add_node(
            node_id,
            type=entity_type,
            name=entity_name,
            **properties
        )
        
        self._save_graph()
        logger.debug(f"Created node: {node_id}")
        return node_id
    
    async def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """创建关系边"""
        await self._ensure_connected()
        
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            logger.warning(f"Cannot create edge: node not found")
            return
        
        self.graph.add_edge(
            source_id,
            target_id,
            type=relation_type,
            **(properties or {})
        )
        
        self._save_graph()
        logger.debug(f"Created edge: {source_id} -{relation_type}-> {target_id}")
    
    async def query_neighbors(
        self,
        entity_id: str,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """查询邻居节点"""
        await self._ensure_connected()
        
        if not self.graph.has_node(entity_id):
            return []
        
        neighbors = []
        
        # BFS遍历指定深度
        visited = {entity_id}
        current_level = {entity_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                # 获取所有邻居（入边和出边）
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in visited:
                        next_level.add(neighbor)
                        visited.add(neighbor)
                        neighbors.append({
                            'neighbor': {
                                'id': neighbor,
                                **self.graph.nodes[neighbor]
                            },
                            'relations': list(self.graph[node][neighbor].values())
                        })
                
                # 反向边
                for predecessor in self.graph.predecessors(node):
                    if predecessor not in visited:
                        next_level.add(predecessor)
                        visited.add(predecessor)
                        neighbors.append({
                            'neighbor': {
                                'id': predecessor,
                                **self.graph.nodes[predecessor]
                            },
                            'relations': list(self.graph[predecessor][node].values())
                        })
            
            current_level = next_level
        
        return neighbors
    
    async def search_entities(
        self,
        entity_type: Optional[str] = None,
        name_pattern: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索实体"""
        await self._ensure_connected()
        
        results = []
        
        for node_id, data in self.graph.nodes(data=True):
            # 类型过滤
            if entity_type and data.get('type') != entity_type:
                continue
            
            # 名称过滤
            if name_pattern and name_pattern.lower() not in data.get('name', '').lower():
                continue
            
            results.append({
                'id': node_id,
                'types': [data.get('type', 'Unknown')],
                'properties': data
            })
            
            if len(results) >= limit:
                break
        
        return results
    
    async def delete_document_graph(self, document_id: str) -> None:
        """删除文档相关的图谱数据"""
        await self._ensure_connected()
        
        # 查找所有与该文档相关的节点
        nodes_to_remove = [
            node for node, data in self.graph.nodes(data=True)
            if data.get('document_id') == document_id
        ]
        
        # 删除节点（会自动删除相关边）
        self.graph.remove_nodes_from(nodes_to_remove)
        self._save_graph()
        
        logger.info(f"Deleted {len(nodes_to_remove)} nodes for document {document_id}")
    
    async def close(self):
        """关闭连接"""
        self._save_graph()
        logger.info("Local graph database closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取图统计信息"""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'node_types': len(set(nx.get_node_attributes(self.graph, 'type').values()))
        }


# 全局实例
local_graph_client = LocalGraphClient(
    storage_path="D:/project/mcp-tools/ai-context-system/graph_data"
)
