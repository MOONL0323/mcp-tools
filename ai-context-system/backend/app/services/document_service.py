"""
文档服务 - 文档管理相关业务逻辑
"""

from typing import List, Optional, Dict, Any, BinaryIO
from uuid import UUID
import os
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.orm import selectinload, joinedload
import aiofiles

from app.core.config import get_settings
from app.core.exceptions import (
    DatabaseError, ValidationError, NotFoundError, 
    BusinessLogicError, FileOperationError
)
from app.models.database import (
    Document, DocumentChunk, Entity, Relation, DocumentAccessLog,
    User, Team, Project, Module, DevType,
    DocumentType, AccessLevel, ProcessingStatus
)
from app.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentUpload,
    DocumentSearchRequest, DocumentSearchResult, DocumentSearchResponse,
    DocumentChunkResponse, EntityResponse, RelationResponse
)

settings = get_settings()


class DocumentService:
    """文档服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件操作相关方法
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _get_mime_type(self, filename: str) -> str:
        """获取文件MIME类型"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
    
    def _generate_file_path(self, user_id: UUID, filename: str) -> str:
        """生成文件存储路径"""
        date_path = datetime.now().strftime("%Y/%m/%d")
        user_path = str(user_id)
        return f"{date_path}/{user_path}/{filename}"
    
    async def _save_file(self, file_content: bytes, file_path: str) -> bool:
        """保存文件到磁盘"""
        try:
            full_path = self.upload_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(file_content)
            
            return True
        except Exception as e:
            raise FileOperationError(f"保存文件失败: {str(e)}")
    
    async def _delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            full_path = self.upload_dir / file_path
            if full_path.exists():
                full_path.unlink()
            return True
        except Exception as e:
            raise FileOperationError(f"删除文件失败: {str(e)}")
    
    # 文档查询方法
    async def get_document_by_id(self, document_id: UUID, user_id: UUID) -> Optional[Document]:
        """通过ID获取文档"""
        try:
            query = (
                select(Document)
                .options(
                    selectinload(Document.team),
                    selectinload(Document.project),
                    selectinload(Document.module),
                    selectinload(Document.dev_type),
                    selectinload(Document.uploader)
                )
                .where(Document.id == document_id)
            )
            
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()
            
            if document and await self._check_document_access(document, user_id):
                return document
            
            return None
        except Exception as e:
            raise DatabaseError(f"获取文档失败: {str(e)}")
    
    async def get_documents(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        document_type: Optional[DocumentType] = None,
        team_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        module_id: Optional[UUID] = None,
        dev_type_id: Optional[UUID] = None,
        access_level: Optional[AccessLevel] = None,
        status: Optional[ProcessingStatus] = None,
        search: Optional[str] = None,
        tags: List[str] = None
    ) -> List[Document]:
        """获取文档列表"""
        try:
            query = (
                select(Document)
                .options(
                    selectinload(Document.team),
                    selectinload(Document.project),
                    selectinload(Document.module),
                    selectinload(Document.dev_type),
                    selectinload(Document.uploader)
                )
            )
            
            # 添加过滤条件
            if document_type:
                query = query.where(Document.type == document_type)
            
            if team_id:
                query = query.where(Document.team_id == team_id)
            
            if project_id:
                query = query.where(Document.project_id == project_id)
            
            if module_id:
                query = query.where(Document.module_id == module_id)
            
            if dev_type_id:
                query = query.where(Document.dev_type_id == dev_type_id)
            
            if access_level:
                query = query.where(Document.access_level == access_level)
            
            if status:
                query = query.where(Document.status == status)
            
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    or_(
                        Document.title.ilike(search_term),
                        Document.description.ilike(search_term),
                        Document.file_name.ilike(search_term)
                    )
                )
            
            if tags:
                for tag in tags:
                    query = query.where(Document.tags.contains([tag]))
            
            # 添加访问权限过滤
            user = await self._get_user_with_teams(user_id)
            if user:
                access_filter = or_(
                    Document.access_level == AccessLevel.PUBLIC,
                    Document.uploaded_by == user_id
                )
                
                if user.teams:
                    access_filter = or_(
                        access_filter,
                        and_(
                            Document.access_level == AccessLevel.TEAM,
                            Document.team_id.in_(
                                select(Team.id).where(Team.name.in_(user.teams))
                            )
                        )
                    )
                
                query = query.where(access_filter)
            
            query = query.offset(skip).limit(limit)
            query = query.order_by(Document.created_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"获取文档列表失败: {str(e)}")
    
    async def _get_user_with_teams(self, user_id: UUID) -> Optional[User]:
        """获取用户及其团队信息"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    async def _check_document_access(self, document: Document, user_id: UUID) -> bool:
        """检查文档访问权限"""
        # 公开文档或自己上传的文档
        if document.access_level == AccessLevel.PUBLIC or document.uploaded_by == user_id:
            return True
        
        # 团队文档需要检查团队权限
        if document.access_level == AccessLevel.TEAM and document.team_id:
            user = await self._get_user_with_teams(user_id)
            if user and document.team:
                return document.team.name in user.teams
        
        return False
    
    # 文档创建和更新方法
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        upload_data: DocumentUpload,
        user_id: UUID
    ) -> Document:
        """上传文档"""
        try:
            # 验证文件大小
            if len(file_content) > settings.MAX_FILE_SIZE:
                raise ValidationError(f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)")
            
            # 验证文件类型
            mime_type = self._get_mime_type(filename)
            if mime_type not in settings.ALLOWED_MIME_TYPES:
                raise ValidationError(f"不支持的文件类型: {mime_type}")
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_content)
            
            # 检查是否已存在相同文件
            existing_doc = await self.db.execute(
                select(Document).where(Document.file_hash == file_hash)
            )
            if existing_doc.scalar_one_or_none():
                raise ValidationError("文件已存在")
            
            # 生成文件路径
            file_path = self._generate_file_path(user_id, filename)
            
            # 保存文件
            await self._save_file(file_content, file_path)
            
            # 创建文档记录
            document = Document(
                title=upload_data.title,
                description=upload_data.description,
                type=upload_data.type,
                team_id=upload_data.team_id,
                project_id=upload_data.project_id,
                module_id=upload_data.module_id,
                dev_type_id=upload_data.dev_type_id,
                file_name=filename,
                file_path=file_path,
                file_size=len(file_content),
                mime_type=mime_type,
                file_hash=file_hash,
                access_level=upload_data.access_level,
                tags=upload_data.tags,
                metadata=upload_data.metadata,
                uploaded_by=user_id,
                status=ProcessingStatus.PENDING
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            # 记录访问日志
            await self._log_document_access(document.id, user_id, "upload")
            
            return document
        except (ValidationError, FileOperationError):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"上传文档失败: {str(e)}")
    
    async def update_document(
        self,
        document_id: UUID,
        update_data: DocumentUpdate,
        user_id: UUID
    ) -> Document:
        """更新文档"""
        try:
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            # 检查更新权限
            if document.uploaded_by != user_id:
                raise ValidationError("只能更新自己上传的文档")
            
            # 更新字段
            update_dict = update_data.dict(exclude_unset=True)
            if update_dict:
                await self.db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(**update_dict)
                )
                await self.db.commit()
                await self.db.refresh(document)
            
            # 记录访问日志
            await self._log_document_access(document.id, user_id, "update")
            
            return document
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"更新文档失败: {str(e)}")
    
    async def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """删除文档"""
        try:
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            # 检查删除权限
            if document.uploaded_by != user_id:
                raise ValidationError("只能删除自己上传的文档")
            
            # 删除相关数据
            await self.db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            await self.db.execute(
                delete(Entity).where(Entity.document_id == document_id)
            )
            await self.db.execute(
                delete(DocumentAccessLog).where(DocumentAccessLog.document_id == document_id)
            )
            
            # 删除文档记录
            await self.db.execute(
                delete(Document).where(Document.id == document_id)
            )
            
            # 删除文件
            await self._delete_file(document.file_path)
            
            await self.db.commit()
            
            return True
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"删除文档失败: {str(e)}")
    
    # 文档下载和查看方法
    async def download_document(self, document_id: UUID, user_id: UUID) -> tuple[bytes, str, str]:
        """下载文档"""
        try:
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            # 读取文件内容
            full_path = self.upload_dir / document.file_path
            if not full_path.exists():
                raise FileOperationError("文件不存在")
            
            async with aiofiles.open(full_path, 'rb') as f:
                content = await f.read()
            
            # 更新下载次数
            await self.db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(download_count=Document.download_count + 1)
            )
            await self.db.commit()
            
            # 记录访问日志
            await self._log_document_access(document.id, user_id, "download")
            
            return content, document.file_name, document.mime_type
        except (NotFoundError, FileOperationError):
            raise
        except Exception as e:
            raise DatabaseError(f"下载文档失败: {str(e)}")
    
    async def view_document(self, document_id: UUID, user_id: UUID) -> DocumentResponse:
        """查看文档详情"""
        try:
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            # 更新查看次数
            await self.db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(view_count=Document.view_count + 1)
            )
            await self.db.commit()
            
            # 记录访问日志
            await self._log_document_access(document.id, user_id, "view")
            
            return DocumentResponse.from_orm(document)
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"查看文档失败: {str(e)}")
    
    # 文档搜索方法
    async def search_documents(
        self,
        search_request: DocumentSearchRequest,
        user_id: UUID
    ) -> DocumentSearchResponse:
        """搜索文档"""
        try:
            # 构建基础查询
            query = (
                select(Document)
                .options(
                    selectinload(Document.team),
                    selectinload(Document.project),
                    selectinload(Document.module),
                    selectinload(Document.dev_type),
                    selectinload(Document.uploader)
                )
            )
            
            # 添加文本搜索条件
            search_term = f"%{search_request.query}%"
            text_search = or_(
                Document.title.ilike(search_term),
                Document.description.ilike(search_term),
                Document.file_name.ilike(search_term)
            )
            
            # 全文搜索（如果需要更高级的搜索，可以使用PostgreSQL的全文搜索功能）
            if search_request.query:
                query = query.where(text_search)
            
            # 添加过滤条件
            if search_request.document_type:
                query = query.where(Document.type == search_request.document_type)
            
            if search_request.team_id:
                query = query.where(Document.team_id == search_request.team_id)
            
            if search_request.project_id:
                query = query.where(Document.project_id == search_request.project_id)
            
            if search_request.module_id:
                query = query.where(Document.module_id == search_request.module_id)
            
            if search_request.dev_type_id:
                query = query.where(Document.dev_type_id == search_request.dev_type_id)
            
            if search_request.tags:
                for tag in search_request.tags:
                    query = query.where(Document.tags.contains([tag]))
            
            # 添加访问权限过滤
            user = await self._get_user_with_teams(user_id)
            if user:
                access_filter = or_(
                    Document.access_level == AccessLevel.PUBLIC,
                    Document.uploaded_by == user_id
                )
                
                if user.teams:
                    access_filter = or_(
                        access_filter,
                        and_(
                            Document.access_level == AccessLevel.TEAM,
                            Document.team_id.in_(
                                select(Team.id).where(Team.name.in_(user.teams))
                            )
                        )
                    )
                
                query = query.where(access_filter)
            
            # 计算总数
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
            
            # 分页和排序
            query = query.offset(search_request.offset).limit(search_request.limit)
            query = query.order_by(Document.created_at.desc())
            
            # 执行查询
            result = await self.db.execute(query)
            documents = result.scalars().all()
            
            # 构建搜索结果
            search_results = []
            for doc in documents:
                # 获取相关的文档块（用于高亮显示）
                chunks = await self._get_matching_chunks(doc.id, search_request.query)
                
                search_result = DocumentSearchResult(
                    document=DocumentResponse.from_orm(doc),
                    chunks=[DocumentChunkResponse.from_orm(chunk) for chunk in chunks[:3]],  # 最多返回3个相关块
                    score=1.0,  # 简单评分，可以后续优化
                    highlights=self._generate_highlights(doc, search_request.query)
                )
                search_results.append(search_result)
            
            return DocumentSearchResponse(
                results=search_results,
                total=total,
                query=search_request.query,
                limit=search_request.limit,
                offset=search_request.offset
            )
        except Exception as e:
            raise DatabaseError(f"搜索文档失败: {str(e)}")
    
    async def _get_matching_chunks(self, document_id: UUID, query: str) -> List[DocumentChunk]:
        """获取匹配的文档块"""
        try:
            search_term = f"%{query}%"
            result = await self.db.execute(
                select(DocumentChunk)
                .where(
                    and_(
                        DocumentChunk.document_id == document_id,
                        or_(
                            DocumentChunk.content.ilike(search_term),
                            DocumentChunk.title.ilike(search_term),
                            DocumentChunk.summary.ilike(search_term)
                        )
                    )
                )
                .order_by(DocumentChunk.chunk_index)
                .limit(10)
            )
            return result.scalars().all()
        except Exception:
            return []
    
    def _generate_highlights(self, document: Document, query: str) -> List[str]:
        """生成搜索结果高亮"""
        highlights = []
        
        # 简单的高亮逻辑
        if query.lower() in document.title.lower():
            highlights.append(document.title)
        
        if document.description and query.lower() in document.description.lower():
            # 截取包含关键词的部分
            desc_lower = document.description.lower()
            query_lower = query.lower()
            index = desc_lower.find(query_lower)
            if index >= 0:
                start = max(0, index - 50)
                end = min(len(document.description), index + len(query) + 50)
                highlight = document.description[start:end]
                if start > 0:
                    highlight = "..." + highlight
                if end < len(document.description):
                    highlight = highlight + "..."
                highlights.append(highlight)
        
        return highlights[:3]  # 最多返回3个高亮
    
    # 文档块相关方法
    async def get_document_chunks(
        self,
        document_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentChunk]:
        """获取文档块列表"""
        try:
            # 检查文档访问权限
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            result = await self.db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"获取文档块失败: {str(e)}")
    
    # 实体和关系相关方法
    async def get_document_entities(
        self,
        document_id: UUID,
        user_id: UUID,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Entity]:
        """获取文档实体列表"""
        try:
            # 检查文档访问权限
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            query = select(Entity).where(Entity.document_id == document_id)
            
            if entity_type:
                query = query.where(Entity.type == entity_type)
            
            query = query.order_by(Entity.name).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"获取文档实体失败: {str(e)}")
    
    async def get_document_relations(
        self,
        document_id: UUID,
        user_id: UUID,
        relation_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Relation]:
        """获取文档关系列表"""
        try:
            # 检查文档访问权限
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            query = (
                select(Relation)
                .options(
                    selectinload(Relation.source_entity),
                    selectinload(Relation.target_entity)
                )
                .join(Entity, or_(
                    Relation.source_entity_id == Entity.id,
                    Relation.target_entity_id == Entity.id
                ))
                .where(Entity.document_id == document_id)
            )
            
            if relation_type:
                query = query.where(Relation.relation_type == relation_type)
            
            query = query.order_by(Relation.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"获取文档关系失败: {str(e)}")
    
    # 访问日志相关方法
    async def _log_document_access(
        self,
        document_id: UUID,
        user_id: UUID,
        action: str,
        ip_address: Optional[str] = None
    ):
        """记录文档访问日志"""
        try:
            log = DocumentAccessLog(
                document_id=document_id,
                user_id=user_id,
                action=action,
                ip_address=ip_address
            )
            self.db.add(log)
            await self.db.commit()
        except Exception:
            # 访问日志失败不应该影响主要操作
            pass
    
    async def get_document_access_logs(
        self,
        document_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[DocumentAccessLog]:
        """获取文档访问日志"""
        try:
            # 检查文档访问权限
            document = await self.get_document_by_id(document_id, user_id)
            if not document:
                raise NotFoundError("文档不存在或无权限访问")
            
            result = await self.db.execute(
                select(DocumentAccessLog)
                .options(selectinload(DocumentAccessLog.user))
                .where(DocumentAccessLog.document_id == document_id)
                .order_by(DocumentAccessLog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"获取文档访问日志失败: {str(e)}")
    
    # 统计相关方法
    async def get_document_stats(self, user_id: UUID) -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            # 获取用户可访问的文档
            user = await self._get_user_with_teams(user_id)
            
            base_query = select(Document)
            if user:
                access_filter = or_(
                    Document.access_level == AccessLevel.PUBLIC,
                    Document.uploaded_by == user_id
                )
                
                if user.teams:
                    access_filter = or_(
                        access_filter,
                        and_(
                            Document.access_level == AccessLevel.TEAM,
                            Document.team_id.in_(
                                select(Team.id).where(Team.name.in_(user.teams))
                            )
                        )
                    )
                
                base_query = base_query.where(access_filter)
            
            # 总文档数
            total_docs = await self.db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            
            # 按类型统计
            type_stats = await self.db.execute(
                select(Document.type, func.count())
                .select_from(base_query.subquery())
                .group_by(Document.type)
            )
            
            # 按状态统计
            status_stats = await self.db.execute(
                select(Document.status, func.count())
                .select_from(base_query.subquery())
                .group_by(Document.status)
            )
            
            # 最近上传的文档
            recent_docs = await self.db.execute(
                base_query
                .options(selectinload(Document.uploader))
                .order_by(Document.created_at.desc())
                .limit(10)
            )
            
            return {
                "total_documents": total_docs.scalar(),
                "by_type": dict(type_stats.all()),
                "by_status": dict(status_stats.all()),
                "recent_uploads": [DocumentResponse.from_orm(doc) for doc in recent_docs.scalars().all()]
            }
        except Exception as e:
            raise DatabaseError(f"获取文档统计失败: {str(e)}")