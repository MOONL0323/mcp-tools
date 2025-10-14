"""
初始化预定义数据
- 团队分类
- Demo代码分类
- 默认团队
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import Team, DevType, DocumentType
from app.core.database import get_db, init_db
import uuid
import asyncio


# 团队分类
TEAM_CATEGORIES = [
    {"name": "前端", "description": "前端开发团队，负责UI/UX和前端架构"},
    {"name": "后端", "description": "后端开发团队，负责API和业务逻辑"},
    {"name": "测试", "description": "测试团队，负责质量保证和自动化测试"},
    {"name": "规划", "description": "产品规划团队，负责需求分析和产品设计"},
    {"name": "其它", "description": "其他团队或跨职能团队"},
]

# 默认团队
DEFAULT_TEAM = {
    "name": "xaas开发组",
    "display_name": "XaaS开发组",
    "description": "XaaS平台核心开发团队"
}

# Demo代码分类
DEMO_CODE_CATEGORIES = [
    {
        "name": "api",
        "display_name": "API接口",
        "description": "RESTful API、GraphQL等接口实现示例",
        "icon": "api"
    },
    {
        "name": "pkg",
        "display_name": "工具包",
        "description": "可复用的工具包、库和模块",
        "icon": "package"
    },
    {
        "name": "cmd",
        "display_name": "命令行",
        "description": "CLI工具和脚本",
        "icon": "code"
    },
    {
        "name": "test",
        "display_name": "单元测试",
        "description": "单元测试、集成测试示例代码",
        "icon": "experiment"
    },
    {
        "name": "other",
        "display_name": "其它",
        "description": "其他类型的示例代码",
        "icon": "ellipsis"
    },
]

# 业务文档分类
BUSINESS_DOC_CATEGORIES = [
    {
        "name": "requirement",
        "display_name": "需求文档",
        "description": "产品需求、功能规格说明",
        "icon": "file-text"
    },
    {
        "name": "design",
        "display_name": "设计文档",
        "description": "系统设计、架构设计文档",
        "icon": "deployment-unit"
    },
    {
        "name": "api_doc",
        "display_name": "API文档",
        "description": "API接口文档和说明",
        "icon": "api"
    },
    {
        "name": "guide",
        "display_name": "使用指南",
        "description": "用户手册、开发指南",
        "icon": "read"
    },
    {
        "name": "other",
        "display_name": "其它",
        "description": "其他类型的项目文档",
        "icon": "ellipsis"
    },
]

# 规范文档分类（Checklist）
CHECKLIST_CATEGORIES = [
    {
        "name": "coding_standard",
        "display_name": "代码规范",
        "description": "编码规范、代码风格指南",
        "icon": "code"
    },
    {
        "name": "process_standard",
        "display_name": "流程规范",
        "description": "开发流程、评审流程、发布流程",
        "icon": "project"
    },
    {
        "name": "quality_checklist",
        "display_name": "质量检查",
        "description": "代码审查清单、测试检查清单",
        "icon": "check-circle"
    },
    {
        "name": "security_checklist",
        "display_name": "安全检查",
        "description": "安全检查清单、安全规范",
        "icon": "safety"
    },
    {
        "name": "best_practice",
        "display_name": "最佳实践",
        "description": "团队最佳实践、经验总结",
        "icon": "trophy"
    },
    {
        "name": "other",
        "display_name": "其它",
        "description": "其他类型的规范文档",
        "icon": "ellipsis"
    },
]


async def init_default_team(db: AsyncSession):
    """初始化默认团队"""
    print("\n🏢 初始化默认团队...")
    
    # 检查是否已存在
    result = await db.execute(
        select(Team).filter(Team.name == DEFAULT_TEAM["name"])
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        print(f"  ✓ 默认团队已存在: {DEFAULT_TEAM['name']}")
        return existing
    
    # 创建默认团队
    team = Team(
        id=str(uuid.uuid4()),
        name=DEFAULT_TEAM["name"],
        display_name=DEFAULT_TEAM["display_name"],
        description=DEFAULT_TEAM["description"],
        tech_stack='["Python", "Go", "TypeScript", "React"]',
        created_by=None  # 系统创建
    )
    
    db.add(team)
    await db.commit()
    await db.refresh(team)
    
    print(f"  ✓ 创建默认团队: {DEFAULT_TEAM['name']}")
    return team


async def init_demo_code_types(db: AsyncSession):
    """初始化Demo代码分类"""
    print("\n📦 初始化Demo代码分类...")
    
    created_count = 0
    skipped_count = 0
    
    for category in DEMO_CODE_CATEGORIES:
        # 检查是否已存在
        result = await db.execute(
            select(DevType).filter(
                DevType.category == DocumentType.DEMO_CODE,
                DevType.name == category["name"]
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            skipped_count += 1
            continue
        
        # 创建新分类
        dev_type = DevType(
            id=str(uuid.uuid4()),
            category=DocumentType.DEMO_CODE,
            name=category["name"],
            display_name=category["display_name"],
            description=category["description"],
            icon=category["icon"],
            sort_order=DEMO_CODE_CATEGORIES.index(category)
        )
        
        db.add(dev_type)
        created_count += 1
        print(f"  ✓ 创建分类: {category['display_name']}")
    
    await db.commit()
    print(f"  📊 Demo代码分类: 创建 {created_count} 个, 跳过 {skipped_count} 个")


async def init_business_doc_types(db: AsyncSession):
    """初始化业务文档分类"""
    print("\n📄 初始化业务文档分类...")
    
    created_count = 0
    skipped_count = 0
    
    for category in BUSINESS_DOC_CATEGORIES:
        # 检查是否已存在
        result = await db.execute(
            select(DevType).filter(
                DevType.category == DocumentType.BUSINESS_DOC,
                DevType.name == category["name"]
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            skipped_count += 1
            continue
        
        # 创建新分类
        dev_type = DevType(
            id=str(uuid.uuid4()),
            category=DocumentType.BUSINESS_DOC,
            name=category["name"],
            display_name=category["display_name"],
            description=category["description"],
            icon=category["icon"],
            sort_order=BUSINESS_DOC_CATEGORIES.index(category)
        )
        
        db.add(dev_type)
        created_count += 1
        print(f"  ✓ 创建分类: {category['display_name']}")
    
    await db.commit()
    print(f"  📊 业务文档分类: 创建 {created_count} 个, 跳过 {skipped_count} 个")


async def init_checklist_types(db: AsyncSession):
    """初始化规范文档分类（Checklist）"""
    print("\n✅ 初始化规范文档分类...")
    
    created_count = 0
    skipped_count = 0
    
    for category in CHECKLIST_CATEGORIES:
        # 检查是否已存在
        result = await db.execute(
            select(DevType).filter(
                DevType.category == DocumentType.CHECKLIST,
                DevType.name == category["name"]
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            skipped_count += 1
            continue
        
        # 创建新分类
        dev_type = DevType(
            id=str(uuid.uuid4()),
            category=DocumentType.CHECKLIST,
            name=category["name"],
            display_name=category["display_name"],
            description=category["description"],
            icon=category["icon"],
            sort_order=CHECKLIST_CATEGORIES.index(category)
        )
        
        db.add(dev_type)
        created_count += 1
        print(f"  ✓ 创建分类: {category['display_name']}")
    
    await db.commit()
    print(f"  📊 规范文档分类: 创建 {created_count} 个, 跳过 {skipped_count} 个")


async def init_all_data():
    """初始化所有预定义数据"""
    print("=" * 60)
    print("🚀 开始初始化预定义数据")
    print("=" * 60)
    
    # 先初始化数据库
    await init_db()
    
    async for db in get_db():
        try:
            # 初始化默认团队
            await init_default_team(db)
            
            # 初始化Demo代码分类
            await init_demo_code_types(db)
            
            # 初始化业务文档分类
            await init_business_doc_types(db)
            
            # 初始化规范文档分类（Checklist）
            await init_checklist_types(db)
            
            print("\n" + "=" * 60)
            print("✅ 预定义数据初始化完成！")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 初始化失败: {str(e)}")
            await db.rollback()
            raise
        finally:
            break  # 只执行一次


if __name__ == "__main__":
    asyncio.run(init_all_data())
