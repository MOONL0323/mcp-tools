"""
抽象接口层
定义所有可替换组件的接口
"""

from .document_parser import DocumentParserInterface
from .embedding_provider import EmbeddingProviderInterface  
from .vector_store import VectorStoreInterface
from .knowledge_graph import KnowledgeGraphInterface

__all__ = [
    'DocumentParserInterface',
    'EmbeddingProviderInterface', 
    'VectorStoreInterface',
    'KnowledgeGraphInterface'
]