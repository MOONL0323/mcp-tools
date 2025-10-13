"""
智能文档分块服务
使用LLM辅助进行语义感知的文档分块
"""

import json
from typing import List, Dict, Any
from loguru import logger
from app.services.llm_client import llm_client
from app.core.graphrag_config import graph_rag_settings


class DocumentChunk:
    """文档块数据结构"""
    
    def __init__(
        self,
        content: str,
        title: str = "",
        summary: str = "",
        keywords: List[str] = None,
        chunk_type: str = "text",
        start_pos: int = 0,
        end_pos: int = 0,
        metadata: Dict[str, Any] = None
    ):
        self.content = content
        self.title = title
        self.summary = summary
        self.keywords = keywords or []
        self.chunk_type = chunk_type
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.metadata = metadata or {}


class IntelligentChunker:
    """智能文档分块器"""
    
    async def chunk_document(
        self,
        content: str,
        document_type: str = "business_doc",
        enable_llm: bool = True
    ) -> List[DocumentChunk]:
        """
        智能分块文档
        
        Args:
            content: 文档内容
            document_type: 文档类型 (business_doc/demo_code)
            enable_llm: 是否启用LLM辅助分块
            
        Returns:
            文档块列表
        """
        try:
            if enable_llm and graph_rag_settings.enable_llm_chunking:
                # 先分析文档结构
                structure = await self._analyze_structure(content, document_type)
                
                # 基于结构进行智能分块
                chunks = await self._intelligent_chunk(content, structure)
            else:
                # 简单分块
                chunks = await self._simple_chunk(content)
            
            # 为每个chunk生成增强信息
            enhanced_chunks = []
            for chunk in chunks:
                if enable_llm:
                    enhanced = await self._enhance_chunk(chunk)
                    enhanced_chunks.append(enhanced)
                else:
                    enhanced_chunks.append(chunk)
            
            logger.info(f"文档分块完成，共 {len(enhanced_chunks)} 个块")
            return enhanced_chunks
            
        except Exception as e:
            logger.error(f"文档分块失败: {e}")
            # 降级到简单分块
            return await self._simple_chunk(content)
    
    async def _analyze_structure(
        self,
        content: str,
        document_type: str
    ) -> Dict[str, Any]:
        """分析文档结构"""
        prompt = f"""分析以下{"业务文档" if document_type == "business_doc" else "代码文档"}的结构，识别主要章节和逻辑块。

文档内容（前2000字符）:
{content[:2000]}

请以JSON格式返回结构分析，包含：
1. document_type: 文档具体类型（如：API文档、设计文档、代码示例等）
2. main_sections: 主要章节列表
3. logical_blocks: 建议的逻辑分块位置
4. key_concepts: 关键概念列表

返回格式：
```json
{{
  "document_type": "文档类型",
  "main_sections": ["章节1", "章节2"],
  "logical_blocks": [
    {{"start": 0, "end": 100, "topic": "主题"}}
  ],
  "key_concepts": ["概念1", "概念2"]
}}
```"""
        
        try:
            response = await llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            structure = await llm_client.extract_json_from_text(response)
            return structure
        except Exception as e:
            logger.warning(f"结构分析失败，使用默认结构: {e}")
            return {
                "document_type": "unknown",
                "main_sections": [],
                "logical_blocks": [],
                "key_concepts": []
            }
    
    async def _intelligent_chunk(
        self,
        content: str,
        structure: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """基于结构的智能分块"""
        chunks = []
        
        # 如果有逻辑块建议，使用它们
        if structure.get("logical_blocks"):
            for block in structure["logical_blocks"]:
                chunk_content = content[block["start"]:block["end"]]
                if len(chunk_content.strip()) > 50:  # 过滤太短的块
                    chunks.append(DocumentChunk(
                        content=chunk_content,
                        title=block.get("topic", ""),
                        start_pos=block["start"],
                        end_pos=block["end"]
                    ))
        else:
            # 使用固定大小分块
            chunks = await self._simple_chunk(content)
        
        return chunks
    
    async def _simple_chunk(self, content: str) -> List[DocumentChunk]:
        """简单固定大小分块"""
        chunk_size = graph_rag_settings.chunk_size
        overlap = graph_rag_settings.chunk_overlap
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk_content = content[start:end]
            
            chunks.append(DocumentChunk(
                content=chunk_content,
                start_pos=start,
                end_pos=end
            ))
            
            start = end - overlap
        
        return chunks
    
    async def _enhance_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """使用LLM增强chunk信息"""
        prompt = f"""为以下文档片段生成元信息：

内容：
{chunk.content[:500]}

请以JSON格式返回：
1. title: 简短标题（10字以内）
2. summary: 简洁摘要（50字以内）
3. keywords: 3-5个关键词
4. chunk_type: 内容类型（concept/code/api/design/other）

返回格式：
```json
{{
  "title": "标题",
  "summary": "摘要",
  "keywords": ["关键词1", "关键词2"],
  "chunk_type": "类型"
}}
```"""
        
        try:
            response = await llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            enhancement = await llm_client.extract_json_from_text(response)
            
            chunk.title = enhancement.get("title", "")
            chunk.summary = enhancement.get("summary", "")
            chunk.keywords = enhancement.get("keywords", [])
            chunk.chunk_type = enhancement.get("chunk_type", "text")
            
        except Exception as e:
            logger.warning(f"Chunk增强失败: {e}")
        
        return chunk


# 全局实例
intelligent_chunker = IntelligentChunker()
