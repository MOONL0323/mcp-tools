"""
默认文档解析器实现
支持PDF、Word、文本等多种格式，并集成代码解析功能
"""
import os
from typing import List, Dict, Any
from pathlib import Path
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader
)
from loguru import logger

from interfaces.document_parser import DocumentParserInterface
from implementations.parsers.code_parser_factory import code_parser_factory


class DefaultDocumentParser(DocumentParserInterface):
    """默认文档解析器实现"""
    
    def __init__(self):
        """初始化解析器"""
        self.chunk_size = 500
        self.chunk_overlap = 50
        self.supported_extensions = ['.pdf', '.docx', '.txt', '.md']
        self.text_splitter = None
        self._init_splitter()
        
        logger.info("默认文档解析器初始化完成")
    
    def _init_splitter(self):
        """初始化文本分割器"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )
    
    def parse_file(self, file_path: str) -> List[Document]:
        """
        解析单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"解析文件: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        # 优先检查是否为代码文件
        if code_parser_factory.is_supported(file_path):
            logger.info(f"使用代码解析器处理: {file_path}")
            return code_parser_factory.parse_file(file_path)
        
        # 检查是否为支持的文档文件
        if not self.is_supported(file_path):
            raise ValueError(f"不支持的文件类型: {file_path}")
        
        try:
            # 根据文件类型选择合适的加载器
            if file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_ext == '.docx':
                loader = Docx2txtLoader(file_path)
            elif file_ext in ['.txt', '.md']:
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                raise ValueError(f"不支持的文件扩展名: {file_ext}")
            
            # 加载文档
            documents = loader.load()
            
            # 分块处理
            split_documents = []
            for doc in documents:
                # 添加源文件信息
                doc.metadata.update({
                    'source_file': file_path,
                    'file_type': file_ext,
                    'file_size': os.path.getsize(file_path)
                })
                
                # 分割文档
                chunks = self.text_splitter.split_documents([doc])
                split_documents.extend(chunks)
            
            logger.info(f"文件解析完成，生成 {len(split_documents)} 个文档块")
            return split_documents
            
        except Exception as e:
            logger.error(f"文件解析失败 {file_path}: {str(e)}")
            raise
    
    def get_supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名
        
        Returns:
            支持的扩展名列表
        """
        return self.supported_extensions.copy()
    
    def is_supported(self, file_path: str) -> bool:
        """
        检查是否支持该文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        file_ext = Path(file_path).suffix.lower()
        
        # 检查代码文件
        if code_parser_factory.is_supported(file_path):
            return True
        
        # 检查文档文件
        return file_ext in self.supported_extensions
    
    def get_document_info(self, documents: List[Document]) -> Dict[str, Any]:
        """
        获取文档信息统计
        
        Args:
            documents: 文档列表
            
        Returns:
            文档信息字典
        """
        if not documents:
            return {"total_chunks": 0, "total_chars": 0, "avg_chunk_size": 0}
        
        total_chars = sum(len(doc.page_content) for doc in documents)
        avg_chunk_size = total_chars / len(documents) if documents else 0
        
        # 统计源文件
        source_files = set()
        for doc in documents:
            source_file = doc.metadata.get('source_file')
            if source_file:
                source_files.add(source_file)
        
        return {
            "total_chunks": len(documents),
            "total_chars": total_chars,
            "avg_chunk_size": round(avg_chunk_size, 2),
            "source_files": list(source_files),
            "source_file_count": len(source_files)
        }
    
    def configure(self, **kwargs) -> None:
        """
        配置解析器参数
        
        Args:
            **kwargs: 配置参数
        """
        if 'chunk_size' in kwargs:
            self.chunk_size = kwargs['chunk_size']
        
        if 'chunk_overlap' in kwargs:
            self.chunk_overlap = kwargs['chunk_overlap']
        
        if 'supported_extensions' in kwargs:
            self.supported_extensions = kwargs['supported_extensions']
        
        # 重新初始化分割器
        self._init_splitter()
        
        logger.info(f"文档解析器配置已更新: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")