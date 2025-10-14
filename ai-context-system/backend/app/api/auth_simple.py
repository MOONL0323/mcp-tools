"""
简化认证API - 不使用JWT，用于快速测试
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from ..core.database import get_db
from ..models.database import User, UserRole
from ..schemas.auth import LoginRequest, RegisterRequest, UserInfo

router = APIRouter(prefix="/auth", tags=["认证-简化版"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


async def get_user_by_username(db: AsyncSession, username: str):
    """根据用户名获取用户"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


class SimpleLoginResponse(BaseModel):
    """简化登录响应"""
    success: bool
    message: str
    user: UserInfo


@router.post("/register", response_model=UserInfo)
async def register(
    register_request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = await get_user_by_username(db, register_request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == register_request.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被使用"
        )
    
    try:
        # 创建新用户
        hashed_password = get_password_hash(register_request.password)
        new_user = User(
            username=register_request.username,
            email=register_request.email,
            password_hash=hashed_password,
            full_name=register_request.full_name,
            role=UserRole.DEVELOPER,
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return UserInfo(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login_at=new_user.last_login_at
        )
    except Exception as e:
        await db.rollback()
        print(f"注册错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=SimpleLoginResponse)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录 - 简化版"""
    user = await get_user_by_username(db, login_request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not verify_password(login_request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户账户已被禁用"
        )
    
    try:
        # 更新最后登录时间
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
        
        return SimpleLoginResponse(
            success=True,
            message="登录成功",
            user=user_info
        )
    except Exception as e:
        await db.rollback()
        print(f"登录错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )