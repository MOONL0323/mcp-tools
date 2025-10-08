"""
本地知识图谱实现
使用NetworkX和jieba，完全离线运行
"""
import os
import json
import pickle
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter, defaultdict
import networkx as nx
from langchain.schema import Document
import numpy as np
from loguru import logger

from interfaces.knowledge_graph import KnowledgeGraphInterface
from interfaces.embedding_provider import EmbeddingProviderInterface


class LocalKnowledgeGraph(KnowledgeGraphInterface):
    """本地知识图谱实现"""
    
    def __init__(self):
        """初始化知识图谱构建器"""
        self.min_keyword_freq = 2
        self.max_keywords_per_doc = 20
        self.similarity_threshold = 0.7
        self.embedding_provider: Optional[EmbeddingProviderInterface] = None
        
        # 停用词
        self.stopwords = self._load_stopwords()
        
        # 图对象
        self.graph = nx.Graph()
        
        # 统计信息
        self.keyword_freq = Counter()
        self.doc_keywords = {}  # 文档ID -> 关键词列表
        self.keyword_docs = defaultdict(set)  # 关键词 -> 文档ID集合
        
        logger.info("本地知识图谱构建器初始化完成")
    
    def _load_stopwords(self) -> Set[str]:
        """加载停用词表"""
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', 
            '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '对', '可以',
            '他', '她', '它', '们', '这个', '那个', '这些', '那些', '什么', '怎么', '为什么', '哪里',
            '如何', '所以', '因为', '但是', '然后', '而且', '或者', '以及', '等等', '比如', '例如'
        }
        return stopwords
    
    def extract_keywords(self, text: str, max_keywords: int = None) -> List[str]:
        """
        提取文本关键词
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数
            
        Returns:
            关键词列表
        """
        if max_keywords is None:
            max_keywords = self.max_keywords_per_doc
        
        try:
            import jieba
            import jieba.analyse
            
            # 初始化jieba（如果尚未初始化）
            jieba.initialize()
            
            # 使用jieba的TF-IDF算法提取关键词
            keywords = jieba.analyse.extract_tags(
                text, 
                topK=max_keywords * 2,  # 提取更多候选词
                withWeight=True
            )
            
            # 过滤停用词和短词
            filtered_keywords = []
            for word, weight in keywords:
                if (len(word) >= 2 and 
                    word not in self.stopwords and 
                    not word.isdigit() and
                    len(filtered_keywords) < max_keywords):
                    filtered_keywords.append(word)
            
            return filtered_keywords
            
        except ImportError:
            logger.warning("jieba 未安装，使用简单的关键词提取方法")
            return self._simple_extract_keywords(text, max_keywords)
    
    def _simple_extract_keywords(self, text: str, max_keywords: int) -> List[str]:
        """简单的关键词提取方法"""
        # 简单的词频统计
        import re
        
        # 移除标点符号并分词
        words = re.findall(r'[\u4e00-\u9fff]+', text)
        word_freq = Counter(words)
        
        # 过滤停用词和短词
        filtered_words = []
        for word, freq in word_freq.most_common():
            if (len(word) >= 2 and 
                word not in self.stopwords and 
                len(filtered_words) < max_keywords):
                filtered_words.append(word)
        
        return filtered_words
    
    def build_from_documents(self, documents: List[Document]) -> nx.Graph:
        """
        从文档列表构建知识图谱
        
        Args:
            documents: 文档列表
            
        Returns:
            构建的图对象
        """
        logger.info(f"开始从 {len(documents)} 个文档构建知识图谱")
        
        # 重置图和统计信息
        self.graph.clear()
        self.keyword_freq.clear()
        self.doc_keywords.clear()
        self.keyword_docs.clear()
        
        # 第一阶段：提取所有关键词并统计频率
        logger.info("提取关键词...")
        for i, doc in enumerate(documents):
            doc_id = f"doc_{i}"
            keywords = self.extract_keywords(doc.page_content)
            
            self.doc_keywords[doc_id] = keywords
            
            for keyword in keywords:
                self.keyword_freq[keyword] += 1
                self.keyword_docs[keyword].add(doc_id)
            
            # 将文档信息添加到图中
            self.graph.add_node(
                doc_id,
                type='document',
                content=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                metadata=doc.metadata,
                keywords=keywords
            )
        
        # 过滤低频关键词
        valid_keywords = {
            keyword for keyword, freq in self.keyword_freq.items() 
            if freq >= self.min_keyword_freq
        }
        
        logger.info(f"提取到 {len(self.keyword_freq)} 个关键词，过滤后保留 {len(valid_keywords)} 个")
        
        # 第二阶段：添加关键词节点和关系
        logger.info("构建关键词节点和关系...")
        
        # 添加关键词节点
        for keyword in valid_keywords:
            self.graph.add_node(
                keyword,
                type='keyword',
                frequency=self.keyword_freq[keyword],
                related_docs=list(self.keyword_docs[keyword])
            )
        
        # 添加文档-关键词关系
        for doc_id, keywords in self.doc_keywords.items():
            for keyword in keywords:
                if keyword in valid_keywords:
                    self.graph.add_edge(
                        doc_id, keyword,
                        type='contains',
                        weight=1.0
                    )
        
        # 第三阶段：添加关键词之间的共现关系
        logger.info("构建关键词共现关系...")
        self._build_keyword_cooccurrence(valid_keywords)
        
        # 第四阶段：基于语义相似度添加关系（可选）
        if len(valid_keywords) <= 100 and self.embedding_provider is not None:
            logger.info("构建语义相似度关系...")
            self._build_semantic_relations(valid_keywords)
        
        logger.info(f"知识图谱构建完成: {self.graph.number_of_nodes()} 个节点, {self.graph.number_of_edges()} 条边")
        
        return self.graph
    
    def _build_keyword_cooccurrence(self, keywords: Set[str]):
        """构建关键词共现关系"""
        # 计算关键词共现
        cooccurrence = defaultdict(int)
        
        for doc_keywords in self.doc_keywords.values():
            # 过滤有效关键词
            valid_doc_keywords = [kw for kw in doc_keywords if kw in keywords]
            
            # 计算两两共现
            for i, kw1 in enumerate(valid_doc_keywords):
                for kw2 in valid_doc_keywords[i+1:]:
                    pair = tuple(sorted([kw1, kw2]))
                    cooccurrence[pair] += 1
        
        # 添加共现边
        for (kw1, kw2), count in cooccurrence.items():
            if count >= self.min_keyword_freq:
                # 计算共现强度
                freq1 = self.keyword_freq[kw1]
                freq2 = self.keyword_freq[kw2]
                cooccurrence_strength = count / min(freq1, freq2)
                
                self.graph.add_edge(
                    kw1, kw2,
                    type='cooccurrence',
                    weight=cooccurrence_strength,
                    count=count
                )
    
    def _build_semantic_relations(self, keywords: Set[str]):
        """基于语义相似度构建关系"""
        keywords_list = list(keywords)
        
        try:
            # 计算所有关键词的向量
            embeddings = self.embedding_provider.encode(keywords_list)
            
            # 计算相似度矩阵
            for i, kw1 in enumerate(keywords_list):
                for j, kw2 in enumerate(keywords_list[i+1:], i+1):
                    # 计算余弦相似度
                    emb1, emb2 = embeddings[i], embeddings[j]
                    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                    
                    # 如果相似度超过阈值且不存在共现关系，添加语义关系
                    if (similarity > self.similarity_threshold and 
                        not self.graph.has_edge(kw1, kw2)):
                        
                        self.graph.add_edge(
                            kw1, kw2,
                            type='semantic',
                            weight=float(similarity),
                            similarity=float(similarity)
                        )
                        
        except Exception as e:
            logger.warning(f"构建语义关系时出错: {str(e)}")
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图统计信息"""
        stats = {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
            "connected_components": nx.number_connected_components(self.graph)
        }
        
        # 节点类型统计
        node_types = defaultdict(int)
        for node, data in self.graph.nodes(data=True):
            node_types[data.get('type', 'unknown')] += 1
        stats["node_types"] = dict(node_types)
        
        # 边类型统计
        edge_types = defaultdict(int)
        for _, _, data in self.graph.edges(data=True):
            edge_types[data.get('type', 'unknown')] += 1
        stats["edge_types"] = dict(edge_types)
        
        return stats
    
    def find_related_keywords(self, keyword: str, max_results: int = 10) -> List[Tuple[str, float, str]]:
        """
        查找与给定关键词相关的其他关键词
        
        Args:
            keyword: 目标关键词
            max_results: 最大结果数
            
        Returns:
            (关键词, 权重, 关系类型) 的列表
        """
        if keyword not in self.graph:
            return []
        
        related = []
        for neighbor in self.graph.neighbors(keyword):
            if self.graph.nodes[neighbor].get('type') == 'keyword':
                edge_data = self.graph[keyword][neighbor]
                weight = edge_data.get('weight', 0.0)
                relation_type = edge_data.get('type', 'unknown')
                related.append((neighbor, weight, relation_type))
        
        # 按权重排序
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:max_results]
    
    def find_related_documents(self, keyword: str) -> List[str]:
        """
        查找包含指定关键词的文档
        
        Args:
            keyword: 关键词
            
        Returns:
            文档ID列表
        """
        if keyword not in self.graph:
            return []
        
        related_docs = []
        for neighbor in self.graph.neighbors(keyword):
            if self.graph.nodes[neighbor].get('type') == 'document':
                related_docs.append(neighbor)
        
        return related_docs
    
    def save_graph(self, filepath: str) -> None:
        """
        保存图到文件
        
        Args:
            filepath: 文件路径
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存为pickle格式（包含所有数据）
        with open(filepath, 'wb') as f:
            pickle.dump({
                'graph': self.graph,
                'keyword_freq': self.keyword_freq,
                'doc_keywords': self.doc_keywords,
                'keyword_docs': dict(self.keyword_docs)
            }, f)
        
        logger.info(f"图已保存到: {filepath}")
    
    def load_graph(self, filepath: str) -> None:
        """
        从文件加载图
        
        Args:
            filepath: 文件路径
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.graph = data['graph']
            self.keyword_freq = data['keyword_freq']
            self.doc_keywords = data['doc_keywords']
            self.keyword_docs = defaultdict(set, data['keyword_docs'])
        
        logger.info(f"图已从文件加载: {filepath}")
    
    def configure(self, **kwargs) -> None:
        """
        配置图构建参数
        
        Args:
            **kwargs: 配置参数
        """
        if 'min_keyword_freq' in kwargs:
            self.min_keyword_freq = kwargs['min_keyword_freq']
        
        if 'max_keywords_per_doc' in kwargs:
            self.max_keywords_per_doc = kwargs['max_keywords_per_doc']
        
        if 'similarity_threshold' in kwargs:
            self.similarity_threshold = kwargs['similarity_threshold']
        
        if 'embedding_provider' in kwargs:
            self.embedding_provider = kwargs['embedding_provider']
        
        if 'stopwords' in kwargs:
            self.stopwords.update(kwargs['stopwords'])
        
        logger.info(f"知识图谱配置已更新: min_freq={self.min_keyword_freq}, max_keywords={self.max_keywords_per_doc}")
    
    def export(self) -> Dict[str, Any]:
        """
        导出图数据供前端可视化使用
        
        Returns:
            包含节点和边的字典
        """
        nodes = []
        edges = []
        
        # 导出节点
        for node_id, data in self.graph.nodes(data=True):
            node_info = {
                'id': str(node_id),
                'label': str(node_id),
                'type': data.get('type', 'keyword'),
                'frequency': data.get('frequency', 1),
                'documents': list(data.get('documents', set()))
            }
            nodes.append(node_info)
        
        # 导出边
        for source, target, data in self.graph.edges(data=True):
            edge_info = {
                'source': str(source),
                'target': str(target),
                'weight': data.get('weight', 1),
                'type': data.get('type', 'related')
            }
            edges.append(edge_info)
        
        # 统计信息
        stats = {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'document_count': len(self.doc_keywords),
            'avg_degree': sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1)
        }
        
        logger.info(f"导出图数据: {stats['node_count']} 个节点, {stats['edge_count']} 条边")
        
        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': stats
        }
    
    def remove_node(self, node_id: str) -> bool:
        """
        删除指定节点及其相关边
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否删除成功
        """
        try:
            if node_id in self.graph:
                # 获取节点信息
                node_data = self.graph.nodes[node_id]
                
                # 从统计中移除
                if node_id in self.keyword_freq:
                    del self.keyword_freq[node_id]
                
                # 从文档关键词映射中移除
                docs_to_update = node_data.get('documents', set())
                for doc_id in docs_to_update:
                    if doc_id in self.doc_keywords:
                        if node_id in self.doc_keywords[doc_id]:
                            self.doc_keywords[doc_id].remove(node_id)
                
                # 从关键词文档映射中移除
                if node_id in self.keyword_docs:
                    del self.keyword_docs[node_id]
                
                # 从图中移除节点
                self.graph.remove_node(node_id)
                
                logger.info(f"节点 '{node_id}' 已删除")
                return True
            else:
                logger.warning(f"节点 '{node_id}' 不存在")
                return False
        except Exception as e:
            logger.error(f"删除节点失败: {str(e)}")
            return False
    
    def clear(self) -> None:
        """清空整个图"""
        self.graph.clear()
        self.keyword_freq.clear()
        self.doc_keywords.clear()
        self.keyword_docs.clear()
        logger.info("知识图谱已清空")