"""
用户管理API路由
User management API routes for JobCatcher
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_async_session
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter()


class UserProfileUpdate(BaseModel):
    """
    用户资料更新模型
    User profile update model
    """
    full_name: str = None
    preferred_language: str = None
    preferences: dict = None


@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    获取用户资料
    Get user profile
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "preferred_language": current_user.preferred_language,
        "preferences": current_user.preferences,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


@router.put("/profile")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    更新用户资料
    Update user profile
    """
    try:
        # 更新用户信息
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name
        if profile_data.preferred_language is not None:
            current_user.preferred_language = profile_data.preferred_language
        if profile_data.preferences is not None:
            current_user.preferences = profile_data.preferences
        
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "success": True,
            "message": "用户资料更新成功 / User profile updated successfully",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "preferred_language": current_user.preferred_language,
                "preferences": current_user.preferences
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户资料失败 / Failed to update user profile: {str(e)}"
        ) 