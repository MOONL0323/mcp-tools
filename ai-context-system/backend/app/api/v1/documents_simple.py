"""
文档处理 API - 完整可用版本
直接连接到Graph RAG处理Pipeline
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.services.document_processing_pipeline import document_processor
from app.services.embedding_service import embedding_service

router = APIRouter()

# 上传目录
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    type: str = Form("business_doc"),  # business_doc 或 demo_code
    team: str = Form(""),
    project: str = Form(""),
    module: str = Form(""),
    dev_type: str = Form(""),
    access_level: str = Form("team"),
    tags: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    """
    上传并处理文档
    
    立即返回文档ID，后台异步处理
    """
    try:
        # 生成文档ID
        document_id = str(uuid.uuid4())
        
        # 保存文件
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{document_id}{file_ext}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 解析tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # 创建文档记录
        await db.execute(
            """
            INSERT INTO documents (
                id, title, description, type, team, project, module, dev_type,
                file_name, file_path, file_size, upload_time, processing_status,
                access_level, tags
            ) VALUES (
                :id, :title, :description, :type, :team, :project, :module, :dev_type,
                :file_name, :file_path, :file_size, :upload_time, :status,
                :access_level, :tags
            )
            """,
            {
                "id": document_id,
                "title": title,
                "description": description,
                "type": type,
                "team": team,
                "project": project,
                "module": module,
                "dev_type": dev_type,
                "file_name": file.filename,
                "file_path": str(file_path),
                "file_size": len(content),
                "upload_time": datetime.utcnow(),
                "status": "processing",
                "access_level": access_level,
                "tags": ",".join(tag_list)
            }
        )
        await db.commit()
        
        # 后台处理文档
        background_tasks.add_task(
            process_document_background,
            document_id,
            str(file_path),
            type
        )
        
        logger.info(f"文档上传成功: {document_id}, 开始后台处理")
        
        return {
            "document_id": document_id,
            "status": "processing",
            "message": "文档上传成功，正在后台处理"
        }
        
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_background(
    document_id: str,
    file_path: str,
    document_type: str
):
    """后台处理文档"""
    try:
        # 注意：这里需要创建新的数据库session
        from app.core.database import async_session_maker
        async with async_session_maker() as db:
            await document_processor.process_document(
                document_id=document_id,
                file_path=file_path,
                document_type=document_type,
                db=db
            )
    except Exception as e:
        logger.error(f"后台处理失败: {e}")


@router.get("/")
async def get_documents(
    skip: int = 0,
    limit: int = 20,
    type: Optional[str] = None,
    team: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取文档列表"""
    try:
        # 构建查询条件
        conditions = []
        params = {"skip": skip, "limit": limit}
        
        if type:
            conditions.append("type = :type")
            params["type"] = type
        if team:
            conditions.append("team = :team")
            params["team"] = team
        if status:
            conditions.append("processing_status = :status")
            params["status"] = status
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        result = await db.execute(
            f"""
            SELECT * FROM documents
            {where_clause}
            ORDER BY upload_time DESC
            LIMIT :limit OFFSET :skip
            """,
            params
        )
        
        documents = result.fetchall()
        
        return {
            "documents": [dict(row) for row in documents],
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取文档详情"""
    try:
        result = await db.execute(
            "SELECT * FROM documents WHERE id = :id",
            {"id": document_id}
        )
        document = result.fetchone()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return dict(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除文档"""
    try:
        # 删除向量和图谱数据
        await document_processor.delete_document_data(document_id)
        
        # 删除数据库记录
        await db.execute(
            "DELETE FROM documents WHERE id = :id",
            {"id": document_id}
        )
        await db.commit()
        
        logger.info(f"文档删除成功: {document_id}")
        
        return {"message": "文档删除成功"}
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(
    query: str = Form(...),
    n_results: int = Form(10),
    type: Optional[str] = Form(None),
    team: Optional[str] = Form(None)
):
    """搜索文档（向量搜索）"""
    try:
        # 构建过滤条件
        filters = {}
        if type:
            filters["type"] = type
        if team:
            filters["team"] = team
        
        # 向量搜索
        results = await embedding_service.search_similar_chunks(
            query=query,
            n_results=n_results,
            filters=filters if filters else None
        )
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    n_results: int = 100
):
    """获取文档的所有chunks"""
    try:
        from app.services.chroma_client import chroma_client
        
        collection = chroma_client.get_or_create_collection()
        results = collection.get(
            where={"document_id": document_id},
            limit=n_results,
            include=["documents", "metadatas"]
        )
        
        chunks = []
        for i in range(len(results['ids'])):
            chunks.append({
                "id": results['ids'][i],
                "content": results['documents'][i],
                "metadata": results['metadatas'][i]
            })
        
        return {
            "document_id": document_id,
            "chunks": chunks,
            "total": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"获取文档chunks失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/entities")
async def get_document_entities(
    document_id: str
):
    """获取文档的实体"""
    try:
        from app.services.neo4j_client import neo4j_client
        
        entities = await neo4j_client.search_entities(
            name_pattern=None,
            limit=100
        )
        
        # 过滤该文档的实体
        doc_entities = [
            e for e in entities 
            if e.get('properties', {}).get('document_id') == document_id
        ]
        
        return {
            "document_id": document_id,
            "entities": doc_entities,
            "total": len(doc_entities)
        }
        
    except Exception as e:
        logger.error(f"获取文档实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
