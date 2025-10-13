"""
统计数据的Pydantic模型
"""

from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class DashboardStats(BaseModel):
    """仪表板统计数据"""
    totalDocuments: int = 0
    processingDocuments: int = 0
    completedDocuments: int = 0
    totalChunks: int = 0
    totalEntities: int = 0
    totalRelations: int = 0
    teamMembers: int = 0
    knowledgeGraphs: int = 0

class DocumentStats(BaseModel):
    """文档统计数据"""
    total: int
    processing: int
    completed: int
    failed: int
    business_docs: int
    demo_code: int
    recent_uploads: int
    team_distribution: Dict[str, int] = {}

class EntityStats(BaseModel):
    """实体统计数据"""
    total_entities: int
    total_relations: int
    entity_type_distribution: Dict[str, int] = {}
    relation_type_distribution: Dict[str, int] = {}

class ChunkStats(BaseModel):
    """文本块统计数据"""
    total: int
    type_distribution: Dict[str, int] = {}
    avg_lengths: Dict[str, int] = {}

class UserStats(BaseModel):
    """用户统计数据"""
    total_users: int
    active_users: int
    role_distribution: Dict[str, int] = {}
    recent_registrations: int
    active_projects: int

class SystemHealthStats(BaseModel):
    """系统健康状态统计"""
    api_status: str = "healthy"
    database_status: str = "healthy"
    vector_db_status: str = "healthy"
    graph_db_status: str = "healthy"
    last_updated: datetime
    
class ProcessingStats(BaseModel):
    """处理任务统计"""
    total_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_processing_time: float = 0.0  # 平均处理时间（秒）