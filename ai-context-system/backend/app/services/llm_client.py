"""
LLM API 客户端
支持Qwen3-32B和Qwen3-Embedding-8B模型调用
"""

import httpx
import json
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.graphrag_config import graph_rag_settings


class LLMClient:
    """LLM API客户端"""
    
    def __init__(self):
        self.api_key = graph_rag_settings.llm_api_key
        self.base_url = graph_rag_settings.llm_api_base
        self.model = graph_rag_settings.llm_chat_model
        self.embedding_model = graph_rag_settings.llm_embedding_model
        self.temperature = graph_rag_settings.llm_temperature
        self.max_tokens = graph_rag_settings.llm_max_tokens
        
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        调用聊天补全API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            model: 模型名称
            
        Returns:
            模型回复内容
        """
        try:
            payload = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.debug(f"LLM响应: {content[:200]}...")
            return content
            
        except Exception as e:
            logger.error(f"LLM API调用失败: {e}")
            raise
    
    async def embedding(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        调用Embedding API
        
        Args:
            texts: 文本列表
            model: 模型名称
            
        Returns:
            向量列表
        """
        try:
            payload = {
                "model": model or self.embedding_model,
                "input": texts
            }
            
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]
            
            logger.debug(f"成功生成 {len(embeddings)} 个向量")
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding API调用失败: {e}")
            raise
    
    async def extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取JSON
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            解析后的JSON对象
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取```json```代码块
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 尝试提取```代码块
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"无法从文本中提取JSON: {text[:200]}...")
        return {}
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局LLM客户端实例
llm_client = LLMClient()
