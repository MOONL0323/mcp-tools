"""
代码解析器接口定义
为不同编程语言提供统一的解析接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain.schema import Document

class CodeParserInterface(ABC):
    """代码解析器基础接口"""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> List[Document]:
        """
        解析代码文件
        
        Args:
            file_path: 代码文件路径
            
        Returns:
            解析后的文档列表
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名列表
        
        Returns:
            支持的文件扩展名列表，如 ['.go', '.py', '.js']
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        提取代码文件的元数据
        
        Args:
            content: 文件内容
            file_path: 文件路径
            
        Returns:
            元数据字典
        """
        pass

class CodeStructureExtractorInterface(ABC):
    """代码结构提取器接口"""
    
    @abstractmethod
    def extract_functions(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取函数/方法"""
        pass
    
    @abstractmethod
    def extract_classes_or_structs(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取类/结构体"""
        pass
    
    @abstractmethod
    def extract_interfaces(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取接口"""
        pass
    
    @abstractmethod
    def extract_imports(self, content: str) -> List[str]:
        """提取导入/依赖"""
        pass
    
    @abstractmethod
    def extract_comments(self, content: str, position: int) -> List[str]:
        """提取特定位置的注释"""
        pass

class DocumentGeneratorInterface(ABC):
    """文档生成器接口"""
    
    @abstractmethod
    def generate_function_document(self, func_info: Dict[str, Any], file_path: str) -> Document:
        """生成函数文档"""
        pass
    
    @abstractmethod
    def generate_class_document(self, class_info: Dict[str, Any], file_path: str) -> Document:
        """生成类/结构体文档"""
        pass
    
    @abstractmethod
    def generate_interface_document(self, interface_info: Dict[str, Any], file_path: str) -> Document:
        """生成接口文档"""
        pass
    
    @abstractmethod
    def generate_file_overview_document(self, metadata: Dict[str, Any], file_path: str) -> Document:
        """生成文件概览文档"""
        pass