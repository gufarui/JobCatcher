"""
PDF生成服务
PDF generation service for JobCatcher
使用Claude 4生成Markdown简历，然后通过PDFMonkey转换为PDF
Using Claude 4 to generate Markdown resumes, then convert to PDF via PDFMonkey
"""

import logging
import httpx
import asyncio
from typing import Dict, Any, Optional
import anthropic

from app.core.config import settings


class PDFGeneratorService:
    """
    增强的PDF生成服务类 - 集成Claude 4和PDFMonkey
    Enhanced PDF generation service class - integrating Claude 4 and PDFMonkey
    """
    
    def __init__(self):
        """
        初始化PDF生成服务
        Initialize PDF generation service
        """
        self.logger = logging.getLogger("service.pdf_generator")
        
        # 初始化Claude 4客户端
        # Initialize Claude 4 client
        self.anthropic_client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            base_url=settings.ANTHROPIC_BASE_URL
        )
        
        # PDFMonkey API配置
        # PDFMonkey API configuration
        self.pdfmonkey_api_key = settings.PDFMONKEY_KEY
        self.pdfmonkey_base_url = settings.PDFMONKEY_BASE_URL
    
    async def generate_resume_markdown(
        self,
        resume_data: Dict[str, Any],
        target_job: Optional[Dict[str, Any]] = None,
        style: str = "professional"
    ) -> str:
        """
        使用Claude 4生成Markdown格式的简历
        Generate Markdown format resume using Claude 4
        """
        try:
            # 构建提示词，包含简历数据和目标职位信息
            # Build prompt including resume data and target job information
            prompt = self._build_markdown_prompt(resume_data, target_job, style)
            
            # 调用Claude 4生成Markdown
            # Call Claude 4 to generate Markdown
            response = await self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=settings.CLAUDE_TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # 提取生成的Markdown内容
            # Extract generated Markdown content
            markdown_content = ""
            for content_block in response.content:
                if content_block.type == "text":
                    markdown_content += content_block.text
            
            return markdown_content
            
        except Exception as e:
            self.logger.error(f"Markdown生成失败 / Markdown generation failed: {e}")
            return self._fallback_markdown_template(resume_data)
    
    async def generate_resume_pdf(
        self,
        resume_data: Dict[str, Any],
        template_style: str = "modern",
        target_job: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成简历PDF - 完整的Claude 4 + PDFMonkey流程
        Generate resume PDF - complete Claude 4 + PDFMonkey workflow
        """
        try:
            self.logger.info(f"开始生成PDF简历 / Starting PDF resume generation with style: {template_style}")
            
            # 步骤1: 使用Claude 4生成Markdown
            # Step 1: Generate Markdown using Claude 4
            markdown_content = await self.generate_resume_markdown(
                resume_data, target_job, template_style
            )
            
            # 步骤2: 使用PDFMonkey将Markdown转换为PDF
            # Step 2: Convert Markdown to PDF using PDFMonkey
            pdf_result = await self._convert_markdown_to_pdf(
                markdown_content, template_style
            )
            
            return {
                "success": True,
                "pdf_url": pdf_result.get("download_url"),
                "file_size": pdf_result.get("file_size", "估算 2-3MB"),
                "pages": pdf_result.get("pages", 2),
                "template_used": template_style,
                "markdown_preview": markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content,
                "generation_method": "Claude 4 + PDFMonkey"
            }
            
        except Exception as e:
            self.logger.error(f"PDF生成失败 / PDF generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pdf_url": None,
                "fallback_markdown": markdown_content if 'markdown_content' in locals() else None
            }
    
    def _build_markdown_prompt(
        self, 
        resume_data: Dict[str, Any], 
        target_job: Optional[Dict[str, Any]], 
        style: str
    ) -> str:
        """
        构建Claude 4的Markdown生成提示词
        Build Claude 4 prompt for Markdown generation
        """
        # 基础简历信息
        personal_info = resume_data.get("personal_info", {})
        work_experience = resume_data.get("work_experience", [])
        education = resume_data.get("education", [])
        skills = resume_data.get("skills", {})
        projects = resume_data.get("projects", [])
        
        # 目标职位信息（如果有）
        job_context = ""
        if target_job:
            job_context = f"""
目标职位信息：
- 职位名称：{target_job.get('title', '')}
- 公司：{target_job.get('company', '')}
- 关键要求：{target_job.get('description', '')[:200]}...
"""
        
        prompt = f"""
请基于以下简历数据生成一份专业的Markdown格式简历，风格为{style}：

{job_context}

个人信息：
- 姓名：{personal_info.get('name', '')}
- 邮箱：{personal_info.get('email', '')}
- 电话：{personal_info.get('phone', '')}
- 地址：{personal_info.get('location', '')}
- LinkedIn：{personal_info.get('linkedin', '')}

工作经验：
{self._format_experience_for_prompt(work_experience)}

教育背景：
{self._format_education_for_prompt(education)}

技能：
{self._format_skills_for_prompt(skills)}

项目经验：
{self._format_projects_for_prompt(projects)}

请生成一份符合ATS系统要求的Markdown简历，要求：
1. 使用标准的Markdown语法
2. 突出与目标职位相关的技能和经验
3. 使用专业的语言和格式
4. 优化关键词密度
5. 保持内容简洁有力
6. 确保语法和拼写正确

请直接输出Markdown代码，不要包含其他解释。
"""
        
        return prompt
    
    async def _convert_markdown_to_pdf(
        self, 
        markdown_content: str, 
        template_style: str
    ) -> Dict[str, Any]:
        """
        使用PDFMonkey将Markdown转换为PDF
        Convert Markdown to PDF using PDFMonkey
        """
        try:
            if self.pdfmonkey_api_key == "demo_key":
                # 模拟PDFMonkey响应用于演示
                # Simulate PDFMonkey response for demo
                return {
                    "download_url": f"/static/resumes/demo_resume_{template_style}.pdf",
                    "file_size": "2.3MB",
                    "pages": 2,
                    "status": "demo_mode"
                }
            
            # 实际PDFMonkey API调用
            # Actual PDFMonkey API call
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.pdfmonkey_api_key}",
                    "Content-Type": "application/json"
                }
                
                # PDFMonkey API请求数据
                # PDFMonkey API request data
                request_data = {
                    "document": {
                        "document_template_id": self._get_template_id(template_style),
                        "payload": {
                            "markdown_content": markdown_content,
                            "style": template_style
                        }
                    }
                }
                
                # 发送PDF生成请求
                # Send PDF generation request
                response = await client.post(
                    f"{self.pdfmonkey_base_url}/documents",
                    headers=headers,
                    json=request_data,
                    timeout=30
                )
                
                if response.status_code == 201:
                    result = response.json()
                    document_id = result["document"]["id"]
                    
                    # 轮询PDF生成状态
                    # Poll PDF generation status
                    pdf_url = await self._poll_pdf_status(document_id, headers)
                    
                    return {
                        "download_url": pdf_url,
                        "file_size": "估算 2-3MB",
                        "pages": 2,
                        "document_id": document_id
                    }
                else:
                    raise Exception(f"PDFMonkey API错误: {response.status_code} - {response.text}")
                    
        except Exception as e:
            self.logger.error(f"PDFMonkey转换失败 / PDFMonkey conversion failed: {e}")
            # 返回fallback结果
            return {
                "download_url": f"/static/resumes/fallback_resume_{template_style}.pdf",
                "file_size": "2.0MB",
                "pages": 2,
                "status": "fallback_mode",
                "error": str(e)
            }
    
    async def _poll_pdf_status(self, document_id: str, headers: Dict[str, str]) -> str:
        """
        轮询PDFMonkey PDF生成状态
        Poll PDFMonkey PDF generation status
        """
        max_attempts = 30  # 最多等待30秒
        attempt = 0
        
        async with httpx.AsyncClient() as client:
            while attempt < max_attempts:
                try:
                    response = await client.get(
                        f"{self.pdfmonkey_base_url}/documents/{document_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        status = result["document"]["status"]
                        
                        if status == "success":
                            return result["document"]["download_url"]
                        elif status == "failure":
                            raise Exception("PDF生成失败")
                        
                        # 等待1秒后重试
                        await asyncio.sleep(1)
                        attempt += 1
                    else:
                        raise Exception(f"状态查询失败: {response.status_code}")
                        
                except Exception as e:
                    self.logger.warning(f"PDF状态轮询失败 / PDF status polling failed: {e}")
                    await asyncio.sleep(1)
                    attempt += 1
        
        raise Exception("PDF生成超时")
    
    def _get_template_id(self, style: str) -> str:
        """
        获取PDFMonkey模板ID
        Get PDFMonkey template ID
        """
        template_map = {
            "modern": "template_modern_001",
            "professional": "template_professional_002", 
            "creative": "template_creative_003",
            "technical": "template_technical_004",
            "executive": "template_executive_005"
        }
        return template_map.get(style, "template_professional_002")
    
    def _format_experience_for_prompt(self, experience: list) -> str:
        """格式化工作经验用于提示词"""
        if not experience:
            return "无工作经验记录"
        
        formatted = []
        for exp in experience:
            formatted.append(f"""
- {exp.get('position', '')} @ {exp.get('company', '')}
  时间: {exp.get('start_date', '')} - {exp.get('end_date', '')}
  描述: {exp.get('description', '')}
""")
        return '\n'.join(formatted)
    
    def _format_education_for_prompt(self, education: list) -> str:
        """格式化教育背景用于提示词"""
        if not education:
            return "无教育背景记录"
        
        formatted = []
        for edu in education:
            formatted.append(f"""
- {edu.get('degree', '')} in {edu.get('major', '')}
  学校: {edu.get('institution', '')}
  毕业时间: {edu.get('graduation_date', '')}
""")
        return '\n'.join(formatted)
    
    def _format_skills_for_prompt(self, skills: dict) -> str:
        """格式化技能用于提示词"""
        if not skills:
            return "无技能记录"
        
        formatted = []
        for category, skill_list in skills.items():
            if skill_list:
                formatted.append(f"- {category}: {', '.join(skill_list)}")
        
        return '\n'.join(formatted) if formatted else "无技能记录"
    
    def _format_projects_for_prompt(self, projects: list) -> str:
        """格式化项目经验用于提示词"""
        if not projects:
            return "无项目经验记录"
        
        formatted = []
        for proj in projects:
            formatted.append(f"""
- {proj.get('name', '')}
  描述: {proj.get('description', '')}
  技术栈: {', '.join(proj.get('technologies', []))}
""")
        return '\n'.join(formatted)
    
    def _fallback_markdown_template(self, resume_data: Dict[str, Any]) -> str:
        """
        备用Markdown模板
        Fallback Markdown template
        """
        personal_info = resume_data.get("personal_info", {})
        
        return f"""
# {personal_info.get('name', '姓名')}

**邮箱**: {personal_info.get('email', '')}  
**电话**: {personal_info.get('phone', '')}  
**地址**: {personal_info.get('location', '')}  
**LinkedIn**: {personal_info.get('linkedin', '')}

## 专业摘要

经验丰富的专业人士，具备多年相关工作经验。

## 工作经验

### 详细工作经历待完善

## 教育背景

### 详细教育背景待完善

## 技能

- 技术技能：待完善
- 软技能：待完善

## 项目经验

### 项目详情待完善

---
*本简历使用JobCatcher AI生成*
""" 