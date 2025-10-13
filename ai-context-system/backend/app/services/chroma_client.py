"""
ChromaDB 向量数据库客户端
用于向量存储和相似度搜索
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.graphrag_config import graph_rag_settings


class ChromaDBClient:
    """ChromaDB向量数据库客户端"""
    
    def __init__(self):
        self.client = None
        self.collection_name = graph_rag_settings.chroma_collection
        self.collection = None
        self._initialized = False
        
    def _ensure_connected(self):
        """延迟初始化连接"""
        if not self._initialized:
            try:
                self.client = chromadb.HttpClient(
                    host=graph_rag_settings.chroma_host,
                    port=graph_rag_settings.chroma_port,
                    settings=Settings(anonymized_telemetry=False)
                )
                self._initialized = True
                logger.info(f"ChromaDB connected: {graph_rag_settings.chroma_host}:{graph_rag_settings.chroma_port}")
            except Exception as e:
                logger.error(f"ChromaDB connection failed: {e}")
                raise
    
    def get_or_create_collection(self):
        """获取或创建集合"""
        self._ensure_connected()
        if not self.collection:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "AI Context System - Document Chunks"}
            )
        return self.collection
    
    async def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """批量添加文档块向量"""
        try:
            collection = self.get_or_create_collection()
            collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"成功添加 {len(chunk_ids)} 个文档块到向量库")
        except Exception as e:
            logger.error(f"添加向量失败: {e}")
            raise
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """向量相似度搜索"""
        try:
            collection = self.get_or_create_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def delete_by_document(self, document_id: str) -> None:
        """删除文档相关的所有向量"""
        try:
            collection = self.get_or_create_collection()
            collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"成功删除文档 {document_id} 的向量数据")
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            collection = self.get_or_create_collection()
            count = collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}


# 全局实例
chroma_client = ChromaDBClient()
