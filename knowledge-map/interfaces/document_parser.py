"""
文档解析器接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain.schema import Document


class DocumentParserInterface(ABC):
    """文档解析器抽象接口"""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> List[Document]:
        """
        解析单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名
        
        Returns:
            支持的扩展名列表
        """
        pass
    
    @abstractmethod
    def is_supported(self, file_path: str) -> bool:
        """
        检查是否支持该文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        pass
    
    @abstractmethod
    def get_document_info(self, documents: List[Document]) -> Dict[str, Any]:
        """
        获取文档信息统计
        
        Args:
            documents: 文档列表
            
        Returns:
            文档信息字典
        """
        pass
    
    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        配置解析器参数
        
        Args:
            **kwargs: 配置参数
        """
        pass