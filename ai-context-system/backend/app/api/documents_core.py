"""
简化的文档管理API - 符合AI代码生成系统方案核心目标
异步版本，兼容当前数据库模型
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.database import (
    Document, DevType, Team, Project, Module, 
    DocumentType, ProcessingStatus, User
)
from app.services.enhanced_document_parser import EnhancedDocumentParser
from datetime import datetime
import structlog
import json
import uuid
import os
import tempfile
from pathlib import Path

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),  # "business_doc" 或 "demo_code"
    team_name: str = Form(...),
    team_role: Optional[str] = Form(None),  # 团队角色: frontend/backend/test/planning/other
    project_name: str = Form(...),
    module_name: Optional[str] = Form(None),
    code_function: Optional[str] = Form(None),  # Demo代码功能: api/pkg/cmd/unittest/other
    tags: str = Form("[]"),  # JSON字符串格式的标签
    uploaded_by: str = Form("default-user"),  # 用户名
    dev_type_id: Optional[str] = Form(None),  # 文档分类ID（UUID字符串）
    description: Optional[str] = Form(None),  # 文档描述
    db: AsyncSession = Depends(get_db)
):
    """
    上传文档或代码文件 - 核心功能：为AI Agent提供上下文
    
    参数:
    - doc_type: business_doc(项目文档) 或 demo_code(Demo代码)
    - team_name: 团队名称（默认: xaas开发组）
    - team_role: 团队角色（前端/后端/测试/规划/其它）
    - project_name: 项目名称
    - module_name: 模块名称（可选）
    - code_function: 代码功能（仅Demo代码，api/pkg/cmd/unittest/other）
    - uploaded_by: 上传用户名
    """
    try:
        # 1. 验证文件类型
        if not EnhancedDocumentParser.is_allowed_file(file.filename):
            allowed = ', '.join(sorted(EnhancedDocumentParser.ALLOWED_EXTENSIONS))
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型。支持的格式: {allowed}"
            )
        
        # 2. 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 检查文件大小（限制100MB）
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大，最大支持100MB"
            )
        
        # 3. 解析文件内容
        # 将内容保存到临时文件进行解析
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='wb', 
                suffix=Path(file.filename).suffix,
                delete=False
            ) as tf:
                tf.write(content)
                temp_file = tf.name
            
            # 使用增强解析器
            content_str, mime_type = await EnhancedDocumentParser.parse_file(
                temp_file, 
                original_content=content
            )
            
            logger.info(f"文件解析成功: {file.filename}, 大小: {file_size}, 类型: {mime_type}")
            
        except Exception as e:
            logger.error(f"文件解析失败: {file.filename}, 错误: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"文件解析失败: {str(e)}"
            )
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        # 4. 解析标签
        try:
            tags_list = json.loads(tags) if tags != "[]" else []
        except:
            tags_list = []
        
        # 1. 查找或创建团队
        team_stmt = select(Team).filter(Team.name == team_name)
        team_result = await db.execute(team_stmt)
        team = team_result.scalar_one_or_none()
        
        if not team:
            # 创建新团队
            team = Team(
                id=str(uuid.uuid4()),
                name=team_name,
                display_name=team_name,
                description=f"Auto-created team: {team_name}",
                created_by=uploaded_by
            )
            db.add(team)
            await db.flush()
        
        # 2. 查找或创建项目
        project_stmt = select(Project).filter(
            Project.name == project_name,
            Project.team_id == team.id
        )
        project_result = await db.execute(project_stmt)
        project = project_result.scalar_one_or_none()
        
        if not project:
            project = Project(
                id=str(uuid.uuid4()),
                team_id=team.id,
                name=project_name,
                display_name=project_name,
                description=f"Auto-created project: {project_name}",
                created_by=uploaded_by
            )
            db.add(project)
            await db.flush()
        
        # 3. 查找或创建模块（如果提供）
        module_id = None
        if module_name:
            module_stmt = select(Module).filter(
                Module.name == module_name,
                Module.project_id == project.id
            )
            module_result = await db.execute(module_stmt)
            module = module_result.scalar_one_or_none()
            
            if not module:
                module = Module(
                    id=str(uuid.uuid4()),
                    project_id=project.id,
                    name=module_name,
                    display_name=module_name,
                    description=f"Auto-created module: {module_name}",
                    created_by=uploaded_by
                )
                db.add(module)
                await db.flush()
            
            module_id = module.id
        
        # 4. 查找DevType（如果提供了dev_type_id）
        dev_type_id_to_use = None
        if dev_type_id:
            dev_type_stmt = select(DevType).filter(DevType.id == dev_type_id)
            dev_type_result = await db.execute(dev_type_stmt)
            dev_type = dev_type_result.scalar_one_or_none()
            if dev_type:
                dev_type_id_to_use = dev_type.id
        
        # 如果没有提供或找不到，使用默认DevType
        if not dev_type_id_to_use:
            doc_type_enum = DocumentType.BUSINESS_DOC if doc_type == "business_doc" else DocumentType.DEMO_CODE
            dev_type_stmt = select(DevType).filter(DevType.category == doc_type_enum).limit(1)
            dev_type_result = await db.execute(dev_type_stmt)
            dev_type = dev_type_result.scalar_one_or_none()
            
            if not dev_type:
                # 创建默认的DevType
                dev_type = DevType(
                    id=str(uuid.uuid4()),
                    category=doc_type_enum,
                    name=doc_type,
                    display_name="设计文档" if doc_type == "business_doc" else "示例代码",
                    description=f"Auto-created dev type for {doc_type}"
                )
                db.add(dev_type)
                await db.flush()
            
            dev_type_id_to_use = dev_type.id
        
        # 5. 准备元数据
        meta_data = {}
        if team_role:
            meta_data['team_role'] = team_role
        if code_function and doc_type == "demo_code":
            meta_data['code_function'] = code_function
        if description:
            meta_data['description'] = description
        
        # 6. 保存文件到磁盘
        # 构建保存路径
        save_dir = Path("uploads") / team_name / project_name
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建完整文件路径
        file_path = save_dir / file.filename
        
        # 保存文件
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"文件已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
        
        # 7. 创建文档记录
        document = Document(
            id=str(uuid.uuid4()),
            title=file.filename,
            content=content_str,
            description=description,
            file_path=str(file_path),  # 使用实际保存的路径
            file_size=file_size,
            mime_type=mime_type,
            dev_type_id=dev_type_id_to_use,
            team_id=team.id,
            project_id=project.id,
            module_id=module_id,
            tags=json.dumps(tags_list) if tags_list else "[]",
            meta_data=json.dumps(meta_data) if meta_data else "{}",
            processing_status=ProcessingStatus.PENDING,
            uploaded_by=uploaded_by,
            created_at=datetime.utcnow()
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"文档创建成功: {document.id}, 文件: {file.filename}")
        
        return {
            "success": True,
            "message": "文档上传成功",
            "document_id": document.id,
            "title": document.title,
            "team": team_name,
            "team_role": team_role,
            "project": project_name,
            "module": module_name,
            "code_function": code_function if doc_type == "demo_code" else None,
            "uploaded_by": uploaded_by,
            "file_size": file_size,
            "mime_type": mime_type,
            "processing_status": document.processing_status.value
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"文档上传失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"文档上传失败: {str(e)}"
        )


@router.get("/search")
async def search_documents(
    query: str,
    doc_type: Optional[str] = None,
    team: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    文档搜索 - 为MCP服务器提供上下文检索
    """
    try:
        # 构建基础查询
        stmt = select(Document)
        
        # 应用搜索条件
        if query:
            stmt = stmt.filter(
                or_(
                    Document.title.contains(query),
                    Document.content.contains(query)
                )
            )
        
        # 按文档类型过滤
        if doc_type:
            doc_type_enum = DocumentType.BUSINESS_DOC if doc_type == "business_doc" else DocumentType.DEMO_CODE
            dev_type_stmt = select(DevType).filter(DevType.category == doc_type_enum)
            dev_type_result = await db.execute(dev_type_stmt)
            dev_types = dev_type_result.scalars().all()
            dev_type_ids = [dt.id for dt in dev_types]
            
            if dev_type_ids:
                stmt = stmt.filter(Document.dev_type_id.in_(dev_type_ids))
        
        # 按团队过滤
        if team:
            team_stmt = select(Team).filter(Team.name == team)
            team_result = await db.execute(team_stmt)
            team_obj = team_result.scalar_one_or_none()
            if team_obj:
                stmt = stmt.filter(Document.team_id == team_obj.id)
        
        # 按项目过滤
        if project:
            project_stmt = select(Project).filter(Project.name == project)
            project_result = await db.execute(project_stmt)
            project_obj = project_result.scalar_one_or_none()
            if project_obj:
                stmt = stmt.filter(Document.project_id == project_obj.id)
        
        # 执行查询
        stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # 格式化结果
        results = []
        for doc in documents:
            # 获取关联的团队、项目名称
            team_obj = await db.get(Team, doc.team_id) if doc.team_id else None
            project_obj = await db.get(Project, doc.project_id) if doc.project_id else None
            
            results.append({
                "id": doc.id,
                "title": doc.title,
                "content": doc.content[:500] + "..." if doc.content and len(doc.content) > 500 else doc.content,
                "team": team_obj.name if team_obj else None,
                "project": project_obj.name if project_obj else None,
                "tags": json.loads(doc.tags) if doc.tags and doc.tags != "[]" else [],
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            })
        
        return results  # 直接返回数组格式
        
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/list")
async def list_documents(
    doc_type: Optional[str] = None,
    team: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    获取文档列表
    """
    try:
        # 构建查询
        stmt = select(Document)
        
        # 按文档类型过滤
        if doc_type:
            doc_type_enum = DocumentType.BUSINESS_DOC if doc_type == "business_doc" else DocumentType.DEMO_CODE
            dev_type_stmt = select(DevType).filter(DevType.category == doc_type_enum)
            dev_type_result = await db.execute(dev_type_stmt)
            dev_types = dev_type_result.scalars().all()
            dev_type_ids = [dt.id for dt in dev_types]
            
            if dev_type_ids:
                stmt = stmt.filter(Document.dev_type_id.in_(dev_type_ids))
        
        # 按团队过滤
        if team:
            team_stmt = select(Team).filter(Team.name == team)
            team_result = await db.execute(team_stmt)
            team_obj = team_result.scalar_one_or_none()
            if team_obj:
                stmt = stmt.filter(Document.team_id == team_obj.id)
        
        # 按项目过滤
        if project:
            project_stmt = select(Project).filter(Project.name == project)
            project_result = await db.execute(project_stmt)
            project_obj = project_result.scalar_one_or_none()
            if project_obj:
                stmt = stmt.filter(Document.project_id == project_obj.id)
        
        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.alias())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # 获取分页数据
        stmt = stmt.offset(offset).limit(limit).order_by(Document.created_at.desc())
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # 格式化结果
        results = []
        for doc in documents:
            # 获取关联的团队、项目名称
            team_obj = await db.get(Team, doc.team_id) if doc.team_id else None
            project_obj = await db.get(Project, doc.project_id) if doc.project_id else None
            dev_type_obj = await db.get(DevType, doc.dev_type_id) if doc.dev_type_id else None
            
            # 解析 meta_data
            meta_data = {}
            if doc.meta_data:
                try:
                    meta_data = json.loads(doc.meta_data)
                except:
                    pass
            
            # 获取上传用户信息
            uploaded_by_name = None
            if doc.uploaded_by:
                from app.models.database import User
                user_obj = await db.get(User, doc.uploaded_by)
                uploaded_by_name = user_obj.username if user_obj else None
            
            results.append({
                "id": doc.id,
                "title": doc.title,
                "team": team_obj.name if team_obj else None,
                "project": project_obj.name if project_obj else None,
                "dev_type": dev_type_obj.name if dev_type_obj else None,
                "doc_type": dev_type_obj.category.value if dev_type_obj else None,
                "tags": json.loads(doc.tags) if doc.tags and doc.tags != "[]" else [],
                "file_size": doc.file_size or 0,
                "processing_status": doc.processing_status.value if doc.processing_status else "unknown",
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "uploaded_by": uploaded_by_name,
                "team_role": meta_data.get('team_role'),
                "code_function": meta_data.get('code_function'),
                "description": meta_data.get('description')
            })
        
        return results  # 直接返回数组格式，前端期望的格式
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.get("/{document_id}")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取文档详情
    """
    try:
        stmt = select(Document).filter(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取关联信息
        team_obj = await db.get(Team, document.team_id) if document.team_id else None
        project_obj = await db.get(Project, document.project_id) if document.project_id else None
        module_obj = await db.get(Module, document.module_id) if document.module_id else None
        
        return {
            "id": document.id,
            "title": document.title,
            "content": document.content,
            "team": team_obj.name if team_obj else None,
            "project": project_obj.name if project_obj else None,
            "module": module_obj.name if module_obj else None,
            "tags": json.loads(document.tags) if document.tags and document.tags != "[]" else [],
            "file_path": document.file_path,
            "file_size": document.file_size,
            "processing_status": document.processing_status.value if document.processing_status else "unknown",
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")


@router.get("/{document_id}/detail")
async def get_document_detail(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取文档详细信息（包含完整内容和元数据）
    """
    try:
        stmt = select(Document).filter(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取关联信息
        team_obj = await db.get(Team, document.team_id) if document.team_id else None
        project_obj = await db.get(Project, document.project_id) if document.project_id else None
        module_obj = await db.get(Module, document.module_id) if document.module_id else None
        dev_type_obj = await db.get(DevType, document.dev_type_id) if document.dev_type_id else None
        
        # 从file_path提取file_name
        file_name = os.path.basename(document.file_path) if document.file_path else document.title
        
        # 计算chunk数量
        from app.models.database import DocumentChunk
        chunk_count_stmt = select(func.count()).select_from(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        )
        chunk_count_result = await db.execute(chunk_count_stmt)
        chunk_count = chunk_count_result.scalar() or 0
        
        # 计算entity数量（暂时返回0，Task 11会实现）
        entity_count = 0
        
        return {
            "id": document.id,
            "title": document.title,
            "description": document.description,
            "doc_type": dev_type_obj.category.value if dev_type_obj else None,
            "content": document.content,
            "file_name": file_name,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "team": {
                "id": team_obj.id,
                "name": team_obj.name,
                "display_name": team_obj.display_name
            } if team_obj else None,
            "project": {
                "id": project_obj.id,
                "name": project_obj.name,
                "display_name": project_obj.display_name
            } if project_obj else None,
            "module": {
                "id": module_obj.id,
                "name": module_obj.name
            } if module_obj else None,
            "dev_type": {
                "id": dev_type_obj.id,
                "name": dev_type_obj.name,
                "display_name": dev_type_obj.display_name,
                "category": dev_type_obj.category.value
            } if dev_type_obj else None,
            "tags": json.loads(document.tags) if document.tags and document.tags != "[]" else [],
            "uploaded_by": document.uploaded_by,
            "processing_status": document.processing_status.value if document.processing_status else "unknown",
            "chunk_count": chunk_count,
            "entity_count": entity_count,
            "access_level": document.access_level.value if document.access_level else "private",
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")


@router.get("/{document_id}/download")
async def download_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    下载文档原始文件
    """
    from fastapi.responses import FileResponse
    
    try:
        stmt = select(Document).filter(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        if not document.file_path or not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 从file_path提取file_name
        file_name = os.path.basename(document.file_path)
        
        # 返回文件
        return FileResponse(
            path=document.file_path,
            filename=file_name,
            media_type=document.mime_type or "application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载文档失败: {str(e)}")


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取文档的chunks列表（如果已进行chunking）
    """
    from app.models.database import DocumentChunk
    
    try:
        # 检查文档是否存在
        stmt = select(Document).filter(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取chunks
        chunks_stmt = select(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)
        
        chunks_result = await db.execute(chunks_stmt)
        chunks = chunks_result.scalars().all()
        
        return {
            "document_id": document_id,
            "document_title": document.title,
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "chunk_size": chunk.chunk_size,
                    "chunk_overlap": chunk.chunk_overlap,
                    "meta_data": chunk.meta_data,
                    "keywords": chunk.keywords,
                    "created_at": chunk.created_at.isoformat() if chunk.created_at else None
                }
                for chunk in chunks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档chunks失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文档chunks失败: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除文档
    """
    try:
        stmt = select(Document).filter(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        await db.delete(document)
        await db.commit()
        
        return {
            "success": True,
            "message": "文档删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.post("/{document_id}/chunk")
async def chunk_document(
    document_id: str,
    max_chunk_size: int = 2000,
    db: AsyncSession = Depends(get_db)
):
    """
    对文档进行智能分块
    
    使用LLM辅助分块服务，根据文档类型选择不同策略：
    - business_doc: 按语义段落分块（LLM辅助）
    - demo_code: 按函数/类分块（保持代码结构）
    - checklist: 按规则项分块
    
    Args:
        document_id: 文档ID
        max_chunk_size: 最大块大小（字符数），默认2000
    
    Returns:
        分块统计信息和预览
    """
    try:
        from app.models.database import DocumentChunk
        from app.services.llm_chunking_service import get_chunking_service
        
        # 1. 获取文档和关联的DevType
        stmt = select(Document).filter(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        if not document.content:
            raise HTTPException(status_code=400, detail="文档内容为空，无法分块")
        
        # 获取DevType以确定文档类型
        dev_type = await db.get(DevType, document.dev_type_id)
        if not dev_type:
            raise HTTPException(status_code=400, detail="文档类型信息不存在")
        
        doc_type = dev_type.category  # DocumentType枚举值
        file_name = document.title or ""
        
        # 2. 更新处理状态
        document.processing_status = ProcessingStatus.PROCESSING
        await db.commit()
        
        try:
            # 3. 调用分块服务
            chunking_service = get_chunking_service()
            chunks_data = await chunking_service.chunk_document(
                content=document.content,
                doc_type=doc_type,
                file_name=file_name,
                max_chunk_size=max_chunk_size
            )
            
            # 4. 删除旧的chunks（如果有）
            delete_stmt = select(DocumentChunk).filter(DocumentChunk.document_id == document_id)
            old_chunks = await db.execute(delete_stmt)
            for old_chunk in old_chunks.scalars():
                await db.delete(old_chunk)
            
            # 5. 保存新的chunks到数据库
            saved_chunks = []
            for chunk_data in chunks_data:
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=chunk_data["content"],
                    chunk_index=chunk_data["chunk_index"],
                    chunk_size=len(chunk_data["content"]),
                    chunk_overlap=0,  # 当前版本不使用overlap
                    meta_data=json.dumps(chunk_data.get("metadata", {})),
                    keywords="[]"  # 后续可以添加关键词提取
                )
                db.add(chunk)
                saved_chunks.append({
                    "chunk_index": chunk.chunk_index,
                    "chunk_size": chunk.chunk_size,
                    "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "token_count": chunk_data.get("token_count", 0),
                    "metadata": chunk_data.get("metadata", {})
                })
            
            # 6. 更新文档状态
            document.processing_status = ProcessingStatus.COMPLETED
            await db.commit()
            
            logger.info(f"文档分块完成: document_id={document_id}, chunks_count={len(saved_chunks)}")
            
            return {
                "success": True,
                "document_id": document_id,
                "doc_type": doc_type,
                "total_chunks": len(saved_chunks),
                "total_size": len(document.content),
                "average_chunk_size": sum(c["chunk_size"] for c in saved_chunks) // len(saved_chunks) if saved_chunks else 0,
                "chunks_preview": saved_chunks[:5],  # 只返回前5个chunk的预览
                "message": f"成功创建 {len(saved_chunks)} 个文档块"
            }
            
        except Exception as chunk_error:
            # 分块失败，更新状态
            document.processing_status = ProcessingStatus.FAILED
            await db.commit()
            logger.error(f"分块处理失败: {str(chunk_error)}")
            raise HTTPException(status_code=500, detail=f"分块处理失败: {str(chunk_error)}")
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"分块API失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分块API失败: {str(e)}")


@router.post("/{document_id}/embed")
async def embed_document_chunks(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    为文档的所有chunks生成向量
    
    使用Qwen3-Embedding-8B为每个chunk生成8192维向量，存储到embedding字段
    
    Args:
        document_id: 文档ID
    
    Returns:
        向量化统计信息
    """
    try:
        from app.models.database import DocumentChunk
        from app.services.embedding_service import get_embedding_service
        
        # 1. 检查文档是否存在
        stmt = select(Document).filter(Document.id == document_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 2. 获取所有chunks
        chunks_stmt = select(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)
        
        chunks_result = await db.execute(chunks_stmt)
        chunks = chunks_result.scalars().all()
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="文档尚未分块，请先调用 /chunk 接口"
            )
        
        logger.info(f"开始为文档 {document_id} 的 {len(chunks)} 个chunks生成向量")
        
        # 3. 准备chunks数据
        chunks_data = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index
            }
            for chunk in chunks
        ]
        
        # 4. 定义更新回调函数
        async def update_chunk_embedding(chunk_id: str, embedding: str, embedding_dim: int):
            """更新chunk的embedding字段"""
            chunk = await db.get(DocumentChunk, chunk_id)
            if chunk:
                chunk.embedding = embedding
                # 可以在meta_data中记录embedding维度
                try:
                    meta_data = json.loads(chunk.meta_data) if chunk.meta_data else {}
                    meta_data["embedding_dim"] = embedding_dim
                    chunk.meta_data = json.dumps(meta_data)
                except:
                    pass
        
        # 5. 调用embedding服务
        embedding_service = get_embedding_service()
        stats = await embedding_service.embed_chunks_for_document(
            chunks=chunks_data,
            update_callback=update_chunk_embedding
        )
        
        # 6. 提交数据库更新
        await db.commit()
        
        logger.info(
            f"文档向量化完成: document_id={document_id}",
            **stats
        )
        
        return {
            "success": True,
            "document_id": document_id,
            "document_title": document.title,
            "embedding_stats": stats,
            "message": f"成功为 {stats['success']} 个chunks生成向量"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"向量化API失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"向量化API失败: {str(e)}")
