"""
职位管理API路由
Job management API routes for JobCatcher
"""

from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/")
async def get_jobs(
    current_user: User = Depends(get_current_user)
):
    """
    获取职位列表
    Get job listings
    """
    return {
        "success": True,
        "message": "职位管理API - 开发中 / Job management API - under development"
    }


@router.get("/{job_id}")
async def get_job_detail(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取职位详情
    Get job details
    """
    return {
        "success": True,
        "job_id": job_id,
        "message": "职位详情API - 开发中 / Job details API - under development"
    } 