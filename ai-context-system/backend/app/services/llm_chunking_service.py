"""
LLM辅助文档分块服务
使用Qwen3-32B进行智能文档分块
"""

import asyncio
import re
import json
from typing import List, Dict, Any, Optional
import httpx
from app.models.database import DocumentType


class LLMChunkingService:
    """LLM辅助分块服务"""
    
    def __init__(self):
        self.api_url = "https://oneapi.sangfor.com/v1/chat/completions"
        self.api_key = "sk-KskGcDMEQWGncNHr6bE2Ee61F22b40F8A1C09c8b150968Ff"
        self.model = "qwen3-32b"
        self.timeout = 120.0  # 120秒超时
        
    async def chunk_document(
        self,
        content: str,
        doc_type: str,
        file_name: str = "",
        max_chunk_size: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        根据文档类型智能分块
        
        Args:
            content: 文档内容
            doc_type: 文档类型 (business_doc/demo_code/checklist)
            file_name: 文件名（用于代码语言识别）
            max_chunk_size: 最大块大小（字符数）
            
        Returns:
            分块列表，每个块包含: content, chunk_index, token_count, metadata
        """
        if not content or not content.strip():
            return []
        
        # 根据文档类型选择分块策略
        if doc_type == DocumentType.BUSINESS_DOC.value:
            return await self._chunk_business_doc(content, max_chunk_size)
        elif doc_type == DocumentType.DEMO_CODE.value:
            return await self._chunk_code(content, file_name, max_chunk_size)
        elif doc_type == DocumentType.CHECKLIST.value:
            return await self._chunk_checklist(content, max_chunk_size)
        else:
            # 默认策略：简单分段
            return self._chunk_simple(content, max_chunk_size)
    
    async def _chunk_business_doc(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """
        业务文档分块策略：按语义段落分块
        使用LLM识别语义边界
        """
        chunks = []
        
        # 如果内容较短，直接返回单块
        if len(content) <= max_chunk_size:
            return [{
                "content": content,
                "chunk_index": 0,
                "token_count": len(content) // 4,  # 粗略估算
                "metadata": {"strategy": "single_chunk", "type": "business_doc"}
            }]
        
        # 使用LLM分析语义段落
        try:
            semantic_chunks = await self._llm_semantic_split(content, max_chunk_size)
            
            for idx, chunk_content in enumerate(semantic_chunks):
                chunks.append({
                    "content": chunk_content,
                    "chunk_index": idx,
                    "token_count": len(chunk_content) // 4,
                    "metadata": {
                        "strategy": "llm_semantic",
                        "type": "business_doc"
                    }
                })
        except Exception as e:
            print(f"LLM分块失败，回退到简单分块: {e}")
            # 回退到基于段落的简单分块
            chunks = self._chunk_by_paragraphs(content, max_chunk_size)
        
        return chunks
    
    async def _chunk_code(
        self,
        content: str,
        file_name: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """
        代码文档分块策略：按函数/类分块
        保持代码结构完整性
        """
        chunks = []
        language = self._detect_language(file_name)
        
        # 如果内容较短，直接返回
        if len(content) <= max_chunk_size:
            return [{
                "content": content,
                "chunk_index": 0,
                "token_count": len(content) // 4,
                "metadata": {
                    "strategy": "single_chunk",
                    "type": "demo_code",
                    "language": language
                }
            }]
        
        # 根据编程语言特性分块
        if language in ["python", "py"]:
            chunks = self._chunk_python_code(content, max_chunk_size)
        elif language in ["javascript", "typescript", "js", "ts"]:
            chunks = self._chunk_js_code(content, max_chunk_size)
        elif language in ["java"]:
            chunks = self._chunk_java_code(content, max_chunk_size)
        elif language in ["go"]:
            chunks = self._chunk_go_code(content, max_chunk_size)
        else:
            # 通用代码分块：按空行或注释分隔
            chunks = self._chunk_generic_code(content, max_chunk_size)
        
        # 添加语言信息到metadata
        for chunk in chunks:
            chunk["metadata"]["language"] = language
        
        return chunks
    
    async def _chunk_checklist(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """
        Checklist分块策略：按规则项分块
        每个规则项作为独立块
        """
        chunks = []
        
        # 识别列表项模式
        # 支持格式: 1. / - / * / • / [] / 【】
        patterns = [
            r'\n\d+\.\s+',  # 数字列表: 1. 2. 3.
            r'\n-\s+',       # 破折号列表: - item
            r'\n\*\s+',      # 星号列表: * item
            r'\n•\s+',       # 圆点列表: • item
            r'\n\[\s*\]\s+', # 复选框: [] item
            r'\n【.*?】',     # 中文标题: 【标题】
        ]
        
        # 尝试按列表项分割
        items = self._split_by_patterns(content, patterns)
        
        if len(items) <= 1:
            # 如果没有识别到列表项，按段落分割
            items = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 合并小块，避免过小的chunk
        merged_items = []
        current_chunk = ""
        
        for item in items:
            if len(current_chunk) + len(item) <= max_chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + item
            else:
                if current_chunk:
                    merged_items.append(current_chunk)
                current_chunk = item
        
        if current_chunk:
            merged_items.append(current_chunk)
        
        # 创建chunks
        for idx, item_content in enumerate(merged_items):
            chunks.append({
                "content": item_content,
                "chunk_index": idx,
                "token_count": len(item_content) // 4,
                "metadata": {
                    "strategy": "checklist_items",
                    "type": "checklist",
                    "item_count": item_content.count('\n') + 1
                }
            })
        
        return chunks
    
    async def _llm_semantic_split(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[str]:
        """
        使用LLM进行语义分段
        """
        # 构造prompt让LLM识别语义边界
        prompt = f"""请将以下文档按语义段落分割，每个段落应该是一个完整的语义单元。
要求：
1. 每个段落长度尽量接近但不超过{max_chunk_size}字符
2. 保持语义完整性，不要在句子中间分割
3. 返回分割后的段落，用"===SPLIT==="标记分隔

文档内容：
{content[:8000]}  # 限制输入长度
"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的文档分析助手，擅长识别文档的语义结构。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 4000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_output = result["choices"][0]["message"]["content"]
                    
                    # 解析LLM输出
                    chunks = [chunk.strip() for chunk in llm_output.split("===SPLIT===") if chunk.strip()]
                    
                    # 如果分块太少，回退到段落分割
                    if len(chunks) < 2:
                        return self._split_by_paragraphs(content, max_chunk_size)
                    
                    return chunks
                else:
                    raise Exception(f"LLM API error: {response.status_code}")
                    
        except Exception as e:
            print(f"LLM semantic split failed: {e}")
            # 回退到段落分割
            return self._split_by_paragraphs(content, max_chunk_size)
    
    def _split_by_paragraphs(self, content: str, max_size: int) -> List[str]:
        """按段落分割文档"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks = []
        current = ""
        
        for para in paragraphs:
            if len(current) + len(para) <= max_size:
                current += ("\n\n" if current else "") + para
            else:
                if current:
                    chunks.append(current)
                current = para
        
        if current:
            chunks.append(current)
        
        return chunks if chunks else [content]
    
    def _chunk_by_paragraphs(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """基于段落的简单分块（回退策略）"""
        paragraph_chunks = self._split_by_paragraphs(content, max_chunk_size)
        
        return [
            {
                "content": chunk,
                "chunk_index": idx,
                "token_count": len(chunk) // 4,
                "metadata": {"strategy": "paragraph_fallback", "type": "business_doc"}
            }
            for idx, chunk in enumerate(paragraph_chunks)
        ]
    
    def _chunk_python_code(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """Python代码分块：按类和函数分割"""
        chunks = []
        
        # 正则匹配类和函数定义
        # 匹配: class ClassName: 或 def function_name():
        pattern = r'^(class\s+\w+.*?:|def\s+\w+.*?:)'
        
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        chunk_start_line = 0
        
        for i, line in enumerate(lines):
            # 检查是否是新的类或函数定义
            if re.match(pattern, line.strip()):
                # 如果当前块不为空且达到一定大小，保存
                if current_chunk and current_size > 100:  # 最小100字符
                    chunks.append({
                        "content": '\n'.join(current_chunk),
                        "chunk_index": len(chunks),
                        "token_count": current_size // 4,
                        "metadata": {
                            "strategy": "python_structure",
                            "type": "demo_code",
                            "start_line": chunk_start_line,
                            "end_line": i - 1
                        }
                    })
                    current_chunk = []
                    current_size = 0
                    chunk_start_line = i
            
            current_chunk.append(line)
            current_size += len(line)
            
            # 如果当前块超过最大大小，强制分割
            if current_size > max_chunk_size:
                chunks.append({
                    "content": '\n'.join(current_chunk),
                    "chunk_index": len(chunks),
                    "token_count": current_size // 4,
                    "metadata": {
                        "strategy": "python_structure",
                        "type": "demo_code",
                        "start_line": chunk_start_line,
                        "end_line": i
                    }
                })
                current_chunk = []
                current_size = 0
                chunk_start_line = i + 1
        
        # 添加最后一个块
        if current_chunk:
            chunks.append({
                "content": '\n'.join(current_chunk),
                "chunk_index": len(chunks),
                "token_count": current_size // 4,
                "metadata": {
                    "strategy": "python_structure",
                    "type": "demo_code",
                    "start_line": chunk_start_line,
                    "end_line": len(lines) - 1
                }
            })
        
        return chunks if chunks else self._chunk_simple(content, max_chunk_size)
    
    def _chunk_js_code(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """JavaScript/TypeScript代码分块"""
        chunks = []
        
        # 匹配: function name() / const name = / class Name / export
        pattern = r'^(function\s+\w+|const\s+\w+\s*=|let\s+\w+\s*=|class\s+\w+|export\s+)'
        
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        
        for line in lines:
            if re.match(pattern, line.strip()) and current_size > 100:
                if current_chunk:
                    chunks.append({
                        "content": '\n'.join(current_chunk),
                        "chunk_index": len(chunks),
                        "token_count": current_size // 4,
                        "metadata": {"strategy": "js_structure", "type": "demo_code"}
                    })
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(line)
            current_size += len(line)
            
            if current_size > max_chunk_size:
                if current_chunk:
                    chunks.append({
                        "content": '\n'.join(current_chunk),
                        "chunk_index": len(chunks),
                        "token_count": current_size // 4,
                        "metadata": {"strategy": "js_structure", "type": "demo_code"}
                    })
                    current_chunk = []
                    current_size = 0
        
        if current_chunk:
            chunks.append({
                "content": '\n'.join(current_chunk),
                "chunk_index": len(chunks),
                "token_count": current_size // 4,
                "metadata": {"strategy": "js_structure", "type": "demo_code"}
            })
        
        return chunks if chunks else self._chunk_simple(content, max_chunk_size)
    
    def _chunk_java_code(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """Java代码分块"""
        # 匹配: public/private class/interface/method
        pattern = r'^\s*(public|private|protected)?\s*(class|interface|enum|\w+\s+\w+\s*\()'
        return self._chunk_generic_code(content, max_chunk_size, pattern)
    
    def _chunk_go_code(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """Go代码分块"""
        # 匹配: func, type, const, var
        pattern = r'^(func\s+|type\s+|const\s+|var\s+)'
        return self._chunk_generic_code(content, max_chunk_size, pattern)
    
    def _chunk_generic_code(
        self,
        content: str,
        max_chunk_size: int,
        pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """通用代码分块：按空行分割"""
        # 按双空行分割代码块
        blocks = re.split(r'\n\s*\n', content)
        
        chunks = []
        current = ""
        
        for block in blocks:
            if not block.strip():
                continue
                
            if len(current) + len(block) <= max_chunk_size:
                current += ("\n\n" if current else "") + block
            else:
                if current:
                    chunks.append({
                        "content": current,
                        "chunk_index": len(chunks),
                        "token_count": len(current) // 4,
                        "metadata": {"strategy": "generic_code", "type": "demo_code"}
                    })
                current = block
        
        if current:
            chunks.append({
                "content": current,
                "chunk_index": len(chunks),
                "token_count": len(current) // 4,
                "metadata": {"strategy": "generic_code", "type": "demo_code"}
            })
        
        return chunks if chunks else self._chunk_simple(content, max_chunk_size)
    
    def _chunk_simple(
        self,
        content: str,
        max_chunk_size: int
    ) -> List[Dict[str, Any]]:
        """简单分块：固定大小切分"""
        chunks = []
        words = content.split()
        current = ""
        
        for word in words:
            if len(current) + len(word) + 1 <= max_chunk_size:
                current += (" " if current else "") + word
            else:
                if current:
                    chunks.append({
                        "content": current,
                        "chunk_index": len(chunks),
                        "token_count": len(current) // 4,
                        "metadata": {"strategy": "simple_split"}
                    })
                current = word
        
        if current:
            chunks.append({
                "content": current,
                "chunk_index": len(chunks),
                "token_count": len(current) // 4,
                "metadata": {"strategy": "simple_split"}
            })
        
        return chunks if chunks else [{
            "content": content,
            "chunk_index": 0,
            "token_count": len(content) // 4,
            "metadata": {"strategy": "simple_split"}
        }]
    
    def _detect_language(self, file_name: str) -> str:
        """从文件名检测编程语言"""
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ""
        
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'java': 'java',
            'go': 'go',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'rb': 'ruby',
            'php': 'php',
            'swift': 'swift',
            'kt': 'kotlin',
            'rs': 'rust',
        }
        
        return lang_map.get(ext, ext or 'unknown')
    
    def _split_by_patterns(
        self,
        content: str,
        patterns: List[str]
    ) -> List[str]:
        """使用多个正则模式分割文本"""
        # 尝试每个模式
        for pattern in patterns:
            parts = re.split(pattern, content)
            if len(parts) > 1:
                # 过滤空字符串，保留有内容的部分
                return [p.strip() for p in parts if p.strip()]
        
        # 如果所有模式都不匹配，返回原文
        return [content]


# 全局单例
_chunking_service = None


def get_chunking_service() -> LLMChunkingService:
    """获取分块服务单例"""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = LLMChunkingService()
    return _chunking_service
