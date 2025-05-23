"""
职位管理API路由
Job management API routes for JobCatcher
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
import logging

from app.models.user import User
from app.api.auth import get_current_user
from app.services.job_search import JobSearchService

router = APIRouter()
logger = logging.getLogger(__name__)

# 初始化服务
job_search_service = JobSearchService()


class JobSearchRequest(BaseModel):
    """
    职位搜索请求模型
    Job search request model
    """
    q: str = Field(..., min_length=1, max_length=200, description="搜索关键词 / Search keywords")
    location: Optional[str] = Field(None, max_length=100, description="工作地点 / Work location")
    salary_min: Optional[int] = Field(None, ge=0, description="最低薪资 / Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="最高薪资 / Maximum salary")
    type: Optional[str] = Field(None, description="职位类型 / Job type")


class JobDTO(BaseModel):
    """
    职位数据传输对象
    Job data transfer object
    """
    id: str
    title: str
    company: str
    location: str
    salary: str
    source: str
    url: str
    description: str
    expired: bool = False


@router.get("/search", response_model=Dict[str, Any])
async def search_jobs(
    q: str = Query(..., description="搜索关键词 / Search keywords"),
    location: Optional[str] = Query(None, description="工作地点 / Work location"),
    salary_min: Optional[int] = Query(None, description="最低薪资 / Minimum salary"),
    salary_max: Optional[int] = Query(None, description="最高薪资 / Maximum salary"),
    type: Optional[str] = Query(None, description="职位类型 / Job type"),
    current_user: User = Depends(get_current_user)
):
    """
    搜索职位
    Search for jobs
    
    Args:
        q: 搜索关键词 / Search keywords
        location: 工作地点 / Work location  
        salary_min: 最低薪资 / Minimum salary
        salary_max: 最高薪资 / Maximum salary
        type: 职位类型 / Job type
        current_user: 当前用户 / Current user
        
    Returns:
        Dict: 职位搜索结果 / Job search results
    """
    try:
        logger.info(f"User {current_user.id} searching jobs with query: {q}")
        
        # 执行搜索 / Execute search
        search_results = await job_search_service.search_jobs(
            query=q,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            job_type=type
        )
        
        return {
            "data": search_results,
            "next_cursor": None  # 简化分页 / Simplified pagination
        }
        
    except Exception as e:
        logger.error(f"Error searching jobs for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="搜索职位时发生错误 / Error occurred while searching jobs"
        )


@router.get("/recommend", response_model=Dict[str, Any])
async def recommend_jobs(
    current_user: User = Depends(get_current_user)
):
    """
    根据简历推荐职位
    Recommend jobs based on resume
    
    Args:
        current_user: 当前用户 / Current user
        
    Returns:
        Dict: 推荐职位列表 / Recommended jobs list
    """
    try:
        logger.info(f"User {current_user.id} getting job recommendations")
        
        # 检查用户是否有简历数据 / Check if user has resume data
        if not hasattr(current_user, 'resume_data') or not current_user.resume_data:
            raise HTTPException(
                status_code=400,
                detail="请先上传简历 / Please upload resume first"
            )
        
        # 基于简历推荐职位 / Recommend jobs based on resume
        recommended_jobs = await job_search_service.recommend_jobs_for_user(
            user_id=current_user.id,
            resume_data=current_user.resume_data
        )
        
        return {
            "data": recommended_jobs,
            "count": len(recommended_jobs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job recommendations for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取职位推荐时发生错误 / Error occurred while getting job recommendations"
        ) 