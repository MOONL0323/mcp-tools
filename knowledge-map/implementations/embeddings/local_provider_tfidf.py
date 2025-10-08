"""
完全离线的本地向量化服务实现
使用TF-IDF和简单的词向量技术，不需要下载任何模型
"""
import os
import re
import math
import hashlib
from typing import List, Union, Dict, Any
import numpy as np
from collections import Counter, defaultdict
from loguru import logger

from interfaces.embedding_provider import EmbeddingProviderInterface


class LocalEmbeddingProvider(EmbeddingProviderInterface):
    """完全离线的本地向量化服务实现"""
    
    def __init__(self):
        """初始化向量化服务"""
        self.dimension = 256  # 固定维度
        self.vocab = {}  # 词汇表 {word: index}
        self.idf_weights = {}  # IDF权重 {word: weight}
        self.word_vectors = {}  # 词向量 {word: vector}
        self.is_initialized = False
        
        # 预定义停用词
        self.stop_words = set([
            # 中文停用词
            '的', '是', '在', '了', '有', '和', '我', '你', '他', '她', '它', '这', '那', '一个', '不是', '就是', 
            '可以', '没有', '要', '会', '对', '上', '下', '中', '也', '都', '很', '还', '就', '只', '能', '从', 
            '到', '把', '被', '让', '使', '用', '与', '或', '而', '但', '如果', '因为', '所以', '因此', '然后',
            # 英文停用词
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 
            'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have', 
            'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how', 'their', 'if', 'up', 'out', 'many', 
            'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'into', 'him', 'time', 'two'
        ])
        
        logger.info("完全离线的本地向量化服务初始化完成")

    def _tokenize(self, text: str) -> List[str]:
        """分词函数，支持中英文"""
        # 先用正则表达式提取英文单词
        english_words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', text)
        
        # 再处理中文
        try:
            import jieba
            # 使用jieba分词处理中文
            chinese_words = [w for w in jieba.cut(text) if re.search(r'[\u4e00-\u9fff]', w)]
        except ImportError:
            chinese_words = []
        
        # 合并所有词汇
        all_words = english_words + chinese_words
        
        # 过滤停用词和短词
        filtered_words = []
        for word in all_words:
            word = word.strip().lower()
            if (len(word) >= 2 and 
                word not in self.stop_words and 
                not word.isdigit()):
                filtered_words.append(word)
        
        return filtered_words

    def _generate_word_vector(self, word: str) -> np.ndarray:
        """为单词生成简单的向量表示"""
        # 使用词的hash值生成伪随机但一致的向量
        hash_value = int(hashlib.md5(word.encode()).hexdigest(), 16)
        np.random.seed(hash_value % (2**32))  # 确保可重现
        vector = np.random.normal(0, 1, self.dimension)
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.astype(np.float32)

    def build_vocabulary_from_corpus(self, all_texts: List[str]):
        """从语料库构建词汇表和IDF权重"""
        logger.info(f"正在从{len(all_texts)}个文档构建离线词汇表...")
        
        # 统计词频和文档频率
        doc_count = len(all_texts)
        word_doc_freq = Counter()  # 词在多少文档中出现
        word_total_freq = Counter()  # 词的总频次
        
        for text in all_texts:
            words = self._tokenize(text)
            word_total_freq.update(words)
            # 统计该文档中出现的唯一词
            unique_words = set(words)
            word_doc_freq.update(unique_words)
        
        # 选择重要词汇
        important_words = []
        for word, doc_freq in word_doc_freq.items():
            # 过滤条件：出现在至少2个文档中，但不超过80%的文档
            if doc_freq >= 2 and doc_freq <= doc_count * 0.8:
                total_freq = word_total_freq[word]
                # 计算重要性得分 (结合文档频率和总频率)
                importance = total_freq * math.log(doc_count / doc_freq)
                important_words.append((word, importance))
        
        # 按重要性排序，选择top词汇
        important_words.sort(key=lambda x: x[1], reverse=True)
        selected_words = [word for word, score in important_words[:self.dimension]]
        
        # 构建词汇表
        self.vocab = {word: idx for idx, word in enumerate(selected_words)}
        
        # 计算IDF权重
        self.idf_weights = {}
        for word in selected_words:
            doc_freq = word_doc_freq[word]
            idf = math.log(doc_count / doc_freq)
            self.idf_weights[word] = idf
        
        # 生成词向量
        self.word_vectors = {}
        for word in selected_words:
            self.word_vectors[word] = self._generate_word_vector(word)
        
        self.is_initialized = True
        logger.info(f"词汇表构建完成，词汇数量: {len(self.vocab)}")
        logger.info(f"词汇示例: {list(self.vocab.keys())[:10]}")

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """编码文本为向量"""
        if not self.is_initialized:
            logger.warning("词汇表未初始化，返回零向量")
            if isinstance(texts, str):
                return np.zeros((1, self.dimension), dtype=np.float32)
            else:
                return np.zeros((len(texts), self.dimension), dtype=np.float32)
        
        if isinstance(texts, str):
            texts = [texts]
        
        vectors = []
        for text in texts:
            vector = self._encode_single_text(text)
            vectors.append(vector)
        
        return np.array(vectors, dtype=np.float32)

    def _encode_single_text(self, text: str) -> np.ndarray:
        """编码单个文本"""
        words = self._tokenize(text)
        
        if not words:
            return np.zeros(self.dimension, dtype=np.float32)
        
        # 计算TF-IDF加权的词向量平均
        word_weights = Counter(words)
        total_words = len(words)
        
        weighted_vectors = []
        total_weight = 0
        
        for word, tf in word_weights.items():
            if word in self.vocab:
                # TF权重
                tf_weight = tf / total_words
                # IDF权重
                idf_weight = self.idf_weights.get(word, 1.0)
                # 最终权重
                final_weight = tf_weight * idf_weight
                
                # 词向量
                word_vector = self.word_vectors[word]
                weighted_vectors.append(word_vector * final_weight)
                total_weight += final_weight
        
        if not weighted_vectors:
            # 如果没有找到任何词汇，返回零向量
            return np.zeros(self.dimension, dtype=np.float32)
        
        # 计算加权平均
        result_vector = np.sum(weighted_vectors, axis=0)
        if total_weight > 0:
            result_vector = result_vector / total_weight
        
        # 归一化
        norm = np.linalg.norm(result_vector)
        if norm > 0:
            result_vector = result_vector / norm
        
        return result_vector.astype(np.float32)

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension

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

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": "LocalOfflineEmbedding",
            "type": "TF-IDF + Word Vectors",
            "dimension": self.dimension,
            "vocab_size": len(self.vocab),
            "is_offline": True,
            "initialized": self.is_initialized
        }

    def is_available(self) -> bool:
        """检查模型是否可用"""
        return True  # 本地实现总是可用

    def configure(self, **kwargs) -> None:
        """配置模型参数"""
        if 'dimension' in kwargs:
            self.dimension = kwargs['dimension']
            logger.info(f"设置向量维度为: {self.dimension}")
        
        if 'stop_words' in kwargs:
            self.stop_words.update(kwargs['stop_words'])
            logger.info(f"添加停用词: {len(kwargs['stop_words'])}个")