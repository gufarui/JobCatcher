"""
用户数据模型
User data model for JobCatcher
"""

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.chat_history import ChatHistory


class User(Base):
    """
    用户模型
    User model for storing user information and authentication
    """
    __tablename__ = "users"
    
    # 主键和基本信息
    # Primary key and basic information
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # OAuth相关字段
    # OAuth related fields
    google_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    
    # 用户偏好设置
    # User preference settings
    preferred_language: Mapped[str] = mapped_column(String(10), default="zh-CN")
    preferred_location: Mapped[str] = mapped_column(String(100), nullable=True)
    preferred_job_types: Mapped[str] = mapped_column(Text, nullable=True)  # JSON字符串 / JSON string
    
    # 账户状态
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 时间戳
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
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
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 关系映射
    # Relationships
    resumes: Mapped[List["Resume"]] = relationship(
        "Resume", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    chat_histories: Mapped[List["ChatHistory"]] = relationship(
        "ChatHistory", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """
        将用户对象转换为字典
        Convert user object to dictionary
        """
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "google_id": self.google_id,
            "preferred_language": self.preferred_language,
            "preferred_location": self.preferred_location,
            "preferred_job_types": self.preferred_job_types,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        } 