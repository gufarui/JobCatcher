"""
简历管理API路由
Resume management API routes for JobCatcher
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import Response
from pydantic import BaseModel
import logging

from app.models.user import User
from app.api.auth import get_current_user
from app.services.resume_processor import ResumeProcessorService

router = APIRouter()
logger = logging.getLogger(__name__)

# 初始化服务
resume_processor = ResumeProcessorService()


class ResumeParseResponse(BaseModel):
    """
    简历解析响应模型
    Resume parse response model
    """
    success: bool
    resume_id: str
    parsed_data: Dict[str, Any]
    message: str


@router.post("/upload", response_model=ResumeParseResponse)
async def upload_resume(
    file: UploadFile = File(..., description="简历文件 / Resume file"),
    current_user: User = Depends(get_current_user)
):
    """
    上传并解析简历文件
    Upload and parse resume file
    
    Args:
        file: 简历文件 (PDF/Word) / Resume file (PDF/Word)
        current_user: 当前用户 / Current user
        
    Returns:
        ResumeParseResponse: 解析结果 / Parse result
    """
    try:
        logger.info(f"User {current_user.id} uploading resume: {file.filename}")
        
        # 检查文件类型 / Check file type
        if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="仅支持PDF和Word文件 / Only PDF and Word files are supported"
            )
        
        # 检查文件大小 (10MB) / Check file size (10MB)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="文件大小不能超过10MB / File size cannot exceed 10MB"
            )
        
        # 解析简历 / Parse resume
        result = await resume_processor.parse_and_store_resume(
            user_id=current_user.id,
            file_content=file_content,
            filename=file.filename
        )
        
        return ResumeParseResponse(
            success=True,
            resume_id=result["resume_id"],
            parsed_data=result["parsed_data"],
            message="简历解析成功 / Resume parsed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="简历上传失败 / Resume upload failed"
        )


@router.get("/{resume_id}", response_model=Dict[str, Any])
async def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取简历数据
    Get resume data
    
    Args:
        resume_id: 简历ID / Resume ID
        current_user: 当前用户 / Current user
        
    Returns:
        Dict: 简历数据 / Resume data
    """
    try:
        logger.info(f"User {current_user.id} fetching resume: {resume_id}")
        
        resume = await resume_processor.get_resume_by_id(resume_id, current_user.id)
        
        if not resume:
            raise HTTPException(
                status_code=404,
                detail="简历不存在 / Resume not found"
            )
        
        return {
            "resume_id": resume_id,
            "parsed_data": resume.parsed_data,
            "uploaded_at": resume.uploaded_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resume for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取简历失败 / Get resume failed"
        ) 