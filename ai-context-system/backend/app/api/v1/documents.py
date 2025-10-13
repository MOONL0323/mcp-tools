"""
文档相关API路由
"""

from typing import List, Optional
from uuid import UUID
from fastapi import (
    APIRouter, Depends, HTTPException, status, 
    UploadFile, File, Form, Response
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    DatabaseError, ValidationError, NotFoundError, 
    BusinessLogicError, FileOperationError
)
from app.schemas import (
    DocumentResponse, DocumentUpdate, DocumentUpload,
    DocumentSearchRequest, DocumentSearchResponse,
    DocumentChunkResponse, EntityResponse, RelationResponse,
    DocumentType, AccessLevel
)
from app.services.document_service import DocumentService
from app.services.document_processing_pipeline import document_processor
from app.api.dependencies import CurrentUser, ClientIP
import os
import shutil
from pathlib import Path

router = APIRouter()

# 上传目录配置
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    type: DocumentType = Form(...),
    team_id: Optional[UUID] = Form(None),
    project_id: Optional[UUID] = Form(None),
    module_id: Optional[UUID] = Form(None),
    dev_type_id: Optional[UUID] = Form(None),
    access_level: AccessLevel = Form(AccessLevel.TEAM),
    tags: str = Form(""),  # 逗号分隔的标签字符串
    metadata: str = Form("{}")  # JSON字符串
):
    """上传文档"""
    try:
        # 处理标签
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # 处理元数据
        import json
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # 读取文件内容
        file_content = await file.read()
        
        # 创建上传数据
        upload_data = DocumentUpload(
            title=title,
            description=description,
            type=type,
            team_id=team_id,
            project_id=project_id,
            module_id=module_id,
            dev_type_id=dev_type_id,
            access_level=access_level,
            tags=tag_list,
            metadata=metadata_dict
        )
        
        document_service = DocumentService(db)
        document = await document_service.upload_document(
            file_content, file.filename, upload_data, current_user.id
        )
        
        return DocumentResponse.from_orm(document)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileOperationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[DocumentType] = None,
    team_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    module_id: Optional[UUID] = None,
    dev_type_id: Optional[UUID] = None,
    access_level: Optional[AccessLevel] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None
):
    """获取文档列表"""
    try:
        # 处理标签
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else None
        
        document_service = DocumentService(db)
        documents = await document_service.get_documents(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            document_type=document_type,
            team_id=team_id,
            project_id=project_id,
            module_id=module_id,
            dev_type_id=dev_type_id,
            access_level=access_level,
            search=search,
            tags=tag_list
        )
        
        return [DocumentResponse.from_orm(doc) for doc in documents]
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: CurrentUser,
    ip_address: ClientIP,
    db: AsyncSession = Depends(get_db)
):
    """获取文档详情"""
    try:
        document_service = DocumentService(db)
        document = await document_service.view_document(document_id, current_user.id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在或无权限访问"
            )
        return document
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    update_data: DocumentUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """更新文档信息"""
    try:
        document_service = DocumentService(db)
        document = await document_service.update_document(
            document_id, update_data, current_user.id
        )
        return DocumentResponse.from_orm(document)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """删除文档"""
    try:
        document_service = DocumentService(db)
        await document_service.delete_document(document_id, current_user.id)
        return {"message": "文档删除成功"}
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: CurrentUser,
    ip_address: ClientIP,
    db: AsyncSession = Depends(get_db)
):
    """下载文档"""
    try:
        document_service = DocumentService(db)
        content, filename, mime_type = await document_service.download_document(
            document_id, current_user.id
        )
        
        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\""
            }
        )
    except (NotFoundError, FileOperationError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """搜索文档"""
    try:
        document_service = DocumentService(db)
        search_result = await document_service.search_documents(
            search_request, current_user.id
        )
        return search_result
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取文档块列表"""
    try:
        document_service = DocumentService(db)
        chunks = await document_service.get_document_chunks(
            document_id, current_user.id, skip, limit
        )
        return [DocumentChunkResponse.from_orm(chunk) for chunk in chunks]
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{document_id}/entities", response_model=List[EntityResponse])
async def get_document_entities(
    document_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    entity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """获取文档实体列表"""
    try:
        document_service = DocumentService(db)
        entities = await document_service.get_document_entities(
            document_id, current_user.id, entity_type, skip, limit
        )
        return [EntityResponse.from_orm(entity) for entity in entities]
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{document_id}/relations", response_model=List[RelationResponse])
async def get_document_relations(
    document_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    relation_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """获取文档关系列表"""
    try:
        document_service = DocumentService(db)
        relations = await document_service.get_document_relations(
            document_id, current_user.id, relation_type, skip, limit
        )
        return [RelationResponse.from_orm(relation) for relation in relations]
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{document_id}/access-logs")
async def get_document_access_logs(
    document_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取文档访问日志"""
    try:
        document_service = DocumentService(db)
        logs = await document_service.get_document_access_logs(
            document_id, current_user.id, skip, limit
        )
        return {
            "logs": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "username": log.user.username if log.user else "anonymous",
                    "action": log.action,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats/overview")
async def get_document_stats(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """获取文档统计信息"""
    try:
        document_service = DocumentService(db)
        stats = await document_service.get_document_stats(current_user.id)
        return stats
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )