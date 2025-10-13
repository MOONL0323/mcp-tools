"""
Pydantic模式定义 - 用于API请求和响应
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from uuid import UUID

from app.models.database import (
    UserRole, DocumentType, AccessLevel, 
    ProcessingStatus, AuditAction
)


# 基础模式
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True


# 用户相关模式
class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.DEVELOPER
    teams: List[str] = []


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含字母')
        return v


class UserUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    teams: Optional[List[str]] = None


class UserInDB(UserBase):
    id: UUID
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class UserResponse(UserInDB):
    pass


class UserLogin(BaseSchema):
    username: str
    password: str


class UserChangePassword(BaseSchema):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含字母')
        return v


# 团队相关模式
class TeamBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tech_stack: List[str] = []


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseSchema):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = None


class TeamInDB(TeamBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class TeamResponse(TeamInDB):
    pass


# 项目相关模式
class ProjectBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tech_stack: List[str] = []
    repository_url: Optional[str] = None


class ProjectCreate(ProjectBase):
    team_id: UUID


class ProjectUpdate(BaseSchema):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    repository_url: Optional[str] = None


class ProjectInDB(ProjectBase):
    id: UUID
    team_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ProjectResponse(ProjectInDB):
    team: Optional["TeamResponse"] = None


# 模块相关模式
class ModuleBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    module_type: Optional[str] = None


class ModuleCreate(ModuleBase):
    project_id: UUID


class ModuleUpdate(BaseSchema):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    module_type: Optional[str] = None


class ModuleInDB(ModuleBase):
    id: UUID
    project_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ModuleResponse(ModuleInDB):
    project: Optional["ProjectResponse"] = None


# 开发类型相关模式
class DevTypeBase(BaseSchema):
    category: DocumentType
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


class DevTypeCreate(DevTypeBase):
    pass


class DevTypeUpdate(BaseSchema):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class DevTypeInDB(DevTypeBase):
    id: UUID
    created_at: datetime


class DevTypeResponse(DevTypeInDB):
    pass


# 文档相关模式
class DocumentBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: DocumentType
    access_level: AccessLevel = AccessLevel.TEAM
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    version: str = "1.0"


class DocumentCreate(DocumentBase):
    team_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    module_id: Optional[UUID] = None
    dev_type_id: Optional[UUID] = None


class DocumentUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    access_level: Optional[AccessLevel] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentInDB(DocumentBase):
    id: UUID
    team_id: Optional[UUID]
    project_id: Optional[UUID]
    module_id: Optional[UUID]
    dev_type_id: Optional[UUID]
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    file_hash: Optional[str]
    status: ProcessingStatus
    chunk_count: int
    entity_count: int
    processing_error: Optional[str]
    download_count: int
    view_count: int
    uploaded_by: UUID
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]


class DocumentResponse(DocumentInDB):
    team: Optional["TeamResponse"] = None
    project: Optional["ProjectResponse"] = None
    module: Optional["ModuleResponse"] = None
    dev_type: Optional["DevTypeResponse"] = None
    uploader: Optional["UserResponse"] = None


class DocumentUpload(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: DocumentType
    team_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    module_id: Optional[UUID] = None
    dev_type_id: Optional[UUID] = None
    access_level: AccessLevel = AccessLevel.TEAM
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


# 文档块相关模式
class DocumentChunkBase(BaseSchema):
    content: str
    title: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = []
    content_type: Optional[str] = None
    chunk_index: int
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    metadata: Dict[str, Any] = {}


class DocumentChunkInDB(DocumentChunkBase):
    id: UUID
    document_id: UUID
    embedding_model: Optional[str]
    created_at: datetime


class DocumentChunkResponse(DocumentChunkInDB):
    pass


# 实体相关模式
class EntityBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    properties: Dict[str, Any] = {}


class EntityInDB(EntityBase):
    id: UUID
    document_id: UUID
    chunk_ids: List[UUID] = []
    created_at: datetime
    updated_at: datetime


class EntityResponse(EntityInDB):
    document: Optional["DocumentResponse"] = None


# 关系相关模式
class RelationBase(BaseSchema):
    relation_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    properties: Dict[str, Any] = {}


class RelationInDB(RelationBase):
    id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    created_at: datetime


class RelationResponse(RelationInDB):
    source_entity: Optional["EntityResponse"] = None
    target_entity: Optional["EntityResponse"] = None


# 搜索相关模式
class DocumentSearchRequest(BaseSchema):
    query: str = Field(..., min_length=1, max_length=500)
    document_type: Optional[DocumentType] = None
    team_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    module_id: Optional[UUID] = None
    dev_type_id: Optional[UUID] = None
    tags: List[str] = []
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class DocumentSearchResult(BaseSchema):
    document: DocumentResponse
    chunks: List[DocumentChunkResponse] = []
    score: float
    highlights: List[str] = []


class DocumentSearchResponse(BaseSchema):
    results: List[DocumentSearchResult]
    total: int
    query: str
    limit: int
    offset: int


# 图搜索相关模式
class GraphSearchRequest(BaseSchema):
    query: str = Field(..., min_length=1, max_length=500)
    entity_types: List[str] = []
    relation_types: List[str] = []
    depth: int = Field(default=2, ge=1, le=5)
    limit: int = Field(default=20, ge=1, le=100)


class GraphNode(BaseSchema):
    id: UUID
    name: str
    type: str
    description: Optional[str]
    properties: Dict[str, Any] = {}


class GraphEdge(BaseSchema):
    id: UUID
    source: UUID
    target: UUID
    type: str
    description: Optional[str]
    confidence: float
    properties: Dict[str, Any] = {}


class GraphSearchResponse(BaseSchema):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    query: str
    total_nodes: int
    total_edges: int


# 统计相关模式
class DocumentStats(BaseSchema):
    total_documents: int
    total_chunks: int
    total_entities: int
    total_relations: int
    by_type: Dict[str, int]
    by_team: Dict[str, int]
    by_status: Dict[str, int]
    recent_uploads: List[DocumentResponse]


class UserStats(BaseSchema):
    total_users: int
    active_users: int
    by_role: Dict[str, int]
    by_team: Dict[str, int]
    recent_logins: List[UserResponse]


class SystemStats(BaseSchema):
    documents: DocumentStats
    users: UserStats
    storage_used: int
    processing_queue: int


# 批处理相关模式
class BatchProcessRequest(BaseSchema):
    document_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., pattern="^(reprocess|delete|export)$")
    options: Dict[str, Any] = {}


class BatchProcessResponse(BaseSchema):
    task_id: UUID
    total_items: int
    message: str


# 导出相关模式
class ExportRequest(BaseSchema):
    document_ids: List[UUID] = Field(..., min_items=1, max_items=1000)
    format: str = Field(..., pattern="^(json|csv|markdown)$")
    include_chunks: bool = True
    include_entities: bool = True
    include_relations: bool = True


class ExportResponse(BaseSchema):
    task_id: UUID
    estimated_size: int
    download_url: Optional[str] = None
    message: str


# 令牌相关模式
class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseSchema):
    refresh_token: str


# 更新模式之间的前向引用
ProjectResponse.model_rebuild()
ModuleResponse.model_rebuild()
DocumentResponse.model_rebuild()
EntityResponse.model_rebuild()
RelationResponse.model_rebuild()