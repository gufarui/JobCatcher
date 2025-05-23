"""
简历管理API路由
Resume management API routes for JobCatcher
"""

from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/")
async def get_resumes(
    current_user: User = Depends(get_current_user)
):
    """
    获取用户简历列表
    Get user resume list
    """
    return {
        "success": True,
        "message": "简历管理API - 开发中 / Resume management API - under development"
    }


@router.get("/{resume_id}")
async def get_resume_detail(
    resume_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取简历详情
    Get resume details
    """
    return {
        "success": True,
        "resume_id": resume_id,
        "message": "简历详情API - 开发中 / Resume details API - under development"
    } 