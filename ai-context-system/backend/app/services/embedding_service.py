"""
Embedding向量化服务
使用 sentence-transformers 轻量级模型（可切换到 Qwen3-Embedding-8B）
"""

import asyncio
import json
import numpy as np
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """文本向量化服务"""
    
    def __init__(self, use_local_model: bool = True):
        """
        初始化向量化服务
        
        Args:
            use_local_model: True=使用本地sentence-transformers模型
                           False=使用远程Qwen3-Embedding-8B API
        """
        self.use_local_model = use_local_model
        
        if use_local_model:
            # 使用轻量级开源模型
            self.model_name = "all-MiniLM-L6-v2"  # 384维，80MB
            self.embedding_dimension = 384
            self._model = None  # 延迟加载
            logger.info(f"使用本地Embedding模型: {self.model_name}")
        else:
            # 使用远程API（内网环境）
            self.api_url = "https://oneapi.sangfor.com/v1/embeddings"
            self.api_key = "sk-KskGcDMEQWGncNHr6bE2Ee61F22b40F8A1C09c8b150968Ff"
            self.model_name = "qwen3-embedding-8b"
            self.embedding_dimension = 8192
            self.timeout = 60.0
            logger.info(f"使用远程Embedding API: {self.model_name}")
        
        self.max_batch_size = 32  # 本地模型可以处理更大批量
    
    def _load_local_model(self):
        """延迟加载本地模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"正在加载本地模型: {self.model_name}...")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"本地模型加载成功，向量维度: {self.embedding_dimension}")
            except ImportError:
                raise ImportError(
                    "需要安装 sentence-transformers: pip install sentence-transformers"
                )
        return self._model
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        为单个文本生成向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表，失败返回 None
        """
        if not text or not text.strip():
            logger.warning("空文本，跳过向量化")
            return None
        
        try:
            result = await self.embed_batch([text])
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"单文本向量化失败: {str(e)}", text_length=len(text))
            return None
    
    async def embed_batch(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[Optional[List[float]]]:
        """
        批量生成向量
        
        Args:
            texts: 文本列表
            show_progress: 是否显示进度
            
        Returns:
            向量列表，每个元素对应输入文本的向量（失败时为 None）
        """
        if not texts:
            return []
        
        # 过滤空文本
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
        
        if not valid_texts:
            logger.warning("所有文本都为空，跳过向量化")
            return [None] * len(texts)
        
        # 批量处理
        all_embeddings = [None] * len(texts)
        
        if self.use_local_model:
            # 使用本地模型
            return await self._embed_batch_local(texts, valid_texts, all_embeddings, show_progress)
        else:
            # 使用远程API
            return await self._embed_batch_remote(texts, valid_texts, all_embeddings, show_progress)
    
    async def _embed_batch_local(
        self,
        texts: List[str],
        valid_texts: List[tuple],
        all_embeddings: List[Optional[List[float]]],
        show_progress: bool
    ) -> List[Optional[List[float]]]:
        """使用本地模型批量向量化"""
        try:
            model = self._load_local_model()
            
            # sentence-transformers 是同步的，在线程池中运行
            loop = asyncio.get_event_loop()
            
            for batch_start in range(0, len(valid_texts), self.max_batch_size):
                batch = valid_texts[batch_start:batch_start + self.max_batch_size]
                batch_indices = [idx for idx, _ in batch]
                batch_texts = [text for _, text in batch]
                
                # 在线程池中执行同步操作
                embeddings = await loop.run_in_executor(
                    None,
                    lambda: model.encode(
                        batch_texts,
                        convert_to_numpy=True,
                        show_progress_bar=False
                    ).tolist()
                )
                
                # 将结果放回原位置
                for i, embedding in enumerate(embeddings):
                    original_idx = batch_indices[i]
                    all_embeddings[original_idx] = embedding
                
                if show_progress:
                    processed = min(batch_start + self.max_batch_size, len(valid_texts))
                    logger.info(f"向量化进度: {processed}/{len(valid_texts)}")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"本地模型向量化失败: {str(e)}")
            raise
    
    async def _embed_batch_remote(
        self,
        texts: List[str],
        valid_texts: List[tuple],
        all_embeddings: List[Optional[List[float]]],
        show_progress: bool
    ) -> List[Optional[List[float]]]:
        """使用远程API批量向量化"""
        import httpx
        
        for batch_start in range(0, len(valid_texts), self.max_batch_size):
            batch = valid_texts[batch_start:batch_start + self.max_batch_size]
            batch_indices = [idx for idx, _ in batch]
            batch_texts = [text for _, text in batch]
            
            try:
                embeddings = await self._call_embedding_api(batch_texts)
                
                # 将结果放回原位置
                for i, embedding in enumerate(embeddings):
                    original_idx = batch_indices[i]
                    all_embeddings[original_idx] = embedding
                
                if show_progress:
                    processed = min(batch_start + self.max_batch_size, len(valid_texts))
                    logger.info(f"向量化进度: {processed}/{len(valid_texts)}")
                    
            except Exception as e:
                logger.error(f"批量向量化失败: {str(e)}", batch_size=len(batch))
                # 批次失败，对应位置保持 None
        
        return all_embeddings
    
    async def _call_embedding_api(self, texts: List[str]) -> List[List[float]]:
        """
        调用远程 Embedding API（内网环境）
        
        Args:
            texts: 文本列表（已验证非空）
            
        Returns:
            向量列表
            
        Raises:
            Exception: API 调用失败
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_name,
                        "input": texts,
                        "encoding_format": "float"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "data" in result:
                        embeddings = []
                        for item in sorted(result["data"], key=lambda x: x["index"]):
                            embedding = item["embedding"]
                            embeddings.append(embedding)
                        
                        logger.info(
                            f"远程API向量化成功",
                            texts_count=len(texts),
                            embedding_dim=len(embeddings[0]) if embeddings else 0
                        )
                        
                        return embeddings
                    else:
                        raise Exception(f"API响应格式错误: {result}")
                else:
                    error_msg = response.text
                    raise Exception(f"API错误 {response.status_code}: {error_msg}")
                    
        except Exception as e:
            logger.error(f"远程Embedding API调用失败: {str(e)}")
            raise
    
    def serialize_embedding(self, embedding: List[float]) -> str:
        """
        序列化向量为字符串（用于存储到数据库）
        
        Args:
            embedding: 向量
            
        Returns:
            JSON字符串
        """
        return json.dumps(embedding)
    
    def deserialize_embedding(self, embedding_str: str) -> List[float]:
        """
        反序列化向量
        
        Args:
            embedding_str: JSON字符串
            
        Returns:
            向量列表
        """
        try:
            return json.loads(embedding_str)
        except Exception as e:
            logger.error(f"反序列化向量失败: {str(e)}")
            return []
    
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            embedding1: 向量1
            embedding2: 向量2
            
        Returns:
            相似度 [0, 1]，1表示完全相同
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # 确保结果在 [0, 1] 范围内
            return float(max(0.0, min(1.0, (similarity + 1) / 2)))
            
        except Exception as e:
            logger.error(f"计算相似度失败: {str(e)}")
            return 0.0
    
    async def embed_chunks_for_document(
        self,
        chunks: List[Dict[str, Any]],
        update_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        为文档的所有chunks生成向量
        
        Args:
            chunks: Chunk列表，每个chunk需要包含 'id' 和 'content'
            update_callback: 更新回调函数，用于更新数据库
            
        Returns:
            统计信息
        """
        if not chunks:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0
            }
        
        logger.info(f"开始为 {len(chunks)} 个chunks生成向量")
        
        # 提取文本
        chunk_texts = [chunk.get("content", "") for chunk in chunks]
        
        # 批量生成向量
        embeddings = await self.embed_batch(chunk_texts, show_progress=True)
        
        # 统计
        stats = {
            "total": len(chunks),
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # 更新数据库（如果提供了回调）
        if update_callback:
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding is None:
                    if not chunk.get("content", "").strip():
                        stats["skipped"] += 1
                    else:
                        stats["failed"] += 1
                    continue
                
                try:
                    # 序列化向量
                    embedding_str = self.serialize_embedding(embedding)
                    
                    # 调用更新回调
                    await update_callback(
                        chunk_id=chunk["id"],
                        embedding=embedding_str,
                        embedding_dim=len(embedding)
                    )
                    
                    stats["success"] += 1
                    
                except Exception as e:
                    logger.error(f"更新chunk向量失败: {str(e)}", chunk_id=chunk.get("id"))
                    stats["failed"] += 1
        else:
            # 没有回调，只统计
            for embedding in embeddings:
                if embedding is None:
                    stats["failed"] += 1
                else:
                    stats["success"] += 1
        
        logger.info(
            "向量化完成",
            **stats
        )
        
        return stats


# 全局单例
_embedding_service = None


def get_embedding_service(use_local_model: bool = True) -> EmbeddingService:
    """
    获取向量化服务单例
    
    Args:
        use_local_model: True=使用本地sentence-transformers模型（默认）
                       False=使用远程Qwen3-Embedding-8B API（需内网）
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(use_local_model=use_local_model)
    return _embedding_service

