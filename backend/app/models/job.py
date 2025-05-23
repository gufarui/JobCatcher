"""
职位数据模型
Job data model for JobCatcher
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from app.core.database import Base


class JobSource(str, Enum):
    """
    职位来源枚举
    Job source enumeration
    """
    STEPSTONE = "stepstone"
    GOOGLE_JOBS = "google_jobs"
    JOBSPIKR = "jobspikr"
    CORESIGNAL = "coresignal"
    MANUAL = "manual"


class JobType(str, Enum):
    """
    职位类型枚举
    Job type enumeration
    """
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    REMOTE = "remote"


class Job(Base):
    """
    职位模型
    Job model for storing job postings and search data
    """
    __tablename__ = "jobs"
    
    # 主键和基本信息
    # Primary key and basic information
    id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)  # 外部来源的唯一ID
    external_id: Mapped[str] = mapped_column(String(200), nullable=True)  # 原始数据源中的ID
    
    # 职位基本信息
    # Job basic information
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True, index=True)
    
    # 职位详情
    # Job details
    description: Mapped[str] = mapped_column(Text, nullable=True)
    requirements: Mapped[str] = mapped_column(Text, nullable=True)
    benefits: Mapped[str] = mapped_column(Text, nullable=True)
    
    # 薪资信息
    # Salary information
    salary_min: Mapped[int] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="EUR")
    salary_period: Mapped[str] = mapped_column(String(20), nullable=True)  # yearly, monthly, hourly
    
    # 职位类型和来源
    # Job type and source
    job_type: Mapped[JobType] = mapped_column(String(20), nullable=True, index=True)
    source: Mapped[JobSource] = mapped_column(String(20), nullable=False, index=True)
    
    # 技能和关键词 (JSON格式存储)
    # Skills and keywords (stored as JSON)
    skills: Mapped[dict] = mapped_column(JSON, nullable=True)
    keywords: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # 公司信息
    # Company information
    company_logo: Mapped[str] = mapped_column(String(500), nullable=True)
    company_size: Mapped[str] = mapped_column(String(50), nullable=True)
    company_industry: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # 申请信息
    # Application information
    application_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    application_email: Mapped[str] = mapped_column(String(255), nullable=True)
    application_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 数据质量和状态
    # Data quality and status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)  # 数据质量评分
    
    # 统计信息
    # Statistics
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 时间戳
    # Timestamps
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 向量化数据 (用于AI搜索)
    # Vectorized data (for AI search)
    embedding_vector: Mapped[str] = mapped_column(Text, nullable=True)  # 序列化的向量数据
    embedding_model: Mapped[str] = mapped_column(String(50), nullable=True)  # 使用的嵌入模型
    
    def __repr__(self) -> str:
        return f"<Job(id='{self.id}', title='{self.title}', company='{self.company}')>"
    
    def to_dict(self) -> dict:
        """
        将职位对象转换为字典
        Convert job object to dictionary
        """
        return {
            "id": self.id,
            "external_id": self.external_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "requirements": self.requirements,
            "benefits": self.benefits,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "salary_period": self.salary_period,
            "job_type": self.job_type,
            "source": self.source,
            "skills": self.skills,
            "keywords": self.keywords,
            "company_logo": self.company_logo,
            "company_size": self.company_size,
            "company_industry": self.company_industry,
            "application_url": self.application_url,
            "application_email": self.application_email,
            "application_deadline": self.application_deadline.isoformat() if self.application_deadline else None,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "quality_score": self.quality_score,
            "view_count": self.view_count,
            "click_count": self.click_count,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
        }
    
    def get_salary_range(self) -> str:
        """
        获取格式化的薪资范围字符串
        Get formatted salary range string
        """
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,} - {self.salary_max:,} {self.salary_currency}"
        elif self.salary_min:
            return f"{self.salary_min:,}+ {self.salary_currency}"
        elif self.salary_max:
            return f"Up to {self.salary_max:,} {self.salary_currency}"
        else:
            return "薪资面议 / Salary negotiable"
    
    def is_remote_job(self) -> bool:
        """
        判断是否为远程工作
        Check if this is a remote job
        """
        remote_keywords = ["remote", "远程", "home", "anywhere", "virtual"]
        location_lower = (self.location or "").lower()
        return any(keyword in location_lower for keyword in remote_keywords) or self.job_type == JobType.REMOTE

# ================== Pydantic响应模型 / Pydantic Response Models ==================

class JobSearchFilters(BaseModel):
    """
    职位搜索过滤器模型
    Job search filters model
    """
    query: str = Field(..., description="搜索关键词 / Search keywords")
    location: Optional[str] = Field(None, description="工作地点 / Work location")
    salary_min: Optional[int] = Field(None, description="最低薪资 / Minimum salary")
    salary_max: Optional[int] = Field(None, description="最高薪资 / Maximum salary")
    job_type: Optional[str] = Field(None, description="职位类型 / Job type")
    experience_level: Optional[str] = Field(None, description="经验要求 / Experience level")
    remote_ok: Optional[bool] = Field(None, description="是否接受远程 / Remote work allowed")
    page: int = Field(1, description="页码 / Page number")
    page_size: int = Field(10, description="每页数量 / Items per page")
    sort_by: Optional[str] = Field("relevance", description="排序方式 / Sort by")


class JobDto(BaseModel):
    """
    职位DTO模型
    Job DTO model
    """
    id: str = Field(..., description="职位ID / Job ID")
    external_id: Optional[str] = Field(None, description="外部ID / External ID")
    title: str = Field(..., description="职位标题 / Job title")
    company: str = Field(..., description="公司名称 / Company name")
    location: Optional[str] = Field(None, description="工作地点 / Work location")
    description: Optional[str] = Field(None, description="职位描述 / Job description")
    requirements: Optional[str] = Field(None, description="职位要求 / Job requirements")
    benefits: Optional[str] = Field(None, description="福利待遇 / Benefits")
    salary_min: Optional[int] = Field(None, description="最低薪资 / Minimum salary")
    salary_max: Optional[int] = Field(None, description="最高薪资 / Maximum salary")
    salary_currency: str = Field("EUR", description="薪资货币 / Salary currency")
    salary_period: Optional[str] = Field(None, description="薪资周期 / Salary period")
    job_type: Optional[str] = Field(None, description="职位类型 / Job type")
    source: str = Field(..., description="数据来源 / Data source")
    skills: Optional[dict] = Field(None, description="技能要求 / Skills required")
    keywords: Optional[dict] = Field(None, description="关键词 / Keywords")
    company_logo: Optional[str] = Field(None, description="公司Logo / Company logo")
    company_size: Optional[str] = Field(None, description="公司规模 / Company size")
    company_industry: Optional[str] = Field(None, description="公司行业 / Company industry")
    application_url: Optional[str] = Field(None, description="申请链接 / Application URL")
    application_email: Optional[str] = Field(None, description="申请邮箱 / Application email")
    application_deadline: Optional[datetime] = Field(None, description="申请截止日期 / Application deadline")
    is_active: bool = Field(True, description="是否有效 / Is active")
    is_expired: bool = Field(False, description="是否过期 / Is expired")
    quality_score: Optional[float] = Field(None, description="质量评分 / Quality score")
    view_count: int = Field(0, description="浏览次数 / View count")
    click_count: int = Field(0, description="点击次数 / Click count")
    posted_at: Optional[datetime] = Field(None, description="发布时间 / Posted time")
    scraped_at: Optional[datetime] = Field(None, description="抓取时间 / Scraped time")
    updated_at: Optional[datetime] = Field(None, description="更新时间 / Updated time")
    
    # 匹配度相关字段（仅在有简历时计算）
    # Match score related fields (calculated only when resume exists)
    match_score: Optional[float] = Field(None, description="匹配度评分 / Match score")
    
    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    """
    单个职位响应模型
    Single job response model
    """
    job: JobDto = Field(..., description="职位信息 / Job information")
    match_analysis: Optional[dict] = Field(None, description="匹配度分析 / Match analysis")


class JobListResponse(BaseModel):
    """
    职位列表响应模型
    Job list response model
    """
    jobs: List[JobDto] = Field(..., description="职位列表 / Job list")
    total: int = Field(..., description="总数量 / Total count")
    page: int = Field(..., description="当前页码 / Current page")
    page_size: int = Field(..., description="每页数量 / Page size")
    has_more: bool = Field(..., description="是否有更多 / Has more")
    filters: Optional[JobSearchFilters] = Field(None, description="搜索过滤器 / Search filters") 