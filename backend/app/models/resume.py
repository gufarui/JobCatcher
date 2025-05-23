"""
简历数据模型
Resume data model for JobCatcher
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Resume(Base):
    """
    简历模型
    Resume model for storing user resumes and analysis results
    """
    __tablename__ = "resumes"
    
    # 主键和关联
    # Primary key and relationships
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # 文件信息
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)  # 文件大小 (bytes)
    file_type: Mapped[str] = mapped_column(String(20), nullable=True)  # PDF, DOCX, etc.
    blob_url: Mapped[str] = mapped_column(String(1000), nullable=True)  # Azure Blob存储URL
    
    # 解析后的简历结构化数据 (来自APILayer)
    # Parsed resume structured data (from APILayer)
    parsed_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # 个人基本信息 (从parsed_data提取)
    # Personal basic information (extracted from parsed_data)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    
    # 职业信息
    # Professional information
    current_position: Mapped[str] = mapped_column(String(200), nullable=True)
    years_of_experience: Mapped[int] = mapped_column(Integer, nullable=True)
    desired_position: Mapped[str] = mapped_column(String(200), nullable=True)
    desired_salary_min: Mapped[int] = mapped_column(Integer, nullable=True)
    desired_salary_max: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # 技能和经验 (JSON格式)
    # Skills and experience (JSON format)
    skills: Mapped[dict] = mapped_column(JSON, nullable=True)  # 技能列表和等级
    languages: Mapped[dict] = mapped_column(JSON, nullable=True)  # 语言能力
    education: Mapped[dict] = mapped_column(JSON, nullable=True)  # 教育背景
    work_experience: Mapped[dict] = mapped_column(JSON, nullable=True)  # 工作经历
    projects: Mapped[dict] = mapped_column(JSON, nullable=True)  # 项目经验
    certifications: Mapped[dict] = mapped_column(JSON, nullable=True)  # 认证资格
    
    # AI分析结果
    # AI analysis results
    analysis_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Claude 4分析结果
    skill_keywords: Mapped[dict] = mapped_column(JSON, nullable=True)  # 提取的技能关键词
    strength_summary: Mapped[str] = mapped_column(Text, nullable=True)  # 优势总结
    improvement_suggestions: Mapped[str] = mapped_column(Text, nullable=True)  # 改进建议
    
    # 匹配评分 (与职位的匹配度)
    # Matching scores (compatibility with jobs)
    overall_score: Mapped[float] = mapped_column(Float, nullable=True)  # 整体评分 (0-100)
    technical_score: Mapped[float] = mapped_column(Float, nullable=True)  # 技术技能评分
    experience_score: Mapped[float] = mapped_column(Float, nullable=True)  # 经验匹配评分
    education_score: Mapped[float] = mapped_column(Float, nullable=True)  # 教育背景评分
    
    # 版本和状态
    # Version and status
    version: Mapped[int] = mapped_column(Integer, default=1)  # 简历版本号
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否为主要简历
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否公开可见
    
    # 处理状态
    # Processing status
    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否已解析
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否已AI分析
    parsing_error: Mapped[str] = mapped_column(Text, nullable=True)  # 解析错误信息
    
    # 时间戳
    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    parsed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # 关系映射
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    
    def __repr__(self) -> str:
        return f"<Resume(id='{self.id}', user_id={self.user_id}, filename='{self.filename}')>"
    
    def to_dict(self) -> dict:
        """
        将简历对象转换为字典
        Convert resume object to dictionary
        """
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "blob_url": self.blob_url,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "current_position": self.current_position,
            "years_of_experience": self.years_of_experience,
            "desired_position": self.desired_position,
            "desired_salary_min": self.desired_salary_min,
            "desired_salary_max": self.desired_salary_max,
            "skills": self.skills,
            "languages": self.languages,
            "education": self.education,
            "work_experience": self.work_experience,
            "projects": self.projects,
            "certifications": self.certifications,
            "strength_summary": self.strength_summary,
            "improvement_suggestions": self.improvement_suggestions,
            "overall_score": self.overall_score,
            "technical_score": self.technical_score,
            "experience_score": self.experience_score,
            "education_score": self.education_score,
            "version": self.version,
            "is_primary": self.is_primary,
            "is_public": self.is_public,
            "is_parsed": self.is_parsed,
            "is_analyzed": self.is_analyzed,
            "parsing_error": self.parsing_error,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "parsed_at": self.parsed_at.isoformat() if self.parsed_at else None,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_skill_list(self) -> list:
        """
        获取技能列表
        Get list of skills
        """
        if not self.skills:
            return []
        
        if isinstance(self.skills, dict):
            # 如果skills是字典格式 {"Python": "Expert", "JavaScript": "Intermediate"}
            return list(self.skills.keys())
        elif isinstance(self.skills, list):
            # 如果skills是列表格式 ["Python", "JavaScript", "React"]
            return self.skills
        else:
            return []
    
    def get_experience_years(self) -> int:
        """
        计算工作经验年数
        Calculate years of work experience
        """
        if self.years_of_experience:
            return self.years_of_experience
        
        # 如果没有直接的经验年数，从工作经历中计算
        if not self.work_experience or not isinstance(self.work_experience, list):
            return 0
        
        total_months = 0
        for experience in self.work_experience:
            if isinstance(experience, dict) and "duration_months" in experience:
                total_months += experience.get("duration_months", 0)
        
        return max(0, total_months // 12)
    
    def get_match_score_summary(self) -> dict:
        """
        获取匹配评分摘要
        Get match score summary
        """
        return {
            "overall": self.overall_score or 0,
            "technical": self.technical_score or 0,
            "experience": self.experience_score or 0,
            "education": self.education_score or 0
        }


# ================== Pydantic响应模型 / Pydantic Response Models ==================

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID


class ResumeDto(BaseModel):
    """
    简历DTO模型
    Resume DTO model
    """
    id: str = Field(..., description="简历ID / Resume ID")
    user_id: int = Field(..., description="用户ID / User ID")
    title: str = Field(..., description="简历标题 / Resume title")
    filename: str = Field(..., description="文件名 / Filename")
    file_size: Optional[int] = Field(None, description="文件大小 / File size")
    file_type: Optional[str] = Field(None, description="文件类型 / File type")
    blob_url: Optional[str] = Field(None, description="文件URL / File URL")
    
    # 个人信息 / Personal information
    full_name: Optional[str] = Field(None, description="姓名 / Full name")
    email: Optional[str] = Field(None, description="邮箱 / Email")
    phone: Optional[str] = Field(None, description="电话 / Phone")
    location: Optional[str] = Field(None, description="地址 / Location")
    
    # 职业信息 / Professional information
    current_position: Optional[str] = Field(None, description="当前职位 / Current position")
    years_of_experience: Optional[int] = Field(None, description="工作年限 / Years of experience")
    desired_position: Optional[str] = Field(None, description="期望职位 / Desired position")
    desired_salary_min: Optional[int] = Field(None, description="期望最低薪资 / Desired minimum salary")
    desired_salary_max: Optional[int] = Field(None, description="期望最高薪资 / Desired maximum salary")
    
    # 结构化数据 / Structured data
    skills: Optional[Dict[str, Any]] = Field(None, description="技能 / Skills")
    languages: Optional[Dict[str, Any]] = Field(None, description="语言 / Languages")
    education: Optional[Dict[str, Any]] = Field(None, description="教育背景 / Education")
    work_experience: Optional[Dict[str, Any]] = Field(None, description="工作经历 / Work experience")
    projects: Optional[Dict[str, Any]] = Field(None, description="项目经验 / Projects")
    certifications: Optional[Dict[str, Any]] = Field(None, description="认证 / Certifications")
    
    # AI分析结果 / AI analysis results
    strength_summary: Optional[str] = Field(None, description="优势总结 / Strength summary")
    improvement_suggestions: Optional[str] = Field(None, description="改进建议 / Improvement suggestions")
    
    # 评分 / Scores
    overall_score: Optional[float] = Field(None, description="总体评分 / Overall score")
    technical_score: Optional[float] = Field(None, description="技术评分 / Technical score")
    experience_score: Optional[float] = Field(None, description="经验评分 / Experience score")
    education_score: Optional[float] = Field(None, description="教育评分 / Education score")
    
    # 状态 / Status
    version: int = Field(1, description="版本号 / Version")
    is_primary: bool = Field(True, description="是否主要简历 / Is primary")
    is_public: bool = Field(False, description="是否公开 / Is public")
    is_parsed: bool = Field(False, description="是否已解析 / Is parsed")
    is_analyzed: bool = Field(False, description="是否已分析 / Is analyzed")
    parsing_error: Optional[str] = Field(None, description="解析错误 / Parsing error")
    
    # 时间戳 / Timestamps
    uploaded_at: Optional[datetime] = Field(None, description="上传时间 / Uploaded time")
    parsed_at: Optional[datetime] = Field(None, description="解析时间 / Parsed time")
    analyzed_at: Optional[datetime] = Field(None, description="分析时间 / Analyzed time")
    updated_at: Optional[datetime] = Field(None, description="更新时间 / Updated time")
    
    class Config:
        from_attributes = True


class ResumeAnalysis(BaseModel):
    """
    简历分析结果模型
    Resume analysis result model
    """
    resume_id: str = Field(..., description="简历ID / Resume ID")
    analysis_type: str = Field(..., description="分析类型 / Analysis type")
    
    # 评分详情 / Score details
    overall_score: float = Field(..., ge=0, le=100, description="总体评分 / Overall score")
    technical_score: float = Field(..., ge=0, le=100, description="技术评分 / Technical score")
    experience_score: float = Field(..., ge=0, le=100, description="经验评分 / Experience score")
    education_score: float = Field(..., ge=0, le=100, description="教育评分 / Education score")
    
    # 分析结果 / Analysis results
    strengths: List[str] = Field(default=[], description="优势列表 / Strengths")
    weaknesses: List[str] = Field(default=[], description="不足列表 / Weaknesses")
    recommendations: List[str] = Field(default=[], description="建议列表 / Recommendations")
    
    # 技能分析 / Skills analysis
    technical_skills: List[str] = Field(default=[], description="技术技能 / Technical skills")
    soft_skills: List[str] = Field(default=[], description="软技能 / Soft skills")
    missing_skills: List[str] = Field(default=[], description="缺失技能 / Missing skills")
    
    # 匹配分析（针对特定职位时）/ Match analysis (for specific position)
    target_position: Optional[str] = Field(None, description="目标职位 / Target position")
    match_percentage: Optional[float] = Field(None, ge=0, le=100, description="匹配度 / Match percentage")
    
    # 分析时间 / Analysis timestamp
    analyzed_at: datetime = Field(..., description="分析时间 / Analyzed time")


class ResumeResponse(BaseModel):
    """
    单个简历响应模型
    Single resume response model
    """
    resume: ResumeDto = Field(..., description="简历信息 / Resume information")
    analysis: Optional[ResumeAnalysis] = Field(None, description="分析结果 / Analysis result")


class ResumeListResponse(BaseModel):
    """
    简历列表响应模型
    Resume list response model
    """
    resumes: List[ResumeDto] = Field(..., description="简历列表 / Resume list")
    total: int = Field(..., description="总数量 / Total count")
    page: int = Field(..., description="当前页码 / Current page")
    page_size: int = Field(..., description="每页数量 / Page size")
    has_more: bool = Field(..., description="是否有更多 / Has more") 