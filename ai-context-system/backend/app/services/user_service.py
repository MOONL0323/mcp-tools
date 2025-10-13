"""
用户服务 - 用户管理相关业务逻辑
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.exceptions import (
    DatabaseError, ValidationError, NotFoundError, 
    AuthenticationError, AuthorizationError
)
from app.models.database import User, UserSession, AuditLog
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    UserChangePassword, TokenResponse
)

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """用户服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # 密码相关方法
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict):
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    # 用户查询方法
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID获取用户"""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        try:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        try:
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"获取用户失败: {str(e)}")
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        team: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """获取用户列表"""
        try:
            query = select(User)
            
            # 添加过滤条件
            if team:
                query = query.where(User.teams.contains([team]))
            
            if role:
                query = query.where(User.role == role)
            
            if search:
                query = query.where(
                    or_(
                        User.username.ilike(f"%{search}%"),
                        User.full_name.ilike(f"%{search}%"),
                        User.email.ilike(f"%{search}%")
                    )
                )
            
            query = query.where(User.is_active == True)
            query = query.offset(skip).limit(limit)
            query = query.order_by(User.created_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"获取用户列表失败: {str(e)}")
    
    # 用户创建和更新方法
    async def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        try:
            # 检查用户名是否已存在
            existing_user = await self.get_user_by_username(user_data.username)
            if existing_user:
                raise ValidationError("用户名已存在")
            
            # 检查邮箱是否已存在
            existing_email = await self.get_user_by_email(user_data.email)
            if existing_email:
                raise ValidationError("邮箱已存在")
            
            # 创建用户
            hashed_password = self.get_password_hash(user_data.password)
            user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=hashed_password,
                full_name=user_data.full_name,
                avatar_url=user_data.avatar_url,
                role=user_data.role,
                teams=user_data.teams
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            return user
        except ValidationError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"创建用户失败: {str(e)}")
    
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """更新用户"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise NotFoundError("用户不存在")
            
            # 更新字段
            update_data = user_data.dict(exclude_unset=True)
            if update_data:
                await self.db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data)
                )
                await self.db.commit()
                await self.db.refresh(user)
            
            return user
        except NotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"更新用户失败: {str(e)}")
    
    async def delete_user(self, user_id: UUID) -> bool:
        """删除用户（软删除）"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise NotFoundError("用户不存在")
            
            # 软删除 - 设置为非活跃状态
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False)
            )
            await self.db.commit()
            
            return True
        except NotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"删除用户失败: {str(e)}")
    
    # 认证相关方法
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        try:
            user = await self.get_user_by_username(username)
            if not user:
                return None
            
            if not user.is_active:
                return None
            
            if not self.verify_password(password, user.password_hash):
                return None
            
            # 更新最后登录时间
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(last_login_at=datetime.utcnow())
            )
            await self.db.commit()
            
            return user
        except Exception as e:
            raise DatabaseError(f"用户认证失败: {str(e)}")
    
    async def login(self, login_data: UserLogin, ip_address: str, user_agent: str) -> TokenResponse:
        """用户登录"""
        try:
            user = await self.authenticate_user(login_data.username, login_data.password)
            if not user:
                raise AuthenticationError("用户名或密码错误")
            
            # 创建令牌
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.create_access_token(
                data={"sub": str(user.id), "username": user.username},
                expires_delta=access_token_expires
            )
            refresh_token = self.create_refresh_token(
                data={"sub": str(user.id), "username": user.username}
            )
            
            # 保存会话
            session = UserSession(
                user_id=user.id,
                session_token=access_token[:32],  # 存储部分令牌作为标识
                refresh_token=refresh_token[-32:],  # 存储部分刷新令牌作为标识
                expires_at=datetime.utcnow() + access_token_expires,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(session)
            await self.db.commit()
            
            # 记录审计日志
            await self._log_audit(user.id, "login", "users", user.id, {
                "ip_address": ip_address,
                "user_agent": user_agent
            })
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        except AuthenticationError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"登录失败: {str(e)}")
    
    async def logout(self, user_id: UUID, session_token: str) -> bool:
        """用户登出"""
        try:
            # 删除会话
            await self.db.execute(
                delete(UserSession).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.session_token == session_token[:32]
                    )
                )
            )
            await self.db.commit()
            
            # 记录审计日志
            await self._log_audit(user_id, "logout", "users", user_id)
            
            return True
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"登出失败: {str(e)}")
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """刷新令牌"""
        try:
            payload = self.verify_token(refresh_token)
            if not payload:
                raise AuthenticationError("无效的刷新令牌")
            
            user_id = UUID(payload.get("sub"))
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("用户不存在或已禁用")
            
            # 验证会话是否存在
            result = await self.db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.refresh_token == refresh_token[-32:]
                    )
                )
            )
            session = result.scalar_one_or_none()
            if not session:
                raise AuthenticationError("会话不存在")
            
            # 创建新令牌
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            new_access_token = self.create_access_token(
                data={"sub": str(user.id), "username": user.username},
                expires_delta=access_token_expires
            )
            new_refresh_token = self.create_refresh_token(
                data={"sub": str(user.id), "username": user.username}
            )
            
            # 更新会话
            await self.db.execute(
                update(UserSession)
                .where(UserSession.id == session.id)
                .values(
                    session_token=new_access_token[:32],
                    refresh_token=new_refresh_token[-32:],
                    expires_at=datetime.utcnow() + access_token_expires,
                    last_accessed_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        except AuthenticationError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"刷新令牌失败: {str(e)}")
    
    async def change_password(self, user_id: UUID, password_data: UserChangePassword) -> bool:
        """修改密码"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise NotFoundError("用户不存在")
            
            # 验证旧密码
            if not self.verify_password(password_data.old_password, user.password_hash):
                raise ValidationError("旧密码错误")
            
            # 更新密码
            new_password_hash = self.get_password_hash(password_data.new_password)
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(password_hash=new_password_hash)
            )
            await self.db.commit()
            
            # 记录审计日志
            await self._log_audit(user_id, "update", "users", user_id, {
                "action": "change_password"
            })
            
            return True
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"修改密码失败: {str(e)}")
    
    # 会话管理方法
    async def get_user_sessions(self, user_id: UUID) -> List[UserSession]:
        """获取用户会话列表"""
        try:
            result = await self.db.execute(
                select(UserSession)
                .where(UserSession.user_id == user_id)
                .order_by(UserSession.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"获取用户会话失败: {str(e)}")
    
    async def revoke_session(self, user_id: UUID, session_id: UUID) -> bool:
        """撤销用户会话"""
        try:
            await self.db.execute(
                delete(UserSession).where(
                    and_(
                        UserSession.id == session_id,
                        UserSession.user_id == user_id
                    )
                )
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"撤销会话失败: {str(e)}")
    
    async def revoke_all_sessions(self, user_id: UUID) -> bool:
        """撤销用户所有会话"""
        try:
            await self.db.execute(
                delete(UserSession).where(UserSession.user_id == user_id)
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise DatabaseError(f"撤销所有会话失败: {str(e)}")
    
    # 审计日志方法
    async def _log_audit(
        self, 
        user_id: UUID, 
        action: str, 
        resource_type: str, 
        resource_id: UUID, 
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """记录审计日志"""
        try:
            log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(log)
            await self.db.commit()
        except Exception:
            # 审计日志失败不应该影响主要操作
            pass
    
    async def get_audit_logs(
        self, 
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """获取审计日志"""
        try:
            query = select(AuditLog).options(selectinload(AuditLog.user))
            
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            
            if action:
                query = query.where(AuditLog.action == action)
            
            if resource_type:
                query = query.where(AuditLog.resource_type == resource_type)
            
            query = query.offset(skip).limit(limit)
            query = query.order_by(AuditLog.created_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise DatabaseError(f"获取审计日志失败: {str(e)}")