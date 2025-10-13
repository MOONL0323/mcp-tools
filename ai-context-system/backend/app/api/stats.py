"""
统计数据API接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.database import get_db
from app.models.database import Document, DocumentChunk, Entity, Relation, User
from app.schemas.stats import DashboardStats, DocumentStats, EntityStats
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表板统计数据"""
    try:
        # 文档统计
        total_documents = db.query(func.count(Document.id)).scalar() or 0
        processing_documents = db.query(func.count(Document.id)).filter(
            Document.status == 'processing'
        ).scalar() or 0
        completed_documents = db.query(func.count(Document.id)).filter(
            Document.status == 'completed'
        ).scalar() or 0
        
        # 文本块统计
        total_chunks = db.query(func.count(DocumentChunk.id)).scalar() or 0
        
        # 实体和关系统计
        total_entities = db.query(func.count(Entity.id)).scalar() or 0
        total_relations = db.query(func.count(Relation.id)).scalar() or 0
        
        # 团队成员统计
        team_members = db.query(func.count(User.id)).filter(
            User.is_active == True
        ).scalar() or 0
        
        # 知识图谱数量（按项目分组计算）
        knowledge_graphs = db.query(func.count(func.distinct(Document.project))).scalar() or 0
        
        return DashboardStats(
            totalDocuments=total_documents,
            processingDocuments=processing_documents,
            completedDocuments=completed_documents,
            totalChunks=total_chunks,
            totalEntities=total_entities,
            totalRelations=total_relations,
            teamMembers=team_members,
            knowledgeGraphs=knowledge_graphs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/documents", response_model=DocumentStats)
async def get_document_stats(db: Session = Depends(get_db)):
    """获取文档详细统计"""
    try:
        # 总数统计
        total = db.query(func.count(Document.id)).scalar() or 0
        processing = db.query(func.count(Document.id)).filter(
            Document.status == 'processing'
        ).scalar() or 0
        completed = db.query(func.count(Document.id)).filter(
            Document.status == 'completed'
        ).scalar() or 0
        failed = db.query(func.count(Document.id)).filter(
            Document.status == 'failed'
        ).scalar() or 0
        
        # 按类型统计
        business_docs = db.query(func.count(Document.id)).filter(
            Document.doc_type == 'business_doc'
        ).scalar() or 0
        demo_code = db.query(func.count(Document.id)).filter(
            Document.doc_type == 'demo_code'
        ).scalar() or 0
        
        # 按时间统计（最近7天）
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_uploads = db.query(func.count(Document.id)).filter(
            Document.created_at >= seven_days_ago
        ).scalar() or 0
        
        # 按团队统计
        team_stats = db.query(
            Document.team,
            func.count(Document.id).label('count')
        ).filter(
            Document.team.isnot(None)
        ).group_by(Document.team).all()
        
        team_distribution = {team: count for team, count in team_stats}
        
        return DocumentStats(
            total=total,
            processing=processing,
            completed=completed,
            failed=failed,
            business_docs=business_docs,
            demo_code=demo_code,
            recent_uploads=recent_uploads,
            team_distribution=team_distribution
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档统计失败: {str(e)}")

@router.get("/entities", response_model=EntityStats)
async def get_entity_stats(db: Session = Depends(get_db)):
    """获取实体统计数据"""
    try:
        # 总数统计
        total_entities = db.query(func.count(Entity.id)).scalar() or 0
        total_relations = db.query(func.count(Relation.id)).scalar() or 0
        
        # 按类型统计实体
        entity_types = db.query(
            Entity.entity_type,
            func.count(Entity.id).label('count')
        ).group_by(Entity.entity_type).all()
        
        entity_type_distribution = {entity_type: count for entity_type, count in entity_types}
        
        # 按类型统计关系
        relation_types = db.query(
            Relation.relation_type,
            func.count(Relation.id).label('count')
        ).group_by(Relation.relation_type).all()
        
        relation_type_distribution = {relation_type: count for relation_type, count in relation_types}
        
        return EntityStats(
            total_entities=total_entities,
            total_relations=total_relations,
            entity_type_distribution=entity_type_distribution,
            relation_type_distribution=relation_type_distribution
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体统计失败: {str(e)}")

@router.get("/chunks")
async def get_chunk_stats(db: Session = Depends(get_db)):
    """获取文本块统计"""
    try:
        total = db.query(func.count(DocumentChunk.id)).scalar() or 0
        
        # 按文档类型统计
        chunk_stats = db.query(
            Document.doc_type,
            func.count(DocumentChunk.id).label('chunk_count'),
            func.avg(func.length(DocumentChunk.content)).label('avg_length')
        ).join(
            DocumentChunk, Document.id == DocumentChunk.document_id
        ).group_by(Document.doc_type).all()
        
        type_distribution = {}
        avg_lengths = {}
        
        for doc_type, chunk_count, avg_length in chunk_stats:
            type_distribution[doc_type] = chunk_count
            avg_lengths[doc_type] = round(avg_length or 0)
        
        return {
            "total": total,
            "type_distribution": type_distribution,
            "avg_lengths": avg_lengths
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文本块统计失败: {str(e)}")

@router.get("/users")
async def get_user_stats(db: Session = Depends(get_db)):
    """获取用户统计"""
    try:
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(
            User.is_active == True
        ).scalar() or 0
        
        # 按角色统计
        role_stats = db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()
        
        role_distribution = {role: count for role, count in role_stats}
        
        # 最近注册用户（30天内）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_registrations = db.query(func.count(User.id)).filter(
            User.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # 活跃项目数（有文档上传的项目）
        active_projects = db.query(func.count(func.distinct(Document.project))).filter(
            Document.project.isnot(None)
        ).scalar() or 0
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "role_distribution": role_distribution,
            "recent_registrations": recent_registrations,
            "active_projects": active_projects
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")