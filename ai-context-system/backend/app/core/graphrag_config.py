"""
Graph RAG 核心引擎配置
基于LLM辅助的文档处理和知识图谱构建
"""

from pydantic_settings import BaseSettings
from typing import Optional


class GraphRAGSettings(BaseSettings):
    """Graph RAG 配置"""
    
    # LLM配置
    llm_api_key: str
    llm_api_base: str = "http://localhost:3000/v1"
    llm_chat_model: str = "Qwen/Qwen3-32B"
    llm_embedding_model: str = "Qwen/Qwen3-Embedding-8B"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    
    # Neo4j配置
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str = "ai_context"
    
    # ChromaDB配置
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "ai_context_vectors"
    
    # 文档处理配置
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_chunk_size: int = 1024
    enable_llm_chunking: bool = True
    
    # 实体提取配置
    enable_llm_entity_extraction: bool = True
    entity_extraction_batch_size: int = 10
    min_entity_confidence: float = 0.7
    
    # 图谱构建配置
    enable_community_detection: bool = True
    min_community_size: int = 3
    graph_embedding_dim: int = 768
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略未定义的额外字段


# 全局配置实例
graph_rag_settings = GraphRAGSettings()
