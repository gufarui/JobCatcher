"""
聊天记录数据模型
Chat history data model for JobCatcher
"""

from datetime import datetime
from typing import TYPE_CHECKING
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class MessageRole(str, Enum):
    """
    消息角色枚举
    Message role enumeration
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageType(str, Enum):
    """
    消息类型枚举
    Message type enumeration
    """
    TEXT = "text"
    FILE_UPLOAD = "file_upload"
    JOB_RECOMMENDATION = "job_recommendation"
    RESUME_ANALYSIS = "resume_analysis"
    SKILL_HEATMAP = "skill_heatmap"
    PDF_GENERATION = "pdf_generation"
    SYSTEM_NOTIFICATION = "system_notification"


class ChatHistory(Base):
    """
    聊天记录模型
    Chat history model for storing conversation between users and AI
    """
    __tablename__ = "chat_histories"
    
    # 主键和关联
    # Primary key and relationships
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)  # 会话ID，用于分组
    
    # 消息基本信息
    # Message basic information
    role: Mapped[MessageRole] = mapped_column(String(20), nullable=False, index=True)
    message_type: Mapped[MessageType] = mapped_column(String(30), default=MessageType.TEXT, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 消息元数据
    # Message metadata
    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # 额外的元数据信息
    attachments: Mapped[dict] = mapped_column(JSON, nullable=True)  # 附件信息
    
    # Tool调用相关 (LangChain工具调用)
    # Tool calling related (LangChain tool calls)
    tool_call_id: Mapped[str] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(50), nullable=True)
    tool_input: Mapped[dict] = mapped_column(JSON, nullable=True)
    tool_output: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Agent相关信息
    # Agent related information
    agent_name: Mapped[str] = mapped_column(String(50), nullable=True)  # 哪个Agent处理的
    agent_step: Mapped[str] = mapped_column(String(50), nullable=True)  # Agent执行的步骤
    
    # 上下文和引用
    # Context and references
    parent_message_id: Mapped[UUID] = mapped_column(ForeignKey("chat_histories.id"), nullable=True)
    context_window: Mapped[dict] = mapped_column(JSON, nullable=True)  # 上下文窗口
    referenced_jobs: Mapped[dict] = mapped_column(JSON, nullable=True)  # 引用的职位
    referenced_resume_id: Mapped[str] = mapped_column(String(100), nullable=True)  # 引用的简历ID
    
    # 消息状态
    # Message status
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 质量评估
    # Quality assessment
    user_feedback: Mapped[str] = mapped_column(String(20), nullable=True)  # thumbs_up, thumbs_down
    feedback_comment: Mapped[str] = mapped_column(Text, nullable=True)
    
    # LLM相关信息
    # LLM related information
    model_name: Mapped[str] = mapped_column(String(50), nullable=True)  # claude-4, gpt-4, etc.
    token_count: Mapped[int] = mapped_column(nullable=True)  # token使用量
    response_time_ms: Mapped[int] = mapped_column(nullable=True)  # 响应时间(毫秒)
    
    # 时间戳
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # 关系映射
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_histories")
    parent_message: Mapped["ChatHistory"] = relationship(
        "ChatHistory", 
        remote_side=[id],
        backref="child_messages"
    )
    
    def __repr__(self) -> str:
        return f"<ChatHistory(id='{self.id}', user_id={self.user_id}, role='{self.role}')>"
    
    def to_dict(self) -> dict:
        """
        将聊天记录对象转换为字典
        Convert chat history object to dictionary
        """
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "role": self.role,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "attachments": self.attachments,
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "agent_name": self.agent_name,
            "agent_step": self.agent_step,
            "parent_message_id": str(self.parent_message_id) if self.parent_message_id else None,
            "context_window": self.context_window,
            "referenced_jobs": self.referenced_jobs,
            "referenced_resume_id": self.referenced_resume_id,
            "is_edited": self.is_edited,
            "is_deleted": self.is_deleted,
            "is_pinned": self.is_pinned,
            "user_feedback": self.user_feedback,
            "feedback_comment": self.feedback_comment,
            "model_name": self.model_name,
            "token_count": self.token_count,
            "response_time_ms": self.response_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_langchain_message(self) -> dict:
        """
        转换为LangChain消息格式
        Convert to LangChain message format
        """
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata or {}
        }
    
    def has_tool_call(self) -> bool:
        """
        检查是否包含工具调用
        Check if message contains tool call
        """
        return self.tool_call_id is not None and self.tool_name is not None
    
    def get_display_content(self) -> str:
        """
        获取用于前端显示的内容
        Get content for frontend display
        """
        if self.is_deleted:
            return "[消息已删除 / Message deleted]"
        
        if self.message_type == MessageType.FILE_UPLOAD:
            return f"📎 上传了文件: {self.attachments.get('filename', '未知文件')}"
        elif self.message_type == MessageType.JOB_RECOMMENDATION:
            return f"🎯 推荐了 {len(self.referenced_jobs or [])} 个职位"
        elif self.message_type == MessageType.RESUME_ANALYSIS:
            return "📄 完成了简历分析"
        elif self.message_type == MessageType.SKILL_HEATMAP:
            return "📊 生成了技能热点图"
        elif self.message_type == MessageType.PDF_GENERATION:
            return "📋 生成了PDF简历"
        else:
            # 如果内容过长，截取前200个字符
            if len(self.content) > 200:
                return self.content[:200] + "..."
            return self.content 