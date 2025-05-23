"""
简历处理服务 - 简化版本，利用Claude 4原生文档理解能力
Resume processor service - Simplified version leveraging Claude 4 native document understanding
"""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_database_session
from app.models.resume import Resume, ResumeDto, ResumeListResponse
from app.models.user import User
from app.services.file_processor import FileProcessorService

logger = logging.getLogger(__name__)


class ResumeProcessorService:
    """
    简化的简历处理服务类 - 充分利用Claude 4的文档理解能力
    Simplified resume processor service leveraging Claude 4's document understanding
    """
    
    def __init__(self):
        self.file_processor_service = FileProcessorService()
    
    async def parse_and_store_resume(
        self,
        user_id: int,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        解析并存储简历 - 让Claude 4直接理解文档内容
        Parse and store resume - let Claude 4 directly understand document content
        """
        try:
            logger.info(f"Processing resume for user {user_id}: {filename}")
            
            # 使用文件处理服务提取文本
            # Use file processor to extract text
            extracted_text = await self.file_processor_service.extract_text(
                file_content, filename
            )
            
            # 生成简历ID
            # Generate resume ID
            resume_id = str(uuid4())
            
            async with get_database_session() as session:
                # 创建简历记录 - 存储原始文本，让Claude 4后续分析
                # Create resume record - store raw text for Claude 4 to analyze later
                new_resume = Resume(
                    id=resume_id,
                    user_id=user_id,
                    filename=filename,
                    file_size=len(file_content),
                    file_type=filename.split('.')[-1].lower(),
                    extracted_text=extracted_text,  # Claude 4可以直接理解这个文本
                    parsed_data={
                        "raw_text": extracted_text,
                        "extraction_method": "file_processor",
                        "processed_at": datetime.now().isoformat()
                    },
                    is_parsed=True
                )
                
                session.add(new_resume)
                await session.commit()
                await session.refresh(new_resume)
                
                return {
                    "resume_id": resume_id,
                    "parsed_data": new_resume.parsed_data,
                    "message": "简历已成功解析，Claude 4将在聊天中提供智能分析"
                }
                
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            raise
    
    async def get_resume_by_id(self, resume_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取简历数据 - 返回原始数据供Claude 4分析
        Get resume data - return raw data for Claude 4 analysis
        """
        try:
            async with get_database_session() as session:
                query = select(Resume).where(
                    and_(Resume.id == resume_id, Resume.user_id == user_id)
                )
                result = await session.execute(query)
                resume = result.scalar_one_or_none()
                
                if resume:
                    return {
                        "resume_id": resume_id,
                        "filename": resume.filename,
                        "extracted_text": resume.extracted_text,
                        "parsed_data": resume.parsed_data,
                        "uploaded_at": resume.uploaded_at.isoformat()
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting resume by ID {resume_id}: {str(e)}")
            raise
    
    async def get_user_latest_resume(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户最新简历 - 供Claude 4在聊天中使用
        Get user's latest resume - for Claude 4 to use in chat
        """
        try:
            async with get_database_session() as session:
                query = select(Resume).where(
                    Resume.user_id == user_id
                ).order_by(Resume.updated_at.desc()).limit(1)
                
                result = await session.execute(query)
                resume = result.scalar_one_or_none()
                
                if resume:
                    return {
                        "resume_id": resume.id,
                        "filename": resume.filename,
                        "extracted_text": resume.extracted_text,
                        "parsed_data": resume.parsed_data,
                        "uploaded_at": resume.uploaded_at.isoformat()
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting latest resume for user {user_id}: {str(e)}")
            raise 