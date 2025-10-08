"""
知识图谱接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Tuple, Optional
from langchain.schema import Document
import networkx as nx


class KnowledgeGraphInterface(ABC):
    """知识图谱抽象接口"""
    
    @abstractmethod
    def build_from_documents(self, documents: List[Document]) -> nx.Graph:
        """
        从文档列表构建知识图谱
        
        Args:
            documents: 文档列表
            
        Returns:
            构建的图对象
        """
        pass
    
    @abstractmethod
    def extract_keywords(self, text: str, max_keywords: int = None) -> List[str]:
        """
        提取文本关键词
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数
            
        Returns:
            关键词列表
        """
        pass
    
    @abstractmethod
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取图统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def find_related_keywords(self, keyword: str, max_results: int = 10) -> List[Tuple[str, float, str]]:
        """
        查找与给定关键词相关的其他关键词
        
        Args:
            keyword: 目标关键词
            max_results: 最大结果数
            
        Returns:
            (关键词, 权重, 关系类型) 的列表
        """
        pass
    
    @abstractmethod
    def find_related_documents(self, keyword: str) -> List[str]:
        """
        查找包含指定关键词的文档
        
        Args:
            keyword: 关键词
            
        Returns:
            文档ID列表
        """
        pass
    
    @abstractmethod
    def save_graph(self, filepath: str) -> None:
        """
        保存图到文件
        
        Args:
            filepath: 文件路径
        """
        pass
    
    @abstractmethod
    def load_graph(self, filepath: str) -> None:
        """
        从文件加载图
        
        Args:
            filepath: 文件路径
        """
        pass
    
    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        配置图构建参数
        
        Args:
            **kwargs: 配置参数
        """
        pass