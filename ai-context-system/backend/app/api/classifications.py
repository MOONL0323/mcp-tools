"""
分类管理API
提供团队分类、文档类型分类等信息
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.database import Team, DevType, DocumentType
from pydantic import BaseModel

router = APIRouter(prefix="/classifications", tags=["分类管理"])


class DevTypeInfo(BaseModel):
    """开发类型信息"""
    id: str
    category: str
    name: str
    display_name: str
    description: str | None
    icon: str | None
    sort_order: int


class TeamInfo(BaseModel):
    """团队信息"""
    id: str
    name: str
    display_name: str
    description: str | None


@router.get("/dev-types")
async def get_dev_types(
    category: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> List[DevTypeInfo]:
    """
    获取开发类型分类列表
    
    参数:
    - category: 可选，过滤特定类别 (business_doc, demo_code)
    """
    query = select(DevType).order_by(DevType.sort_order)
    
    if category:
        try:
            doc_type = DocumentType(category)
            query = query.filter(DevType.category == doc_type)
        except ValueError:
            pass
    
    result = await db.execute(query)
    dev_types = result.scalars().all()
    
    return [
        DevTypeInfo(
            id=dt.id,
            category=dt.category.value,
            name=dt.name,
            display_name=dt.display_name,
            description=dt.description,
            icon=dt.icon,
            sort_order=dt.sort_order
        )
        for dt in dev_types
    ]


@router.get("/teams")
async def get_teams(
    db: AsyncSession = Depends(get_db)
) -> List[TeamInfo]:
    """获取所有团队列表"""
    result = await db.execute(
        select(Team).order_by(Team.name)
    )
    teams = result.scalars().all()
    
    return [
        TeamInfo(
            id=team.id,
            name=team.name,
            display_name=team.display_name,
            description=team.description
        )
        for team in teams
    ]


@router.get("/options")
async def get_classification_options(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取所有分类选项
    一次性返回所有下拉选项，减少前端请求
    """
    # 获取业务文档分类
    business_doc_result = await db.execute(
        select(DevType)
        .filter(DevType.category == DocumentType.BUSINESS_DOC)
        .order_by(DevType.sort_order)
    )
    business_docs = business_doc_result.scalars().all()
    
    # 获取Demo代码分类
    demo_code_result = await db.execute(
        select(DevType)
        .filter(DevType.category == DocumentType.DEMO_CODE)
        .order_by(DevType.sort_order)
    )
    demo_codes = demo_code_result.scalars().all()
    
    # 获取规范文档分类（Checklist）
    checklist_result = await db.execute(
        select(DevType)
        .filter(DevType.category == DocumentType.CHECKLIST)
        .order_by(DevType.sort_order)
    )
    checklists = checklist_result.scalars().all()
    
    # 获取团队列表
    teams_result = await db.execute(
        select(Team).order_by(Team.name)
    )
    teams = teams_result.scalars().all()
    
    return {
        "business_doc_types": [
            {
                "id": dt.id,
                "name": dt.name,
                "display_name": dt.display_name,
                "description": dt.description,
                "icon": dt.icon
            }
            for dt in business_docs
        ],
        "demo_code_types": [
            {
                "id": dt.id,
                "name": dt.name,
                "display_name": dt.display_name,
                "description": dt.description,
                "icon": dt.icon
            }
            for dt in demo_codes
        ],
        "checklist_types": [
            {
                "id": dt.id,
                "name": dt.name,
                "display_name": dt.display_name,
                "description": dt.description,
                "icon": dt.icon
            }
            for dt in checklists
        ],
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "display_name": team.display_name,
                "description": team.description
            }
            for team in teams
        ]
    }
