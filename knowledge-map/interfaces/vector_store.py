"""
向量存储接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document


class VectorStoreInterface(ABC):
    """向量存储抽象接口"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            文档ID列表
        """
        pass
    
    @abstractmethod
    def similarity_search(self, 
                         query: str, 
                         k: int = 5,
                         filter_dict: Optional[Dict] = None) -> List[Tuple[Document, float]]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            (文档, 相似度分数) 的列表
        """
        pass
    
    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """
        获取集合信息
        
        Returns:
            集合信息字典
        """
        pass
    
    @abstractmethod
    def reset_collection(self) -> None:
        """
        重置集合（删除所有数据）
        """
        pass
    
    @abstractmethod
    def search_by_metadata(self, filter_dict: Dict, limit: int = 10) -> List[Document]:
        """
        根据元数据搜索文档
        
        Args:
            filter_dict: 过滤条件
            limit: 结果数量限制
            
        Returns:
            文档列表
        """
        pass
    
    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        配置存储参数
        
        Args:
            **kwargs: 配置参数
        """
        pass