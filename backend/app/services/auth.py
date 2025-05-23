"""
认证服务
Authentication service for JobCatcher user management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User


class AuthService:
    """
    认证服务类
    Authentication service class
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化认证服务
        Initialize authentication service
        """
        self.db = db
        self.logger = logging.getLogger("service.auth")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        Get user by email
        """
        try:
            query = select(User).where(User.email == email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"获取用户失败 / Failed to get user: {e}")
            return None
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        preferred_language: str = "zh"
    ) -> User:
        """
        创建新用户
        Create new user
        """
        try:
            # 密码哈希
            # Password hashing
            password_hash = self._hash_password(password)
            
            # 创建用户对象
            # Create user object
            new_user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                preferred_language=preferred_language,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            
            self.logger.info(f"新用户创建成功 / New user created: {email}")
            return new_user
            
        except Exception as e:
            self.logger.error(f"创建用户失败 / Failed to create user: {e}")
            await self.db.rollback()
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        Authenticate user credentials
        """
        try:
            user = await self.get_user_by_email(email)
            if not user:
                return None
            
            if not self._verify_password(password, user.password_hash):
                return None
            
            return user
            
        except Exception as e:
            self.logger.error(f"用户认证失败 / User authentication failed: {e}")
            return None
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        Create access token
        """
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
            to_encode.update({"exp": expire})
            
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            
            return encoded_jwt
            
        except Exception as e:
            self.logger.error(f"创建访问令牌失败 / Failed to create access token: {e}")
            raise
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """
        根据令牌获取当前用户
        Get current user from token
        """
        try:
            # 解码JWT令牌
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            email: str = payload.get("sub")
            if email is None:
                return None
            
            # 获取用户
            # Get user
            user = await self.get_user_by_email(email)
            return user
            
        except jwt.PyJWTError as e:
            self.logger.error(f"JWT令牌解码失败 / JWT token decode failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取当前用户失败 / Failed to get current user: {e}")
            return None
    
    async def update_last_login(self, user_id: int) -> None:
        """
        更新用户最后登录时间
        Update user last login time
        """
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                user.last_login = datetime.utcnow()
                await self.db.commit()
                self.logger.info(f"用户最后登录时间已更新 / User last login updated: {user_id}")
            
        except Exception as e:
            self.logger.error(f"更新最后登录时间失败 / Failed to update last login: {e}")
            await self.db.rollback()
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        修改用户密码
        Change user password
        """
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # 验证旧密码
            # Verify old password
            if not self._verify_password(old_password, user.password_hash):
                return False
            
            # 更新新密码
            # Update new password
            user.password_hash = self._hash_password(new_password)
            await self.db.commit()
            
            self.logger.info(f"用户密码修改成功 / User password changed: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"修改密码失败 / Failed to change password: {e}")
            await self.db.rollback()
            return False
    
    async def deactivate_user(self, user_id: int) -> bool:
        """
        停用用户账户
        Deactivate user account
        """
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            user.is_active = False
            await self.db.commit()
            
            self.logger.info(f"用户账户已停用 / User account deactivated: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"停用用户账户失败 / Failed to deactivate user: {e}")
            await self.db.rollback()
            return False
    
    def _hash_password(self, password: str) -> str:
        """
        哈希密码
        Hash password
        """
        try:
            # 生成盐值并哈希密码
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            self.logger.error(f"密码哈希失败 / Password hashing failed: {e}")
            raise
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        Verify password
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            self.logger.error(f"密码验证失败 / Password verification failed: {e}")
            return False 