"""
代码解析器工厂
根据文件类型自动选择合适的代码解析器
"""
import os
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from interfaces.code_parser import CodeParserInterface
from implementations.parsers.go_code_parser import GoCodeParser

class CodeParserFactory:
    """代码解析器工厂"""
    
    def __init__(self):
        self._parsers = {}
        self._extension_mapping = {}
        self._register_default_parsers()
    
    def _register_default_parsers(self):
        """注册默认的代码解析器"""
        # 注册Go解析器
        go_parser = GoCodeParser()
        self.register_parser('go', go_parser)
    
    def register_parser(self, language: str, parser: CodeParserInterface):
        """
        注册代码解析器
        
        Args:
            language: 编程语言名称 (如 'go', 'python', 'javascript')
            parser: 解析器实例
        """
        self._parsers[language] = parser
        
        # 注册文件扩展名映射
        for ext in parser.get_supported_extensions():
            self._extension_mapping[ext] = language
    
    def get_parser(self, file_path: str) -> Optional[CodeParserInterface]:
        """
        根据文件路径获取合适的解析器
        
        Args:
            file_path: 文件路径
            
        Returns:
            对应的解析器，如果不支持则返回None
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        language = self._extension_mapping.get(file_ext)
        
        if language:
            return self._parsers.get(language)
        
        return None
    
    def is_supported(self, file_path: str) -> bool:
        """
        检查文件是否支持代码解析
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        return self.get_parser(file_path) is not None
    
    def get_supported_extensions(self) -> List[str]:
        """
        获取所有支持的文件扩展名
        
        Returns:
            支持的扩展名列表
        """
        return list(self._extension_mapping.keys())
    
    def get_supported_languages(self) -> List[str]:
        """
        获取所有支持的编程语言
        
        Returns:
            支持的语言列表
        """
        return list(self._parsers.keys())
    
    def parse_file(self, file_path: str) -> List[Document]:
        """
        解析代码文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的文档列表
            
        Raises:
            ValueError: 文件类型不支持
            FileNotFoundError: 文件不存在
        """
        parser = self.get_parser(file_path)
        if not parser:
            file_ext = os.path.splitext(file_path)[1].lower()
            raise ValueError(f"不支持的文件类型: {file_ext}")
        
        return parser.parse_file(file_path)

# 全局工厂实例
code_parser_factory = CodeParserFactory()