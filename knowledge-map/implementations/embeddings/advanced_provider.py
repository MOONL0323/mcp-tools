"""
先进的开源embedding模型提供者
支持当前最佳的开源embedding模型，为AI Agent提供高质量的向量化服务
"""
import os
import torch
import numpy as np
from typing import List, Union, Dict, Any, Optional
from loguru import logger
import warnings
warnings.filterwarnings("ignore")

from interfaces.embedding_provider import EmbeddingProviderInterface


class AdvancedEmbeddingProvider(EmbeddingProviderInterface):
    """使用最先进开源模型的embedding服务"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化embedding服务"""
        self.config = config or {}
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.dimension = 768  # 默认维度
        self.model_name = None
        self.is_initialized = False
        self.batch_size = self.config.get('batch_size', 32)
        
        # 当前最先进的开源embedding模型（2024年）
        # 支持本地路径和在线模型
        self.model_configs = [
            # 本地模型（优先）
            {
                'name': './data/models/bge-large-zh-v1.5',
                'description': 'BGE大型中文模型(1024维) - 本地版',
                'dimension': 1024,
                'languages': ['zh', 'en'],
                'quality': 'excellent',
                'local': True
            },
            {
                'name': './data/models/bge-base-zh-v1.5',
                'description': 'BGE基础中文模型(768维) - 本地版',
                'dimension': 768,
                'languages': ['zh', 'en'],
                'quality': 'very_good',
                'local': True
            },
            {
                'name': './data/models/all-mpnet-base-v2',
                'description': 'MPNet全能模型(768维) - 本地版',
                'dimension': 768,
                'languages': ['en'],
                'quality': 'good',
                'local': True
            },
            # 在线模型（备用）
            {
                'name': 'BAAI/bge-large-zh-v1.5',
                'description': 'BGE大型中文模型(1024维) - 在线版',
                'dimension': 1024,
                'languages': ['zh', 'en'],
                'quality': 'excellent',
                'local': False
            },
            {
                'name': 'BAAI/bge-base-zh-v1.5',
                'description': 'BGE基础中文模型(768维) - 在线版',
                'dimension': 768,
                'languages': ['zh', 'en'],
                'quality': 'very_good',
                'local': False
            },
            {
                'name': 'sentence-transformers/all-mpnet-base-v2',
                'description': 'MPNet全能模型(768维) - 在线版',
                'dimension': 768,
                'languages': ['en'],
                'quality': 'good',
                'local': False
            }
        ]
        
        logger.info(f"初始化先进embedding服务，设备: {self.device}")
        self._load_best_available_model()

    def _load_best_available_model(self):
        """自动加载最佳可用模型，优先本地模型"""
        # 1. 检查是否有配置的本地模型
        local_models = self.config.get('local_models', {})
        prefer_local = self.config.get('prefer_local', True)
        
        if prefer_local and local_models:
            logger.info("🔍 检查本地模型...")
            for model_key, model_path in local_models.items():
                if self._check_local_model_exists(model_path):
                    logger.info(f"✅ 发现本地模型: {model_key} -> {model_path}")
                    if self._try_load_model(model_path):
                        self.model_name = model_path
                        logger.success(f"🎉 成功加载本地模型: {model_key}")
                        return
        
        # 2. 优先使用配置指定的模型
        specified_model = self.config.get('model_name')
        if specified_model:
            # 检查是否为本地路径
            if os.path.exists(specified_model):
                logger.info(f"尝试加载本地指定模型: {specified_model}")
                if self._try_load_model(specified_model):
                    self.model_name = specified_model
                    logger.success(f"✅ 成功加载本地指定模型")
                    return
            else:
                logger.info(f"尝试在线下载指定模型: {specified_model}")
                if self._try_load_model(specified_model):
                    self.model_name = specified_model
                    logger.success(f"✅ 成功下载并加载指定模型")
                    return
            logger.warning(f"指定模型 {specified_model} 加载失败，尝试其他模型")
        
        # 3. 按质量顺序尝试在线下载模型
        logger.info("🌐 尝试在线下载高级模型...")
        for model_config in self.model_configs:
            model_name = model_config['name']
            logger.info(f"尝试加载 {model_config['description']}")
            
            if self._try_load_model(model_name, model_config):
                self.model_name = model_name
                self.dimension = model_config['dimension']
                logger.success(f"✅ 成功加载 {model_config['description']}")
                logger.info(f"模型维度: {self.dimension}, 语言支持: {model_config['languages']}")
                return
        
        # 4. 如果都失败了，使用简单的fallback模型
        if self.config.get('enable_fallback', True):
            logger.warning("⚠️ 高级模型无法加载，使用离线fallback模型")
            if self._load_fallback_model():
                logger.info("✅ 成功加载离线fallback embedding模型")
                return
        
        logger.error("❌ 所有模型都无法加载，请检查网络连接或模型安装")
        logger.info("💡 建议操作:")
        logger.info("   1. 使用提供的下载脚本:")
        logger.info("      Windows: powershell -ExecutionPolicy Bypass -File download_bge_model.ps1")
        logger.info("      Linux/Mac: ./download_bge_model.sh")
        logger.info("   2. 或手动下载，参考 MANUAL_DOWNLOAD.md")
        logger.info("   3. 或临时使用TF-IDF模型进行测试")
        raise RuntimeError("无法加载任何embedding模型")

    def _check_local_model_exists(self, model_path: str) -> bool:
        """检查本地模型是否存在且完整"""
        if not os.path.exists(model_path):
            return False
        
        # 检查必需文件
        required_files = [
            'config.json',
            'pytorch_model.bin',
            'tokenizer.json',
            'tokenizer_config.json',
            'vocab.txt'
        ]
        
        for file_name in required_files:
            file_path = os.path.join(model_path, file_name)
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                logger.debug(f"本地模型缺少文件: {file_path}")
                return False
        
        logger.debug(f"本地模型文件完整: {model_path}")
        return True

    def _load_fallback_model(self) -> bool:
        """加载离线fallback模型"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import jieba
            import pickle
            import os
            
            logger.info("初始化TF-IDF fallback模型...")
            
            # 创建TF-IDF向量化器
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=768,  # 设置固定维度
                stop_words=None,
                tokenizer=self._chinese_tokenizer,
                lowercase=True,
                ngram_range=(1, 2)
            )
            
            # 初始化状态
            self.is_initialized = True
            self.model_name = "TF-IDF-Fallback"
            self.dimension = 768
            self.is_tfidf_model = True
            
            # 创建初始词汇表
            sample_texts = [
                "这是一个测试文档",
                "人工智能和机器学习",
                "数据科学和算法",
                "编程和软件开发",
                "This is a test document",
                "Artificial intelligence and machine learning"
            ]
            
            # 训练TF-IDF模型
            self.tfidf_vectorizer.fit(sample_texts)
            
            logger.info(f"TF-IDF fallback模型加载成功，维度: {self.dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Fallback模型加载失败: {e}")
            return False

    def _chinese_tokenizer(self, text: str):
        """中文分词器"""
        try:
            import jieba
            return list(jieba.cut(text))
        except ImportError:
            # 如果jieba不可用，使用简单分割
            return text.split()

    def _try_load_model(self, model_name: str, model_config: Dict = None) -> bool:
        """尝试加载指定模型"""
        try:
            # 检查是否为本地路径
            if model_name.startswith('./') or model_name.startswith('../'):
                import os
                if not os.path.exists(model_name):
                    logger.debug(f"本地模型路径不存在: {model_name}")
                    return False
                logger.info(f"尝试加载本地模型: {model_name}")
            else:
                logger.info(f"尝试加载在线模型: {model_name}")
            
            # 方法1: 使用sentence-transformers（推荐）
            if self._load_with_sentence_transformers(model_name):
                return True
            
            # 方法2: 使用huggingface transformers
            if self._load_with_transformers(model_name):
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"加载模型 {model_name} 失败: {e}")
            return False

    def _load_with_sentence_transformers(self, model_name: str) -> bool:
        """使用sentence-transformers加载"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # 配置模型加载参数
            device = str(self.device)
            trust_remote_code = True
            
            # 如果是本地路径，使用绝对路径
            if os.path.exists(model_name):
                model_path = os.path.abspath(model_name)
                logger.info(f"加载本地模型: {model_path}")
            else:
                model_path = model_name
                logger.info(f"加载在线模型: {model_path}")
            
            # 尝试加载模型
            try:
                self.model = SentenceTransformer(
                    model_path, 
                    device=device,
                    trust_remote_code=trust_remote_code
                )
            except:
                # 如果sentence-transformers失败，使用transformers库
                return self._load_with_transformers_fallback(model_path)
            
            # 测试模型并获取实际维度
            test_embedding = self.model.encode(["测试文本"], convert_to_numpy=True)
            self.dimension = test_embedding.shape[1]
            self.is_initialized = True
            
            logger.info(f"sentence-transformers加载成功，实际维度: {self.dimension}")
            return True
            
        except ImportError:
            logger.debug("sentence-transformers未安装")
            return False
        except Exception as e:
            logger.debug(f"sentence-transformers加载失败: {e}")
            return False

    def _load_with_transformers_fallback(self, model_path: str) -> bool:
        """使用transformers作为fallback加载本地模型"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            logger.info("尝试使用transformers库加载本地模型...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            self.model = AutoModel.from_pretrained(model_path, trust_remote_code=True)
            self.model.to(self.device)
            self.model.eval()
            
            # 测试获取维度
            with torch.no_grad():
                test_inputs = self.tokenizer("测试文本", return_tensors="pt", padding=True, truncation=True)
                test_inputs = {k: v.to(self.device) for k, v in test_inputs.items()}
                outputs = self.model(**test_inputs)
                self.dimension = outputs.last_hidden_state.shape[-1]
            
            self.is_initialized = True
            self.is_transformers_model = True  # 标记为transformers模型
            logger.info(f"transformers加载成功，维度: {self.dimension}")
            return True
            
        except Exception as e:
            logger.debug(f"transformers fallback加载失败: {e}")
            return False

    def _load_with_transformers(self, model_name: str) -> bool:
        """使用transformers直接加载"""
        try:
            from transformers import AutoTokenizer, AutoModel
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
            self.model.to(self.device)
            self.model.eval()
            
            # 测试获取维度
            with torch.no_grad():
                test_inputs = self.tokenizer("测试文本", return_tensors="pt", padding=True, truncation=True)
                test_inputs = {k: v.to(self.device) for k, v in test_inputs.items()}
                outputs = self.model(**test_inputs)
                self.dimension = outputs.last_hidden_state.shape[-1]
            
            self.is_initialized = True
            logger.info(f"transformers加载成功，维度: {self.dimension}")
            return True
            
        except Exception as e:
            logger.debug(f"transformers加载失败: {e}")
            return False

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文本"""
        if not self.is_initialized or not texts:
            return []
        
        try:
            # 检查是否为TF-IDF fallback模型
            if hasattr(self, 'is_tfidf_model') and self.is_tfidf_model:
                return self._embed_with_tfidf(texts)
            
            # 检查是否为transformers模型
            if hasattr(self, 'is_transformers_model') and self.is_transformers_model:
                return self._embed_with_transformers(texts)
            
            # sentence-transformers方式
            if hasattr(self.model, 'encode'):
                embeddings = self.model.encode(
                    texts, 
                    convert_to_numpy=True,
                    batch_size=self.batch_size,
                    show_progress_bar=len(texts) > 100
                )
                return embeddings.tolist()
            else:
                # transformers方式
                return self._embed_with_transformers(texts)
                
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            return []

    def _embed_with_tfidf(self, texts: List[str]) -> List[List[float]]:
        """使用TF-IDF进行向量化"""
        try:
            # 将文本转换为TF-IDF向量
            tfidf_matrix = self.tfidf_vectorizer.transform(texts)
            
            # 转换为密集矩阵并填充到固定维度
            dense_matrix = tfidf_matrix.toarray()
            
            # 如果维度不足，用零填充
            if dense_matrix.shape[1] < self.dimension:
                padding = np.zeros((dense_matrix.shape[0], self.dimension - dense_matrix.shape[1]))
                dense_matrix = np.concatenate([dense_matrix, padding], axis=1)
            elif dense_matrix.shape[1] > self.dimension:
                # 如果维度过多，截断
                dense_matrix = dense_matrix[:, :self.dimension]
            
            return dense_matrix.tolist()
            
        except Exception as e:
            logger.error(f"TF-IDF向量化失败: {e}")
            # 返回随机向量作为最后的fallback
            return [[0.0] * self.dimension for _ in texts]

    def _embed_with_transformers(self, texts: List[str]) -> List[List[float]]:
        """使用transformers进行向量化"""
        embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            with torch.no_grad():
                inputs = self.tokenizer(
                    batch_texts, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True,
                    max_length=512
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                outputs = self.model(**inputs)
                # 使用池化策略获取句子向量
                batch_embeddings = self._pool_embeddings(outputs.last_hidden_state, inputs['attention_mask'])
                embeddings.extend(batch_embeddings.cpu().numpy().tolist())
        
        return embeddings

    def _pool_embeddings(self, last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """池化策略获取句子级向量"""
        # 使用mean pooling
        masked_embeddings = last_hidden_state * attention_mask.unsqueeze(-1)
        summed_embeddings = masked_embeddings.sum(dim=1)
        counts = attention_mask.sum(dim=1, keepdim=True).float()
        mean_embeddings = summed_embeddings / counts
        
        # L2标准化
        return torch.nn.functional.normalize(mean_embeddings, p=2, dim=1)

    def embed_query(self, query: str) -> List[float]:
        """向量化单个查询"""
        result = self.embed_texts([query])
        return result[0] if result else []

    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'device': str(self.device),
            'is_initialized': self.is_initialized,
            'batch_size': self.batch_size
        }

    def cleanup(self):
        """清理资源"""
        if self.model is not None:
            del self.model
        if self.tokenizer is not None:
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Embedding provider已清理")

    # 实现抽象接口方法
    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """将文本编码为向量"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.embed_texts(texts)
        return np.array(embeddings)
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.is_initialized and self.model is not None
    
    def configure(self, **kwargs) -> None:
        """配置模型参数"""
        self.config.update(kwargs)
        self.batch_size = self.config.get('batch_size', 32)
        
        # 如果指定了新模型，重新加载
        if 'model_name' in kwargs:
            self._load_best_available_model()