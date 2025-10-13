"""
初始化默认用户
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from app.core.database import init_db, async_session
from app.models.database import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_default_user():
    """创建默认管理员用户"""
    # 初始化数据库连接
    await init_db()
    
    # 获取会话
    from app.core.database import get_db
    async for session in get_db():
        # 检查是否已有管理员用户
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("管理员用户已存在")
            return
        
        # 创建默认管理员用户
        admin_user = User(
            username="admin",
            email="admin@aicontext.com",
            password_hash=pwd_context.hash("admin123"),
            full_name="系统管理员",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        session.add(admin_user)
        await session.commit()
        
        print("已创建默认管理员用户:")
        print(f"用户名: admin")
        print(f"密码: admin123")


if __name__ == "__main__":
    asyncio.run(create_default_user())