"""
增强的文档管理系统
支持文档上传、向量化存储，确保每个片段都能追溯到源文件
为AI Agent提供高质量的文档检索服务
"""
import os
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import pickle
from loguru import logger

from interfaces.document_parser import DocumentParserInterface
from interfaces.embedding_provider import EmbeddingProviderInterface
from interfaces.vector_store import VectorStoreInterface


@dataclass
class DocumentChunk:
    """文档片段数据类"""
    chunk_id: str
    content: str
    source_file: str
    source_path: str
    file_type: str
    chunk_index: int
    total_chunks: int
    start_position: int
    end_position: int
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass 
class DocumentInfo:
    """文档信息数据类"""
    doc_id: str
    filename: str
    file_path: str
    file_type: str
    file_size: int
    file_hash: str
    total_chunks: int
    upload_time: str
    processed: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.upload_time is None:
            self.upload_time = datetime.now().isoformat()


class EnhancedDocumentManager:
    """增强的文档管理器"""
    
    def __init__(
        self,
        document_parser: DocumentParserInterface,
        embedding_provider: EmbeddingProviderInterface,
        vector_store: VectorStoreInterface,
        storage_path: str = "data/documents"
    ):
        self.document_parser = document_parser
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 文档索引文件
        self.index_file = self.storage_path / "document_index.json"
        self.chunks_file = self.storage_path / "document_chunks.pkl"
        
        # 内存缓存
        self.document_index: Dict[str, DocumentInfo] = {}
        self.document_chunks: Dict[str, DocumentChunk] = {}
        
        # 加载现有数据
        self._load_index()
        self._load_chunks()
        
        logger.info(f"文档管理器初始化完成，已加载 {len(self.document_index)} 个文档")

    def _load_index(self):
        """加载文档索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.document_index = {
                        k: DocumentInfo(**v) for k, v in data.items()
                    }
                logger.info(f"已加载文档索引: {len(self.document_index)} 个文档")
            except Exception as e:
                logger.error(f"加载文档索引失败: {e}")
                self.document_index = {}
    
    def _save_index(self):
        """保存文档索引"""
        try:
            data = {k: asdict(v) for k, v in self.document_index.items()}
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文档索引失败: {e}")
    
    def _load_chunks(self):
        """加载文档片段"""
        if self.chunks_file.exists():
            try:
                with open(self.chunks_file, 'rb') as f:
                    self.document_chunks = pickle.load(f)
                logger.info(f"已加载文档片段: {len(self.document_chunks)} 个片段")
            except Exception as e:
                logger.error(f"加载文档片段失败: {e}")
                self.document_chunks = {}
    
    def _save_chunks(self):
        """保存文档片段"""
        try:
            with open(self.chunks_file, 'wb') as f:
                pickle.dump(self.document_chunks, f)
        except Exception as e:
            logger.error(f"保存文档片段失败: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return ""

    def upload_document(self, file_path: str, filename: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        上传并处理文档
        
        Returns:
            (success, message, doc_id)
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False, f"文件不存在: {file_path}", None
            
            if filename is None:
                filename = file_path.name
            
            # 生成文档ID
            doc_id = str(uuid.uuid4())
            
            # 计算文件信息
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(str(file_path))
            file_type = file_path.suffix.lower()
            
            # 检查是否已存在相同文档
            existing_doc = self._find_document_by_hash(file_hash)
            if existing_doc:
                return False, f"文档已存在: {existing_doc.filename}", existing_doc.doc_id
            
            # 创建文档信息
            doc_info = DocumentInfo(
                doc_id=doc_id,
                filename=filename,
                file_path=str(file_path),
                file_type=file_type,
                file_size=file_size,
                file_hash=file_hash,
                total_chunks=0,
                upload_time=datetime.now().isoformat()
            )
            
            # 解析文档
            try:
                documents = self.document_parser.parse_file(str(file_path))
                logger.info(f"文档解析完成，共 {len(documents)} 个片段")
                
                # 处理文档片段
                chunks = self._process_document_chunks(documents, doc_info)
                
                # 向量化
                self._vectorize_chunks(chunks)
                
                # 存储到向量数据库
                self._store_chunks(chunks)
                
                # 更新文档信息
                doc_info.total_chunks = len(chunks)
                doc_info.processed = True
                self.document_index[doc_id] = doc_info
                
                # 保存
                self._save_index()
                self._save_chunks()
                
                logger.success(f"文档上传成功: {filename} ({len(chunks)} 个片段)")
                return True, f"文档上传成功，共处理 {len(chunks)} 个片段", doc_id
                
            except Exception as e:
                doc_info.error_message = str(e)
                doc_info.processed = False
                self.document_index[doc_id] = doc_info
                self._save_index()
                logger.error(f"文档处理失败: {e}")
                return False, f"文档处理失败: {e}", doc_id
                
        except Exception as e:
            logger.error(f"文档上传失败: {e}")
            return False, f"文档上传失败: {e}", None

    def _find_document_by_hash(self, file_hash: str) -> Optional[DocumentInfo]:
        """根据文件哈希查找文档"""
        for doc_info in self.document_index.values():
            if doc_info.file_hash == file_hash:
                return doc_info
        return None

    def _process_document_chunks(self, documents: List[Any], doc_info: DocumentInfo) -> List[DocumentChunk]:
        """处理文档片段"""
        chunks = []
        
        for i, doc in enumerate(documents):
            chunk_id = f"{doc_info.doc_id}_{i:04d}"
            
            # 获取文档内容和元数据
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            # 添加源文件信息到元数据
            metadata.update({
                'source_document_id': doc_info.doc_id,
                'source_filename': doc_info.filename,
                'source_file_path': doc_info.file_path,
                'file_type': doc_info.file_type,
                'chunk_index': i,
                'total_chunks': len(documents)
            })
            
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                content=content,
                source_file=doc_info.filename,
                source_path=doc_info.file_path,
                file_type=doc_info.file_type,
                chunk_index=i,
                total_chunks=len(documents),
                start_position=metadata.get('start_position', 0),
                end_position=metadata.get('end_position', len(content)),
                metadata=metadata
            )
            
            chunks.append(chunk)
            self.document_chunks[chunk_id] = chunk
        
        return chunks

    def _vectorize_chunks(self, chunks: List[DocumentChunk]):
        """向量化文档片段"""
        if not chunks:
            return
        
        try:
            # 提取文本内容
            texts = [chunk.content for chunk in chunks]
            
            # 批量向量化
            embeddings = self.embedding_provider.embed_texts(texts)
            
            # 分配向量到片段
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                
            logger.info(f"向量化完成: {len(chunks)} 个片段")
            
        except Exception as e:
            logger.error(f"向量化失败: {e}")
            raise

    def _store_chunks(self, chunks: List[DocumentChunk]):
        """存储片段到向量数据库"""
        for chunk in chunks:
            if chunk.embedding:
                self.vector_store.add_vector(
                    vector_id=chunk.chunk_id,
                    vector=chunk.embedding,
                    metadata={
                        'content': chunk.content,
                        'source_file': chunk.source_file,
                        'source_path': chunk.source_path,
                        'file_type': chunk.file_type,
                        'chunk_index': chunk.chunk_index,
                        'total_chunks': chunk.total_chunks,
                        **chunk.metadata
                    }
                )

    def search_documents(self, query: str, top_k: int = 10, file_type: str = None) -> List[Dict[str, Any]]:
        """搜索文档"""
        try:
            # 向量化查询
            query_embedding = self.embedding_provider.embed_query(query)
            if not query_embedding:
                return []
            
            # 搜索向量数据库
            results = self.vector_store.search(query_embedding, top_k * 2)  # 多获取一些结果用于过滤
            
            # 过滤结果
            filtered_results = []
            for result in results:
                metadata = result.get('metadata', {})
                
                # 文件类型过滤
                if file_type and metadata.get('file_type', '').lower() != file_type.lower():
                    continue
                
                # 构建结果
                search_result = {
                    'chunk_id': result.get('vector_id'),
                    'content': metadata.get('content', ''),
                    'source_file': metadata.get('source_file', ''),
                    'source_path': metadata.get('source_path', ''),
                    'file_type': metadata.get('file_type', ''),
                    'chunk_index': metadata.get('chunk_index', 0),
                    'total_chunks': metadata.get('total_chunks', 1),
                    'similarity': result.get('similarity', 0.0),
                    'metadata': metadata
                }
                
                filtered_results.append(search_result)
                
                if len(filtered_results) >= top_k:
                    break
            
            logger.info(f"文档搜索完成: 查询'{query}', 返回 {len(filtered_results)} 个结果")
            return filtered_results
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []

    def get_document_info(self, doc_id: str) -> Optional[DocumentInfo]:
        """获取文档信息"""
        return self.document_index.get(doc_id)

    def list_documents(self) -> List[DocumentInfo]:
        """列出所有文档"""
        return list(self.document_index.values())

    def delete_document(self, doc_id: str) -> Tuple[bool, str]:
        """删除文档"""
        try:
            if doc_id not in self.document_index:
                return False, "文档不存在"
            
            doc_info = self.document_index[doc_id]
            
            # 删除相关的chunk
            chunks_to_delete = [chunk_id for chunk_id, chunk in self.document_chunks.items() 
                              if chunk.chunk_id.startswith(doc_id)]
            
            for chunk_id in chunks_to_delete:
                # 从向量数据库删除
                self.vector_store.delete_vector(chunk_id)
                # 从内存删除
                del self.document_chunks[chunk_id]
            
            # 删除文档记录
            del self.document_index[doc_id]
            
            # 保存
            self._save_index()
            self._save_chunks()
            
            logger.info(f"文档已删除: {doc_info.filename}")
            return True, f"文档已删除: {doc_info.filename}"
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False, f"删除文档失败: {e}"

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_docs = len(self.document_index)
        processed_docs = sum(1 for doc in self.document_index.values() if doc.processed)
        total_chunks = len(self.document_chunks)
        
        file_types = {}
        for doc in self.document_index.values():
            file_type = doc.file_type
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            'total_documents': total_docs,
            'processed_documents': processed_docs,
            'total_chunks': total_chunks,
            'file_types': file_types,
            'embedding_dimension': self.embedding_provider.get_embedding_dimension()
        }