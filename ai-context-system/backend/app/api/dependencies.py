"""
认证和授权相关依赖
"""

from typing import Optional, Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.database import User, UserRole
from app.services.user_service import UserService

settings = get_settings()
security = HTTPBearer()


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """获取用户服务"""
    return UserService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """获取当前用户"""
    try:
        # 验证令牌
        payload = user_service.verify_token(credentials.credentials)
        if not payload:
            raise AuthenticationError("无效的访问令牌")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("令牌格式错误")
        
        # 获取用户信息
        user = await user_service.get_user_by_id(UUID(user_id))
        if not user:
            raise AuthenticationError("用户不存在")
        
        if not user.is_active:
            raise AuthenticationError("用户已被禁用")
        
        return user
    except (JWTError, ValueError):
        raise AuthenticationError("无效的访问令牌")
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    return current_user


class RoleChecker:
    """角色检查器"""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user


# 预定义的角色检查器
require_admin = RoleChecker([UserRole.ADMIN])
require_manager = RoleChecker([UserRole.ADMIN, UserRole.MANAGER])
require_developer = RoleChecker([UserRole.ADMIN, UserRole.MANAGER, UserRole.DEVELOPER])


class TeamChecker:
    """团队权限检查器"""
    
    def __init__(self, team_name: Optional[str] = None):
        self.team_name = team_name
    
    def __call__(
        self, 
        current_user: User = Depends(get_current_active_user),
        team_name: Optional[str] = None
    ) -> User:
        check_team = team_name or self.team_name
        if check_team and check_team not in current_user.teams:
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限访问该团队资源"
                )
        return current_user


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """获取用户代理字符串"""
    return request.headers.get("User-Agent", "unknown")


# 类型注解
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
ManagerUser = Annotated[User, Depends(require_manager)]
DeveloperUser = Annotated[User, Depends(require_developer)]
ClientIP = Annotated[str, Depends(get_client_ip)]
UserAgent = Annotated[str, Depends(get_user_agent)]