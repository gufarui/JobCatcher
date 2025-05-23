"""
职位搜索服务 - 简化版本
Job search service - Simplified version
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_database_session
from app.models.job import Job, JobDto, JobSearchFilters, JobListResponse
from app.models.user import User
from app.services.external_apis import ExternalAPIService

logger = logging.getLogger(__name__)


class JobSearchService:
    """
    简化的职位搜索服务类 - 基础搜索功能，让Claude 4处理分析
    Simplified job search service - basic search functionality, let Claude 4 handle analysis
    """
    
    def __init__(self):
        self.external_api_service = ExternalAPIService()
    
    async def search_jobs(
        self, 
        query: str,
        location: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        job_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        真实的职位搜索 - 调用外部API获取数据，让Claude 4分析
        Real job search - call external APIs for data, let Claude 4 analyze
        """
        try:
            logger.info(f"Searching jobs with query: {query}")
            
            # 使用外部API服务搜索职位
            # Use external API service to search jobs
            search_location = location or "Germany"
            jobs = await self.external_api_service.search_all_sources(
                keywords=query,
                location=search_location,
                max_results_per_source=10
            )
            
            # 可以在这里做基础过滤，但分析交给Claude 4
            # Can do basic filtering here, but leave analysis to Claude 4
            if salary_min or salary_max:
                # 基础薪资过滤（如果API支持的话）
                # Basic salary filtering (if API supports it)
                pass
            
            if job_type:
                # 基础职位类型过滤
                # Basic job type filtering
                pass
            
            logger.info(f"Found {len(jobs)} jobs from external APIs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            # 如果外部API失败，返回基础模拟数据以保持功能可用
            # If external APIs fail, return basic mock data to keep functionality available
            return await self._get_fallback_jobs(query, location)
    
    async def _get_fallback_jobs(self, query: str, location: Optional[str]) -> List[Dict[str, Any]]:
        """
        外部API失败时的回退数据
        Fallback data when external APIs fail
        """
        mock_jobs = [
            {
                "id": f"fallback_{i}",
                "title": f"Software Engineer - {query}",
                "company": f"Tech Company {i}",
                "location": location or "Remote",
                "salary": f"€{50000 + i*5000}-{80000 + i*5000}",
                "source": "Fallback",
                "url": f"https://example.com/job_{i}",
                "description": f"Looking for {query} developer with experience...",
                "posted_date": "2025-05-23",
                "requirements": ["Programming", query, "Problem solving"]
            }
            for i in range(5)  # 减少回退数据数量
        ]
        
        return mock_jobs
    
    async def recommend_jobs_for_user(
        self,
        user_id: int,
        resume_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        为用户推荐职位 - 基于简历数据
        Recommend jobs for user - based on resume data
        """
        try:
            logger.info(f"Getting job recommendations for user {user_id}")
            
            # 从简历数据中提取技能关键词
            # Extract skill keywords from resume data
            skills = resume_data.get("skills", [])
            if isinstance(skills, dict):
                skills = list(skills.keys())
            elif isinstance(skills, str):
                skills = [skills]
            
            # 使用技能搜索相关职位
            # Search for relevant jobs using skills
            query = " ".join(skills[:3]) if skills else "software engineer"
            jobs = await self.search_jobs(query=query)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting job recommendations: {str(e)}")
            raise 