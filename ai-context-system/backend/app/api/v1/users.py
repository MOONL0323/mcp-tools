"""
用户相关API路由
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    DatabaseError, ValidationError, NotFoundError, 
    AuthenticationError, AuthorizationError
)
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserChangePassword,
    TokenResponse, TokenRefresh
)
from app.services.user_service import UserService
from app.api.dependencies import (
    get_current_active_user, CurrentUser, AdminUser, ManagerUser,
    get_client_ip, get_user_agent, ClientIP, UserAgent
)

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    try:
        user_service = UserService(db)
        user = await user_service.create_user(user_data)
        return UserResponse.from_orm(user)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    ip_address: ClientIP,
    user_agent: UserAgent,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    try:
        user_service = UserService(db)
        token = await user_service.login(login_data, ip_address, user_agent)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    current_user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """用户登出"""
    try:
        # 从请求头获取token
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的授权头"
            )
        
        token = authorization.replace("Bearer ", "")
        user_service = UserService(db)
        await user_service.logout(current_user.id, token)
        
        return {"message": "登出成功"}
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        user_service = UserService(db)
        token = await user_service.refresh_token(refresh_data.refresh_token)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """获取当前用户信息"""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        user_service = UserService(db)
        user = await user_service.update_user(current_user.id, user_data)
        return UserResponse.from_orm(user)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/change-password")
async def change_password(
    password_data: UserChangePassword,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    try:
        user_service = UserService(db)
        await user_service.change_password(current_user.id, password_data)
        return {"message": "密码修改成功"}
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    current_user: ManagerUser,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    team: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None
):
    """获取用户列表（需要管理员或经理权限）"""
    try:
        user_service = UserService(db)
        users = await user_service.get_users(skip, limit, team, role, search)
        return [UserResponse.from_orm(user) for user in users]
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    current_user: ManagerUser,
    db: AsyncSession = Depends(get_db)
):
    """获取指定用户信息（需要管理员或经理权限）"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return UserResponse.from_orm(user)
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息（需要管理员权限）"""
    try:
        user_service = UserService(db)
        user = await user_service.update_user(user_id, user_data)
        return UserResponse.from_orm(user)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db)
):
    """删除用户（需要管理员权限）"""
    try:
        user_service = UserService(db)
        await user_service.delete_user(user_id)
        return {"message": "用户删除成功"}
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/me/sessions")
async def get_current_user_sessions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户会话列表"""
    try:
        user_service = UserService(db)
        sessions = await user_service.get_user_sessions(current_user.id)
        return {
            "sessions": [
                {
                    "id": str(session.id),
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "created_at": session.created_at,
                    "last_accessed_at": session.last_accessed_at,
                    "expires_at": session.expires_at
                }
                for session in sessions
            ]
        }
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/me/sessions/{session_id}")
async def revoke_user_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """撤销指定会话"""
    try:
        user_service = UserService(db)
        await user_service.revoke_session(current_user.id, session_id)
        return {"message": "会话撤销成功"}
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/me/sessions")
async def revoke_all_user_sessions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """撤销所有会话"""
    try:
        user_service = UserService(db)
        await user_service.revoke_all_sessions(current_user.id)
        return {"message": "所有会话撤销成功"}
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )