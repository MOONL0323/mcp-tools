"""
向量化服务
使用Qwen3-Embedding-8B进行文本向量化
"""

from typing import List, Dict, Any
from loguru import logger
from app.services.llm_client import llm_client
from app.services.chroma_client import chroma_client
from app.services.chunking_service import DocumentChunk


class EmbeddingService:
    """向量化服务"""
    
    async def embed_chunks(
        self,
        chunks: List[DocumentChunk],
        document_id: str
    ) -> None:
        """
        批量向量化文档块并存储
        
        Args:
            chunks: 文档块列表
            document_id: 文档ID
        """
        try:
            # 准备文本
            texts = []
            for chunk in chunks:
                # 组合标题、摘要和内容作为embedding输入
                text = f"{chunk.title}\n{chunk.summary}\n{chunk.content}"
                texts.append(text)
            
            # 批量生成向量
            embeddings = await llm_client.embedding(texts)
            
            # 准备存储数据
            chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
            documents = [chunk.content for chunk in chunks]
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                metadatas.append({
                    "document_id": document_id,
                    "chunk_index": i,
                    "title": chunk.title,
                    "summary": chunk.summary,
                    "keywords": ",".join(chunk.keywords),
                    "chunk_type": chunk.chunk_type,
                    **chunk.metadata
                })
            
            # 存储到ChromaDB
            await chroma_client.add_chunks(
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"成功向量化并存储 {len(chunks)} 个文档块")
            
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            raise
    
    async def search_similar_chunks(
        self,
        query: str,
        n_results: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档块
        
        Args:
            query: 查询文本
            n_results: 返回结果数
            filters: 过滤条件
            
        Returns:
            相似文档块列表
        """
        try:
            # 生成查询向量
            query_embedding = await llm_client.embedding([query])
            
            # 向量搜索
            results = await chroma_client.similarity_search(
                query_embedding=query_embedding[0],
                n_results=n_results,
                where=filters
            )
            
            # 格式化结果
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "chunk_id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "relevance_score": 1 - results['distances'][0][i]  # 转换为相似度分数
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []


# 全局实例
embedding_service = EmbeddingService()
