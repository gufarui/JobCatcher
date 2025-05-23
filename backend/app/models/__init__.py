"""
数据模型包初始化文件
Models package initialization for JobCatcher
"""

from app.models.user import User
from app.models.job import Job, JobSource, JobType
from app.models.resume import Resume
from app.models.chat_history import ChatHistory, MessageRole, MessageType

# 导出所有模型类和枚举
# Export all model classes and enums
__all__ = [
    # 模型类 / Model classes
    "User",
    "Job", 
    "Resume",
    "ChatHistory",
    
    # 枚举类 / Enum classes
    "JobSource",
    "JobType", 
    "MessageRole",
    "MessageType",
] 