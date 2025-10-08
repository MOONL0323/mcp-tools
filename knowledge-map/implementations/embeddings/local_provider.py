"""
使用开源embedding模型的本地实现
支持多种开源模型，完全离线运行
"""
import os
import torch
import numpy as np
from typing import List, Union, Dict, Any
from loguru import logger

from interfaces.embedding_provider import EmbeddingProviderInterface


class LocalEmbeddingProvider(EmbeddingProviderInterface):
    """使用开源模型的本地向量化服务"""
    
    def __init__(self):
        """初始化向量化服务"""
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dimension = 384  # 默认维度，会根据实际模型调整
        self.model_name = None
        self.is_initialized = False
        
        logger.info(f"本地向量化服务初始化，使用设备: {self.device}")
        self._load_model()

    def _load_model(self):
        """加载当前最先进的开源embedding模型"""
        # 当前最高级的开源模型（按优先级排序）
        high_end_models = [
            (r"D:/huggingface_models/BAAI/bge-large-zh-v1.5", "BGE大型中文模型(1024维)"),
            (r"D:/huggingface_models/BAAI/bge-large-en-v1.5", "BGE大型英文模型(1024维)"),
            (r"D:/huggingface_models/BAAI/bge-base-zh-v1.5", "BGE基础中文模型(768维)"),
            (r"D:/huggingface_models/sentence-transformers/all-mpnet-base-v2", "MPNet全能模型(768维)"),
            (r"D:/huggingface_models/shibing624/text2vec-large-chinese", "Text2Vec大型中文模型(1024维)"),
            (r"D:/huggingface_models/shibing624/text2vec-base-chinese", "Text2Vec基础中文模型(768维)"),
        ]
        
        # 尝试加载最高级的可用模型
        for model_path, description in high_end_models:
            if os.path.exists(model_path):
                try:
                    logger.info(f"尝试加载{description}: {model_path}")
                    success = self._try_load_model(model_path)
                    if success:
                        self.model_name = model_path
                        logger.info(f"✅ 成功加载{description}，向量维度: {self.dimension}")
                        return
                except Exception as e:
                    logger.warning(f"无法加载 {model_path}: {e}")
        
        # 如果所有高级模型都不可用，使用TF-IDF fallback
        logger.warning("⚠️ 未找到任何高级embedding模型，使用简化的TF-IDF方法")
        logger.info("💡 建议下载BGE模型以获得最佳效果: https://huggingface.co/BAAI/bge-large-zh-v1.5")
        self._init_simple_tfidf()
        self.is_initialized = True

    def _try_load_model(self, model_name: str) -> bool:
        """尝试加载指定模型"""
        try:
            # 方法1: 尝试使用sentence-transformers
            if self._load_with_sentence_transformers(model_name):
                return True
            
            # 方法2: 尝试使用transformers
            if self._load_with_transformers(model_name):
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"加载模型 {model_name} 失败: {e}")
            return False

    def _load_with_sentence_transformers(self, model_name: str) -> bool:
        """使用sentence-transformers加载模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # 先尝试不设置离线模式（允许首次下载）
            try:
                self.model = SentenceTransformer(model_name, device=self.device)
            except Exception as e:
                # 如果失败，尝试离线模式
                logger.warning(f"联网加载失败，尝试离线模式: {e}")
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                self.model = SentenceTransformer(model_name, device=self.device)
            
            # 测试模型并获取维度
            test_embedding = self.model.encode(["test"], convert_to_numpy=True)
            self.dimension = test_embedding.shape[1]
            
            self.is_initialized = True
            logger.info(f"使用sentence-transformers加载成功，维度: {self.dimension}")
            return True
            
        except ImportError:
            logger.debug("sentence-transformers未安装")
            return False
        except Exception as e:
            logger.debug(f"sentence-transformers加载失败: {e}")
            return False

    def _load_with_transformers(self, model_name: str) -> bool:
        """使用transformers加载模型"""
        try:
            from transformers import AutoTokenizer, AutoModel
            
            # 设置离线模式
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.model.eval()
            
            # 测试模型并获取维度
            with torch.no_grad():
                test_inputs = self.tokenizer("test", return_tensors="pt", 
                                           padding=True, truncation=True, max_length=512)
                test_inputs = {k: v.to(self.device) for k, v in test_inputs.items()}
                outputs = self.model(**test_inputs)
                # 使用[CLS]标记的输出或池化输出
                if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                    test_embedding = outputs.pooler_output
                else:
                    test_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] token
                
                self.dimension = test_embedding.shape[1]
            
            self.is_initialized = True
            logger.info(f"使用transformers加载成功，维度: {self.dimension}")
            return True
            
        except ImportError:
            logger.debug("transformers未安装")
            return False
        except Exception as e:
            logger.debug(f"transformers加载失败: {e}")
            return False

    def _init_simple_tfidf(self):
        """初始化简单的TF-IDF向量化方法（完全离线）"""
        try:
            import jieba
            self.model = "simple_tfidf"
            self.dimension = 256  # 固定维度
            self.vocab = {}  # 词汇表
            self.idf_weights = {}  # IDF权重
            logger.info(f"初始化简化TF-IDF方法，维度: {self.dimension}")
        except ImportError:
            logger.error("需要安装 jieba: pip install jieba")
            raise ImportError("需要安装 jieba: pip install jieba")

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """编码文本为向量"""
        if not self.is_initialized:
            raise RuntimeError("模型未初始化")
        
        if isinstance(texts, str):
            texts = [texts]
        
        # 使用简单TF-IDF方法
        if self.model == "simple_tfidf":
            return self._encode_with_simple_tfidf(texts)
        
        # 使用sentence-transformers
        if hasattr(self.model, 'encode'):
            try:
                embeddings = self.model.encode(texts, batch_size=batch_size, 
                                             convert_to_numpy=True, 
                                             show_progress_bar=False)
                return embeddings.astype(np.float32)
            except Exception as e:
                logger.error(f"sentence-transformers编码失败: {e}")
                raise
        
        # 使用transformers
        elif self.tokenizer is not None:
            return self._encode_with_transformers(texts, batch_size)
        
        else:
            raise RuntimeError("无可用的编码方法")

    def _encode_with_transformers(self, texts: List[str], batch_size: int) -> np.ndarray:
        """使用transformers进行编码"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # 分词
            inputs = self.tokenizer(batch_texts, return_tensors="pt", 
                                  padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # 获取句子表示
                if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                    batch_embeddings = outputs.pooler_output
                else:
                    # 使用[CLS]标记或平均池化
                    batch_embeddings = outputs.last_hidden_state[:, 0, :]  # [CLS] token
                
                embeddings.append(batch_embeddings.cpu().numpy())
        
        return np.vstack(embeddings).astype(np.float32)

    def _encode_with_simple_tfidf(self, texts: List[str]) -> np.ndarray:
        """使用简单的TF-IDF方法编码文本"""
        import jieba
        import math
        from collections import Counter
        
        embeddings = []
        
        for text in texts:
            # 中文分词
            words = list(jieba.cut(text))
            
            # 计算词频 (TF)
            word_count = Counter(words)
            total_words = len(words)
            
            # 创建固定维度的向量
            vector = np.zeros(self.dimension, dtype=np.float32)
            
            for word, count in word_count.items():
                # 计算TF
                tf = count / total_words if total_words > 0 else 0
                
                # 使用词汇的哈希值映射到向量位置
                hash_val = hash(word)
                idx = hash_val % self.dimension
                
                # 简单累加（可以考虑使用更复杂的方法）
                vector[idx] += tf
            
            # 归一化
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            embeddings.append(vector)
        
        return np.array(embeddings, dtype=np.float32)

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.model_name or "Unknown",
            "type": "Transformer-based Embedding",
            "dimension": self.dimension,
            "device": self.device,
            "is_offline": True,
            "initialized": self.is_initialized
        }

    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.is_initialized

    def configure(self, **kwargs) -> None:
        """配置模型参数"""
        if 'device' in kwargs:
            self.device = kwargs['device']
            # 只有真正的PyTorch模型才需要移动到设备
            if self.model is not None and hasattr(self.model, 'to') and self.model != "simple_tfidf":
                self.model = self.model.to(self.device)
            logger.info(f"设置设备为: {self.device}")

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        # 确保向量是1维的
        if vec1.ndim > 1:
            vec1 = vec1.flatten()
        if vec2.ndim > 1:
            vec2 = vec2.flatten()
        
        # 计算余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)