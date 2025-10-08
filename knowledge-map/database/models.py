"""
PostgreSQL向量存储数据模型
使用SQLAlchemy和pgvector
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index, Float
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid

from database.connection import Base


class DocumentVector(Base):
    """文档向量表"""
    __tablename__ = "document_vectors"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 文档信息
    document_id = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    
    # 向量数据
    embedding = Column(Vector(768), nullable=False)  # BGE模型默认768维
    
    # 元数据
    metadata = Column(JSON, nullable=True)
    source = Column(String(500), nullable=True, index=True)
    source_type = Column(String(50), nullable=True, index=True)  # document, code, etc.
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        Index('ix_document_vectors_embedding_hnsw', 'embedding', postgresql_using='hnsw'),
        Index('ix_document_vectors_source_type', 'source', 'source_type'),
        Index('ix_document_vectors_created_at', 'created_at'),
    )


class DocumentChunk(Base):
    """文档分块表"""
    __tablename__ = "document_chunks"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 关联到向量表
    vector_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # 分块信息
    document_id = Column(String(255), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_content = Column(Text, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    
    # 上下文信息
    previous_chunk_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    next_chunk_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # 元数据
    metadata = Column(JSON, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        Index('ix_document_chunks_document_id_index', 'document_id', 'chunk_index'),
        Index('ix_document_chunks_vector_id', 'vector_id'),
    )


class SearchLog(Base):
    """搜索日志表"""
    __tablename__ = "search_logs"
    
    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 搜索信息
    query = Column(Text, nullable=False)
    query_embedding = Column(Vector(768), nullable=True)
    
    # 搜索参数
    search_type = Column(String(50), nullable=False, index=True)  # vector, text, hybrid
    top_k = Column(Integer, nullable=False)
    similarity_threshold = Column(Float, nullable=True)
    
    # 结果信息
    result_count = Column(Integer, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    
    # 用户信息
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        Index('ix_search_logs_created_at', 'created_at'),
        Index('ix_search_logs_search_type', 'search_type'),
    )