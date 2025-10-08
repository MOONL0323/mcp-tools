"""
向量化服务接口
"""
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
import numpy as np


class EmbeddingProviderInterface(ABC):
    """向量化服务抽象接口"""
    
    @abstractmethod
    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        将文本编码为向量
        
        Args:
            texts: 单个文本或文本列表
            batch_size: 批处理大小
            
        Returns:
            向量数组
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        获取向量维度
        
        Returns:
            向量维度
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查模型是否可用
        
        Returns:
            是否可用
        """
        pass
    
    @abstractmethod
    def configure(self, **kwargs) -> None:
        """
        配置模型参数
        
        Args:
            **kwargs: 配置参数
        """
        pass