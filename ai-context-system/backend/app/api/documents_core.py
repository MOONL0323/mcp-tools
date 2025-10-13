"""
简化的文档管理API - 符合AI代码生成系统方案核心目标
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.database import Document
from datetime import datetime

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),  # business_doc 或 demo_code
    team: str = Form(...),
    project: str = Form(...),
    module: str = Form(None),
    tags: str = Form("[]"),  # JSON字符串格式的标签
    db: Session = Depends(get_db)
):
    """
    上传文档或代码文件 - 核心功能：为AI Agent提供上下文
    """
    try:
        # 读取文件内容
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # 解析标签
        import json
        try:
            tags_list = json.loads(tags) if tags != "[]" else []
        except:
            tags_list = []
        
        # 创建文档记录
        document = Document(
            title=file.filename,
            content=content_str,
            doc_type=doc_type,
            team=team,
            project=project,
            module=module,
            tags=tags_list,
            file_path=f"uploads/{team}/{project}/{file.filename}",
            created_at=datetime.utcnow()
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "success": True,
            "message": "文档上传成功",
            "data": {
                "id": document.id,
                "title": document.title,
                "doc_type": document.doc_type,
                "team": document.team,
                "project": document.project
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"文档上传失败: {str(e)}"
        }

@router.get("/search")
async def search_documents(
    query: str,
    doc_type: Optional[str] = None,
    team: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    文档搜索 - 为MCP服务器提供上下文检索
    """
    try:
        # 构建基础查询
        db_query = db.query(Document)
        
        # 应用过滤条件
        if query:
            db_query = db_query.filter(
                Document.title.contains(query) |
                Document.content.contains(query)
            )
        
        if doc_type:
            db_query = db_query.filter(Document.doc_type == doc_type)
            
        if team:
            db_query = db_query.filter(Document.team == team)
            
        if project:
            db_query = db_query.filter(Document.project == project)
        
        # 执行查询
        documents = db_query.limit(limit).all()
        
        # 格式化结果
        results = []
        for doc in documents:
            results.append({
                "id": doc.id,
                "title": doc.title,
                "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                "doc_type": doc.doc_type,
                "team": doc.team,
                "project": doc.project,
                "module": doc.module,
                "tags": doc.tags or [],
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            })
        
        return {
            "success": True,
            "data": results,
            "total": len(results)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"搜索失败: {str(e)}"
        }

@router.get("/list")
async def list_documents(
    doc_type: Optional[str] = None,
    team: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取文档列表
    """
    try:
        # 构建查询
        query = db.query(Document)
        
        if doc_type:
            query = query.filter(Document.doc_type == doc_type)
        if team:
            query = query.filter(Document.team == team)
        if project:
            query = query.filter(Document.project == project)
        
        # 获取总数和分页数据
        total = query.count()
        documents = query.offset(offset).limit(limit).all()
        
        # 格式化结果
        results = []
        for doc in documents:
            results.append({
                "id": doc.id,
                "title": doc.title,
                "doc_type": doc.doc_type,
                "team": doc.team,
                "project": doc.project,
                "module": doc.module,
                "tags": doc.tags or [],
                "file_size": len(doc.content) if doc.content else 0,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            })
        
        return {
            "success": True,
            "data": {
                "documents": results,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取文档列表失败: {str(e)}"
        }

@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    获取文档详情
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {
            "success": True,
            "data": {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "doc_type": document.doc_type,
                "team": document.team,
                "project": document.project,
                "module": document.module,
                "tags": document.tags or [],
                "file_path": document.file_path,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": f"获取文档失败: {str(e)}"
        }

@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    删除文档
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        db.delete(document)
        db.commit()
        
        return {
            "success": True,
            "message": "文档删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": f"删除文档失败: {str(e)}"
        }