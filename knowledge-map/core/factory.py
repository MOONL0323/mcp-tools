"""
组件工厂
管理所有可替换组件的创建和配置
"""
import os
from typing import Dict, Any, Type, Optional
from loguru import logger

from interfaces import (
    DocumentParserInterface,
    EmbeddingProviderInterface,
    VectorStoreInterface,
    KnowledgeGraphInterface
)


class ComponentFactory:
    """组件工厂类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化工厂
        
        Args:
            config: 配置字典
        """
        self.config = config
        self._parsers: Dict[str, Type[DocumentParserInterface]] = {}
        self._embedding_providers: Dict[str, Type[EmbeddingProviderInterface]] = {}
        self._vector_stores: Dict[str, Type[VectorStoreInterface]] = {}
        self._knowledge_graphs: Dict[str, Type[KnowledgeGraphInterface]] = {}
        
        # 注册默认实现
        self._register_default_implementations()
    
    def _register_default_implementations(self):
        """注册默认实现"""
        # 注册文档解析器
        from implementations.parsers.default_parser import DefaultDocumentParser
        self.register_document_parser('default', DefaultDocumentParser)
        
        # 注册向量化服务
        from implementations.embeddings.local_provider import LocalEmbeddingProvider
        from implementations.embeddings.advanced_provider import AdvancedEmbeddingProvider
        self.register_embedding_provider('local', LocalEmbeddingProvider)
        self.register_embedding_provider('advanced', AdvancedEmbeddingProvider)
        
        # 注册向量存储
        from implementations.stores.local_store import LocalVectorStore
        self.register_vector_store('local', LocalVectorStore)
        
        # 注册知识图谱
        from implementations.graphs.local_graph import LocalKnowledgeGraph
        self.register_knowledge_graph('local', LocalKnowledgeGraph)
    
    def register_document_parser(self, name: str, parser_class: Type[DocumentParserInterface]):
        """注册文档解析器"""
        self._parsers[name] = parser_class
        logger.info(f"注册文档解析器: {name}")
    
    def register_embedding_provider(self, name: str, provider_class: Type[EmbeddingProviderInterface]):
        """注册向量化服务"""
        self._embedding_providers[name] = provider_class
        logger.info(f"注册向量化服务: {name}")
    
    def register_vector_store(self, name: str, store_class: Type[VectorStoreInterface]):
        """注册向量存储"""
        self._vector_stores[name] = store_class
        logger.info(f"注册向量存储: {name}")
    
    def register_knowledge_graph(self, name: str, graph_class: Type[KnowledgeGraphInterface]):
        """注册知识图谱"""
        self._knowledge_graphs[name] = graph_class
        logger.info(f"注册知识图谱: {name}")
    
    def create_document_parser(self, name: Optional[str] = None) -> DocumentParserInterface:
        """创建文档解析器"""
        if name is None:
            name = self.config.get('document_parser', 'default')
        
        if name not in self._parsers:
            raise ValueError(f"未知的文档解析器: {name}")
        
        parser_class = self._parsers[name]
        parser = parser_class()
        
        # 应用配置
        parser_config = self.config.get('document_parser_config', {})
        parser.configure(**parser_config)
        
        return parser
    
    def create_embedding_provider(self, name: Optional[str] = None) -> EmbeddingProviderInterface:
        """创建向量化服务"""
        if name is None:
            name = self.config.get('embedding_provider', 'default')
        
        if name not in self._embedding_providers:
            raise ValueError(f"未知的向量化服务: {name}")
        
        provider_class = self._embedding_providers[name]
        provider = provider_class()
        
        # 应用配置
        embedding_config = self.config.get('embedding_config', {})
        provider.configure(**embedding_config)
        
        return provider
    
    def create_vector_store(self, name: Optional[str] = None) -> VectorStoreInterface:
        """创建向量存储"""
        if name is None:
            name = self.config.get('vector_store', 'default')
        
        if name not in self._vector_stores:
            raise ValueError(f"未知的向量存储: {name}")
        
        store_class = self._vector_stores[name]
        store = store_class()
        
        # 应用配置
        store_config = self.config.get('vector_store_config', {})
        store.configure(**store_config)
        
        return store
    
    def create_knowledge_graph(self, name: Optional[str] = None) -> KnowledgeGraphInterface:
        """创建知识图谱"""
        if name is None:
            name = self.config.get('knowledge_graph', 'default')
        
        if name not in self._knowledge_graphs:
            raise ValueError(f"未知的知识图谱: {name}")
        
        graph_class = self._knowledge_graphs[name]
        graph = graph_class()
        
        # 应用配置
        graph_config = self.config.get('knowledge_graph_config', {})
        graph.configure(**graph_config)
        
        return graph
    
    def list_available_components(self) -> Dict[str, list]:
        """列出可用组件"""
        return {
            'document_parser': list(self._parsers.keys()),
            'embedding_provider': list(self._embedding_providers.keys()),
            'vector_store': list(self._vector_stores.keys()),
            'knowledge_graph': list(self._knowledge_graphs.keys())
        }


# 全局工厂实例
_factory_instance: Optional[ComponentFactory] = None


def get_factory(config: Optional[Dict[str, Any]] = None) -> ComponentFactory:
    """获取全局工厂实例"""
    global _factory_instance
    if _factory_instance is None:
        if config is None:
            from config import get_default_config
            config = get_default_config()
        _factory_instance = ComponentFactory(config)
    return _factory_instance


def reset_factory():
    """重置工厂实例"""
    global _factory_instance
    _factory_instance = None