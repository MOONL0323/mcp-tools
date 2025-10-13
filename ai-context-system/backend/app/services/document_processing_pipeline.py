"""
文档处理Pipeline
完整的文档处理流程：解析 -> 分块 -> 实体提取 -> 向量化 -> 存储
"""

from typing import Dict, Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_parser import document_parser
from app.services.chunking_service import intelligent_chunker
from app.services.entity_extraction_service import entity_extractor
from app.services.embedding_service import embedding_service
from app.models.database import Document


class DocumentProcessor:
    """文档处理器"""
    
    async def process_document(
        self,
        document_id: str,
        file_path: str,
        document_type: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        完整处理文档
        
        Args:
            document_id: 文档ID
            file_path: 文件路径
            document_type: 文档类型 (business_doc/demo_code)
            db: 数据库会话
            
        Returns:
            处理结果统计
        """
        try:
            logger.info(f"开始处理文档: {document_id}")
            
            # 1. 更新文档状态为processing
            await self._update_document_status(db, document_id, "processing")
            
            # 2. 解析文档
            logger.info("步骤1: 解析文档...")
            content = await document_parser.parse_file(file_path)
            
            # 3. 智能分块
            logger.info("步骤2: 智能分块...")
            chunks = await intelligent_chunker.chunk_document(
                content=content,
                document_type=document_type,
                enable_llm=True
            )
            
            # 4. 提取实体和关系
            logger.info("步骤3: 提取实体和关系...")
            entities, relations = await entity_extractor.extract_from_chunks(
                chunks=chunks,
                document_id=document_id,
                document_type=document_type
            )
            
            # 5. 构建知识图谱
            logger.info("步骤4: 构建知识图谱...")
            await entity_extractor.build_graph(entities, relations)
            
            # 6. 向量化并存储
            logger.info("步骤5: 向量化并存储...")
            await embedding_service.embed_chunks(chunks, document_id)
            
            # 7. 更新文档元数据
            stats = {
                "chunk_count": len(chunks),
                "entity_count": len(entities),
                "relation_count": len(relations)
            }
            
            await self._update_document_stats(db, document_id, stats)
            await self._update_document_status(db, document_id, "completed")
            
            logger.info(f"文档处理完成: {document_id}, 统计: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"文档处理失败: {document_id}, 错误: {e}")
            await self._update_document_status(db, document_id, "failed")
            raise
    
    async def _update_document_status(
        self,
        db: AsyncSession,
        document_id: str,
        status: str
    ) -> None:
        """更新文档状态"""
        try:
            result = await db.execute(
                """
                UPDATE documents 
                SET processing_status = :status,
                    last_modified = NOW()
                WHERE id = :document_id
                """,
                {"status": status, "document_id": document_id}
            )
            await db.commit()
        except Exception as e:
            logger.error(f"更新文档状态失败: {e}")
            await db.rollback()
    
    async def _update_document_stats(
        self,
        db: AsyncSession,
        document_id: str,
        stats: Dict[str, Any]
    ) -> None:
        """更新文档统计信息"""
        try:
            result = await db.execute(
                """
                UPDATE documents 
                SET chunk_count = :chunk_count,
                    entity_count = :entity_count
                WHERE id = :document_id
                """,
                {
                    "chunk_count": stats["chunk_count"],
                    "entity_count": stats["entity_count"],
                    "document_id": document_id
                }
            )
            await db.commit()
        except Exception as e:
            logger.error(f"更新文档统计失败: {e}")
            await db.rollback()
    
    async def delete_document_data(
        self,
        document_id: str
    ) -> None:
        """删除文档相关的所有数据"""
        try:
            # 删除向量数据
            from app.services.chroma_client import chroma_client
            await chroma_client.delete_by_document(document_id)
            
            # 删除图谱数据
            from app.services.neo4j_client import neo4j_client
            await neo4j_client.delete_document_graph(document_id)
            
            logger.info(f"成功删除文档数据: {document_id}")
            
        except Exception as e:
            logger.error(f"删除文档数据失败: {e}")
            raise


# 全局实例
document_processor = DocumentProcessor()
