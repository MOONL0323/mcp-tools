"""
文档解析器 - 支持多种格式的文档解析
"""

import os
from pathlib import Path
from typing import Optional
from loguru import logger
import PyPDF2
import docx
import markdown


class DocumentParser:
    """文档解析器"""
    
    @staticmethod
    async def parse_file(file_path: str) -> str:
        """
        根据文件类型解析文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档文本内容
        """
        file_ext = Path(file_path).suffix.lower()
        
        parsers = {
            '.txt': DocumentParser._parse_text,
            '.md': DocumentParser._parse_markdown,
            '.pdf': DocumentParser._parse_pdf,
            '.docx': DocumentParser._parse_docx,
            '.py': DocumentParser._parse_code,
            '.js': DocumentParser._parse_code,
            '.ts': DocumentParser._parse_code,
            '.java': DocumentParser._parse_code,
            '.go': DocumentParser._parse_code,
            '.cpp': DocumentParser._parse_code,
            '.c': DocumentParser._parse_code,
            '.h': DocumentParser._parse_code,
        }
        
        parser = parsers.get(file_ext, DocumentParser._parse_text)
        
        try:
            content = await parser(file_path)
            logger.info(f"成功解析文档: {file_path}, 长度: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"解析文档失败 {file_path}: {e}")
            raise
    
    @staticmethod
    async def _parse_text(file_path: str) -> str:
        """解析纯文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    async def _parse_markdown(file_path: str) -> str:
        """解析Markdown文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        # 保留原始markdown格式
        return md_content
    
    @staticmethod
    async def _parse_pdf(file_path: str) -> str:
        """解析PDF文件"""
        text_content = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
        return '\n\n'.join(text_content)
    
    @staticmethod
    async def _parse_docx(file_path: str) -> str:
        """解析Word文档"""
        doc = docx.Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs]
        return '\n\n'.join(paragraphs)
    
    @staticmethod
    async def _parse_code(file_path: str) -> str:
        """解析代码文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 添加代码文件的元信息
        file_name = Path(file_path).name
        file_ext = Path(file_path).suffix
        
        return f"""# 代码文件: {file_name}
# 类型: {file_ext}

{code}
"""


# 全局实例
document_parser = DocumentParser()
