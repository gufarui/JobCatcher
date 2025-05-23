"""
用户认证API路由
User authentication API routes for JobCatcher
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_async_session
from app.core.config import settings
from app.models.user import User
from app.services.auth import AuthService

router = APIRouter()

# OAuth2密码流
# OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class UserCreate(BaseModel):
    """
    用户注册模型
    User registration model
    """
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    preferred_language: str = "zh"


class UserLogin(BaseModel):
    """
    用户登录模型
    User login model
    """
    email: EmailStr
    password: str


class Token(BaseModel):
    """
    访问令牌模型
    Access token model
    """
    access_token: str
    token_type: str
    expires_in: int
    user_info: dict


class UserResponse(BaseModel):
    """
    用户信息响应模型
    User information response model
    """
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    preferred_language: str
    created_at: datetime
    

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    """
    用户注册
    User registration
    """
    try:
        auth_service = AuthService(db)
        
        # 检查用户是否已存在
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户邮箱已存在 / Email already registered"
            )
        
        # 创建新用户
        # Create new user
        new_user = await auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            preferred_language=user_data.preferred_language
        )
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            preferred_language=new_user.preferred_language,
            created_at=new_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败 / Registration failed: {str(e)}"
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session)
):
    """
    用户登录获取访问令牌
    User login to get access token
    """
    try:
        auth_service = AuthService(db)
        
        # 验证用户凭据
        # Verify user credentials
        user = await auth_service.authenticate_user(
            email=form_data.username,  # OAuth2PasswordRequestForm uses username field
            password=form_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误 / Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用 / User account is inactive"
            )
        
        # 生成访问令牌
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        # 更新最后登录时间
        # Update last login time
        await auth_service.update_last_login(user.id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "preferred_language": user.preferred_language
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败 / Login failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login_with_email(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_session)
):
    """
    邮箱密码登录
    Email and password login
    """
    try:
        auth_service = AuthService(db)
        
        # 验证用户凭据
        # Verify user credentials
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误 / Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户账户已被禁用 / User account is inactive"
            )
        
        # 生成访问令牌
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        # 更新最后登录时间
        # Update last login time
        await auth_service.update_last_login(user.id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "preferred_language": user.preferred_language
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败 / Login failed: {str(e)}"
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    获取当前认证用户
    Get current authenticated user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据 / Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception:
        raise credentials_exception


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    Get current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        preferred_language=current_user.preferred_language,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    用户登出
    User logout
    """
    try:
        # 在生产环境中，这里可以将token加入黑名单
        # In production, this could add the token to a blacklist
        
        return {
            "message": "成功登出 / Successfully logged out",
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败 / Logout failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    刷新访问令牌
    Refresh access token
    """
    try:
        auth_service = AuthService(db)
        
        # 生成新的访问令牌
        # Generate new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": current_user.email},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info={
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "preferred_language": current_user.preferred_language
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败 / Token refresh failed: {str(e)}"
        ) 