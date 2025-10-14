"""
数据库模型定义 - SQLite 兼容版本
"""

from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, Boolean, DateTime, Float,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime

from app.core.database import Base


# 枚举类型
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager" 
    DEVELOPER = "developer"


class DocumentType(str, enum.Enum):
    BUSINESS_DOC = "business_doc"
    DEMO_CODE = "demo_code"
    CHECKLIST = "checklist"  # 规范文档：代码规范、流程规范、检查清单等


class AccessLevel(str, enum.Enum):
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"


# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar_url = Column(Text)
    role = Column(SQLEnum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    teams = Column(Text, default="[]")  # JSON 字符串存储数组
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


# 团队模型
class Team(Base):
    __tablename__ = "teams"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    tech_stack = Column(Text, default="[]")  # JSON 字符串
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 项目模型
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    tech_stack = Column(Text, default="[]")  # JSON 字符串
    repository_url = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 模块模型
class Module(Base):
    __tablename__ = "modules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    module_type = Column(String(50))  # api, service, component, utils等
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 开发类型模型
class DevType(Base):
    __tablename__ = "dev_types"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(SQLEnum(DocumentType), nullable=False)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


# 文档模型
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text)
    file_path = Column(Text)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    
    # 分类信息
    dev_type_id = Column(String(36), ForeignKey("dev_types.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"))
    project_id = Column(String(36), ForeignKey("projects.id"))
    module_id = Column(String(36), ForeignKey("modules.id"))
    
    # 访问控制
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.PRIVATE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 处理状态
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    
    # 元数据
    meta_data = Column(Text, default="{}")  # JSON 字符串
    tags = Column(Text, default="[]")  # JSON 字符串
    keywords = Column(Text, default="[]")  # JSON 字符串
    
    # 用户信息
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 文档块模型 (用于向量检索)
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text)  # 存储序列化的向量
    chunk_index = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    chunk_overlap = Column(Integer, default=0)
    keywords = Column(Text, default="[]")  # JSON 字符串
    meta_data = Column(Text, default="{}")  # JSON 字符串
    created_at = Column(DateTime, server_default=func.now())


# 实体模型 (知识图谱)
class Entity(Base):
    __tablename__ = "entities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)  # class, function, variable等
    description = Column(Text)
    properties = Column(Text, default="{}")  # JSON 字符串
    source_location = Column(String(500))  # 源代码位置
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 关系模型 (知识图谱)
class Relation(Base):
    __tablename__ = "relations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("entities.id"), nullable=False)
    target_id = Column(String(36), ForeignKey("entities.id"), nullable=False)
    relation_type = Column(String(100), nullable=False)  # depends_on, implements, calls等
    weight = Column(Float, default=1.0)
    properties = Column(Text, default="{}")  # JSON 字符串
    created_at = Column(DateTime, server_default=func.now())


# 用户会话模型
class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# 审计日志模型
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    action = Column(SQLEnum(AuditAction), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(36))
    old_values = Column(Text)  # JSON 字符串
    new_values = Column(Text)  # JSON 字符串
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


# 文档访问日志模型
class DocumentAccessLog(Base):
    __tablename__ = "document_access_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    access_type = Column(String(50), nullable=False)  # view, download, search等
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.now())