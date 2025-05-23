"""
API包初始化文件
API package initialization for JobCatcher backend
"""

from fastapi import APIRouter

from app.api import auth, jobs, resumes, agents, users, chat

# 创建主API路由器
# Create main API router
api_router = APIRouter()

# 包含各个子模块的路由
# Include routes from sub-modules
api_router.include_router(auth.router, prefix="/auth", tags=["认证 / Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理 / User Management"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["职位管理 / Job Management"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["简历管理 / Resume Management"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agent系统 / Agent System"])
api_router.include_router(chat.router, prefix="/chat", tags=["聊天对话 / Chat"])

__all__ = ["api_router"] 