"""
简历分析Agent
Resume Critic Agent for analyzing resume-job matching and scoring
使用Claude 4文档处理能力进行智能简历解析和匹配度分析
Using Claude 4 document processing capabilities for intelligent resume parsing and match analysis
"""

import logging
import asyncio
import json
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.tools import tool, BaseTool
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.services.azure_search import get_search_service
from app.core.config import settings


class ResumeParseInput(BaseModel):
    """简历解析工具输入参数模型"""
    file_content: str = Field(description="Base64编码的文件内容")
    file_type: str = Field(default="pdf", description="文件类型：pdf、doc或docx")


class SimilaritySearchInput(BaseModel):
    """相似度搜索工具输入参数模型"""
    resume_content: str = Field(description="简历内容文本，用于语义匹配")
    job_preferences: str = Field(default="", description="职位偏好，如地点、行业等")
    top_k: int = Field(default=20, description="返回匹配职位数量，默认20")


class SkillAnalysisInput(BaseModel):
    """技能分析工具输入参数模型"""
    jobs_data: str = Field(description="职位数据JSON字符串")
    resume_skills: List[str] = Field(description="简历中的技能列表")


class JobMatchInput(BaseModel):
    """职位匹配工具输入参数模型"""
    resume_data: Dict[str, Any] = Field(description="解析后的简历数据")
    job_data: Dict[str, Any] = Field(description="职位数据")


class MatchingResult(BaseModel):
    """
    匹配结果模型
    Matching result model
    """
    job_id: str = Field(description="职位ID / Job ID")
    overall_score: float = Field(description="总体匹配分数 (0-100) / Overall match score")
    technical_score: float = Field(description="技术技能匹配分数 / Technical skills match score")
    experience_score: float = Field(description="经验匹配分数 / Experience match score")
    education_score: float = Field(description="教育背景匹配分数 / Education match score")
    missing_skills: List[str] = Field(description="缺失的技能 / Missing skills")
    matching_skills: List[str] = Field(description="匹配的技能 / Matching skills")
    recommendations: List[str] = Field(description="改进建议 / Improvement recommendations")


class ResumeParsingTool(BaseTool):
    """
    Claude 4增强简历解析工具 - 使用文档处理能力
    Enhanced resume parsing tool using Claude 4 document processing capabilities
    """
    
    name: str = "parse_resume_document"
    description: str = """
    使用Claude 4的文档处理能力解析简历文件。支持PDF、DOC、DOCX格式。
    自动提取个人信息、工作经验、教育背景、技能等结构化数据。
    Parse resume files using Claude 4 document processing. Supports PDF, DOC, DOCX formats.
    Automatically extract personal info, work experience, education, skills as structured data.
    """
    args_schema: type[ResumeParseInput] = ResumeParseInput
    
    def _run(self, file_content: str, file_type: str = "pdf") -> str:
        """同步解析包装器"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._arun(file_content, file_type))
    
    async def _arun(self, file_content: str, file_type: str = "pdf") -> str:
        """
        异步简历解析 - 利用Claude 4文档处理
        Asynchronous resume parsing using Claude 4 document processing
        """
        try:
            import anthropic
            
            # 创建Anthropic客户端 / Create Anthropic client
            client = anthropic.AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                base_url=settings.ANTHROPIC_BASE_URL
            )
            
            # 确定媒体类型 / Determine media type
            media_type_map = {
                "pdf": "application/pdf",
                "doc": "application/msword", 
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
            media_type = media_type_map.get(file_type.lower(), "application/pdf")
            
            # 使用Claude 4文档处理API / Use Claude 4 document processing API
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",  # 使用rules指定的模型
                max_tokens=4000,
                temperature=settings.CLAUDE_TEMPERATURE,  # 使用统一的温度设置
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": file_content
                            }
                        },
                        {
                            "type": "text",
                            "text": """请解析这份简历并提取以下结构化信息，以JSON格式返回：

{
  "personal_info": {
    "name": "姓名",
    "email": "邮箱",
    "phone": "电话",
    "location": "地址",
    "linkedin": "LinkedIn链接"
  },
  "summary": "个人简介或职业目标",
  "work_experience": [
    {
      "company": "公司名称",
      "position": "职位",
      "start_date": "开始时间",
      "end_date": "结束时间",
      "description": "工作描述",
      "achievements": ["成就1", "成就2"]
    }
  ],
  "education": [
    {
      "institution": "学校名称",
      "degree": "学位",
      "major": "专业",
      "graduation_date": "毕业时间",
      "gpa": "成绩"
    }
  ],
  "skills": {
    "technical": ["技术技能"],
    "languages": ["语言技能"],
    "soft_skills": ["软技能"]
  },
  "projects": [
    {
      "name": "项目名称",
      "description": "项目描述",
      "technologies": ["使用技术"],
      "url": "项目链接"
    }
  ],
  "certifications": ["证书列表"],
  "languages": ["语言能力"],
  "additional_info": "其他信息"
}

请确保提取的信息准确且结构化。如果某些信息不存在，请使用空值或空数组。"""
                        }
                    ]
                }]
            )
            
            # 提取解析结果 / Extract parsing result
            parsed_content = ""
            for content_block in response.content:
                if content_block.type == "text":
                    parsed_content += content_block.text
            
            # 尝试提取JSON / Try to extract JSON
            try:
                # 查找JSON块 / Find JSON block
                import re
                json_match = re.search(r'\{[\s\S]*\}', parsed_content)
                if json_match:
                    json_str = json_match.group()
                    parsed_data = json.loads(json_str)
                    return json.dumps(parsed_data, ensure_ascii=False, indent=2)
                else:
                    return json.dumps({
                        "error": "无法提取结构化数据",
                        "raw_content": parsed_content
                    }, ensure_ascii=False)
            except json.JSONDecodeError:
                return json.dumps({
                    "error": "JSON解析失败",
                    "raw_content": parsed_content
                }, ensure_ascii=False)
            
        except Exception as e:
            logging.error(f"简历解析失败: {e}")
            return json.dumps({
                "error": f"简历解析失败: {str(e)}",
                "raw_content": ""
            }, ensure_ascii=False)


class SimilaritySearchTool(BaseTool):
    """
    相似度搜索工具 - 使用Azure AI Search进行语义匹配
    Similarity search tool - using Azure AI Search for semantic matching
    """
    
    name: str = "similarity_search"
    description: str = """
    基于简历内容进行语义相似度搜索，找到最匹配的职位。
    使用Azure AI Search的向量化搜索能力，提供精准的语义匹配。
    Perform semantic similarity search based on resume content to find best matching jobs.
    Uses Azure AI Search vectorized search for precise semantic matching.
    """
    args_schema: type[SimilaritySearchInput] = SimilaritySearchInput
    
    def _run(self, resume_content: str, job_preferences: str = "", top_k: int = 20) -> str:
        """同步相似度搜索"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._arun(resume_content, job_preferences, top_k))
    
    async def _arun(self, resume_content: str, job_preferences: str = "", top_k: int = 20) -> str:
        """异步相似度搜索"""
        try:
            search_service = await get_search_service()
            
            # 构建搜索查询 - 结合简历内容和职位偏好
            # Build search query - combine resume content and job preferences
            search_query = resume_content[:500]  # 限制查询长度
            if job_preferences:
                search_query += f" {job_preferences}"
            
            # 执行语义搜索
            # Execute semantic search
            jobs = await search_service.search_jobs(
                query=search_query,
                top=top_k
            )
            
            if not jobs:
                return json.dumps({
                    "status": "no_matches",
                    "message": "未找到匹配的职位。建议扩大搜索范围或调整简历关键词。",
                    "jobs": []
                }, ensure_ascii=False)
            
            # 格式化搜索结果，包含相似度分数
            # Format search results with similarity scores
            results = []
            for job in jobs:
                results.append({
                    "job_id": job.get("id", ""),
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "salary": job.get("salary", ""),
                    "description": job.get("description", "")[:300] + "..." if len(job.get("description", "")) > 300 else job.get("description", ""),
                    "skills": job.get("skills", []),
                    "source": job.get("source", ""),
                    "url": job.get("url", ""),
                    "similarity_score": job.get("@search.score", 0),
                    "indexed_at": job.get("indexed_at", "")
                })
            
            return json.dumps({
                "status": "success",
                "total": len(results),
                "jobs": results
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"相似度搜索时发生错误：{str(e)}",
                "jobs": []
            }, ensure_ascii=False)


class SkillAnalysisTool(BaseTool):
    """
    技能分析工具 - 分析职位技能要求并生成技能差距报告
    Skills analysis tool - analyze job skill requirements and generate skill gap report
    """
    
    name: str = "analyze_skill_gap"
    description: str = """
    分析职位列表中的技能要求，与简历技能对比，生成详细的技能差距和市场需求分析。
    提供技能热度排名、匹配度分析和职业发展建议。
    Analyze skill requirements in job listings, compare with resume skills, 
    generate detailed skill gap and market demand analysis with skill heat ranking.
    """
    args_schema: type[SkillAnalysisInput] = SkillAnalysisInput
    
    def _run(self, jobs_data: str, resume_skills: List[str]) -> str:
        """同步技能分析"""
        try:
            jobs = json.loads(jobs_data)
            
            # 收集所有职位的技能要求
            # Collect skill requirements from all jobs
            all_skills = {}
            job_count = len(jobs)
            
            for job in jobs:
                job_skills = job.get("skills", [])
                
                # 从职位描述中提取技能（增强版）
                # Extract skills from job description (enhanced version)
                description = job.get("description", "").lower()
                common_skills = [
                    "python", "java", "javascript", "react", "vue", "angular", "django", "fastapi",
                    "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
                    "aws", "azure", "gcp", "git", "linux", "nodejs", "typescript", "html", "css",
                    "machine learning", "ai", "data science", "pandas", "numpy", "tensorflow",
                    "pytorch", "flask", "spring", "microservices", "restful", "graphql",
                    "ci/cd", "jenkins", "gitlab", "terraform", "ansible", "prometheus"
                ]
                
                for skill in common_skills:
                    if skill in description:
                        job_skills.append(skill)
                
                # 统计技能出现频率
                # Count skill frequency
                for skill in set(job_skills):  # 去重
                    skill_lower = skill.lower().strip()
                    if skill_lower:
                        all_skills[skill_lower] = all_skills.get(skill_lower, 0) + 1
            
            # 生成技能分析报告
            # Generate skill analysis report
            analysis = {
                "total_jobs_analyzed": job_count,
                "market_demand_skills": [],
                "resume_skills": [skill.lower() for skill in resume_skills],
                "matching_skills": [],
                "missing_skills": [],
                "skill_recommendations": []
            }
            
            # 按需求量排序技能
            # Sort skills by demand
            sorted_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)
            
            for skill, count in sorted_skills[:25]:  # 取前25个热门技能
                demand_percentage = (count / job_count) * 100
                skill_data = {
                    "skill": skill,
                    "demand_count": count,
                    "demand_percentage": round(demand_percentage, 1)
                }
                analysis["market_demand_skills"].append(skill_data)
            
            # 分析技能匹配和差距
            # Analyze skill matching and gaps
            resume_skills_lower = [skill.lower() for skill in resume_skills]
            
            for skill_data in analysis["market_demand_skills"]:
                skill = skill_data["skill"]
                if skill in resume_skills_lower:
                    analysis["matching_skills"].append(skill_data)
                else:
                    analysis["missing_skills"].append(skill_data)
            
            # 生成技能建议
            # Generate skill recommendations
            high_demand_missing = [
                skill for skill in analysis["missing_skills"]
                if skill["demand_percentage"] > 25
            ]
            
            for skill_data in high_demand_missing[:5]:  # 取前5个高需求缺失技能
                analysis["skill_recommendations"].append({
                    "skill": skill_data["skill"],
                    "priority": "高" if skill_data["demand_percentage"] > 50 else "中",
                    "reason": f"市场需求度{skill_data['demand_percentage']}%，建议优先学习",
                    "learning_resources": self._get_learning_resources(skill_data["skill"])
                })
            
            return json.dumps(analysis, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"技能分析失败: {str(e)}",
                "analysis": {}
            }, ensure_ascii=False)
    
    def _get_learning_resources(self, skill: str) -> List[str]:
        """获取技能学习资源建议"""
        resources_map = {
            "python": ["Python官方文档", "Real Python", "Python Crash Course"],
            "javascript": ["MDN Web Docs", "JavaScript.info", "Eloquent JavaScript"],
            "react": ["React官方文档", "React Tutorial", "Full Stack Open"],
            "docker": ["Docker官方文档", "Docker Mastery", "Play with Docker"],
            "kubernetes": ["Kubernetes官方文档", "CKA认证", "Kubernetes in Action"],
            "aws": ["AWS官方培训", "AWS Certified Solutions Architect", "A Cloud Guru"],
            "machine learning": ["Coursera ML课程", "Kaggle Learn", "Fast.ai"]
        }
        
        return resources_map.get(skill.lower(), ["在线教程", "官方文档", "实践项目"])


class JobMatchScoreTool(BaseTool):
    """
    职位匹配度计算工具 - 综合评估简历与职位的匹配程度
    Job match scoring tool - comprehensive assessment of resume-job matching
    """
    
    name: str = "calculate_job_match"
    description: str = """
    计算简历与特定职位的综合匹配度分数。
    分析技能匹配、经验相关性、教育背景等多个维度，提供详细的匹配报告。
    Calculate comprehensive match score between resume and specific job.
    Analyzes skill matching, experience relevance, education background and provides detailed match report.
    """
    args_schema: type[JobMatchInput] = JobMatchInput
    
    def _run(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """计算匹配度分数"""
        try:
            # 提取数据 / Extract data
            resume_skills = self._extract_resume_skills(resume_data)
            job_skills = self._extract_job_skills(job_data)
            
            # 计算各维度分数 / Calculate dimension scores
            technical_score = self._calculate_technical_match(resume_skills, job_skills)
            experience_score = self._calculate_experience_match(resume_data, job_data)
            education_score = self._calculate_education_match(resume_data, job_data)
            
            # 计算综合分数 / Calculate overall score
            overall_score = (technical_score * 0.4 + experience_score * 0.35 + education_score * 0.25)
            
            # 分析技能匹配情况 / Analyze skill matching
            matching_skills = list(set(resume_skills) & set(job_skills))
            missing_skills = list(set(job_skills) - set(resume_skills))
            
            # 生成建议 / Generate recommendations
            recommendations = self._generate_recommendations(missing_skills, resume_data, job_data)
            
            # 构建结果 / Build result
            result = {
                "job_id": job_data.get("id", "unknown"),
                "job_title": job_data.get("title", ""),
                "company": job_data.get("company", ""),
                "overall_score": round(overall_score, 1),
                "dimension_scores": {
                    "technical_skills": round(technical_score, 1),
                    "experience": round(experience_score, 1),
                    "education": round(education_score, 1)
                },
                "skill_analysis": {
                    "matching_skills": matching_skills,
                    "missing_skills": missing_skills,
                    "skill_match_rate": round(len(matching_skills) / len(job_skills) * 100, 1) if job_skills else 0
                },
                "recommendations": recommendations,
                "match_level": self._get_match_level(overall_score)
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"匹配度计算失败: {str(e)}",
                "overall_score": 0
            }, ensure_ascii=False)
    
    def _extract_resume_skills(self, resume_data: Dict[str, Any]) -> List[str]:
        """提取简历技能"""
        skills = []
        skills_data = resume_data.get("skills", {})
        
        if isinstance(skills_data, dict):
            # 新格式：分类技能
            skills.extend(skills_data.get("technical", []))
            skills.extend(skills_data.get("languages", []))
            skills.extend(skills_data.get("soft_skills", []))
        elif isinstance(skills_data, list):
            # 旧格式：技能列表
            skills.extend(skills_data)
        
        # 从工作经验中提取技能
        for exp in resume_data.get("work_experience", []):
            description = exp.get("description", "").lower()
            # 简单关键词提取
            tech_keywords = ["python", "javascript", "java", "sql", "aws", "docker"]
            for keyword in tech_keywords:
                if keyword in description and keyword not in skills:
                    skills.append(keyword)
        
        return [skill.lower().strip() for skill in skills if skill]
    
    def _extract_job_skills(self, job_data: Dict[str, Any]) -> List[str]:
        """提取职位技能要求"""
        skills = job_data.get("skills", [])
        
        # 从描述中提取技能
        description = job_data.get("description", "").lower()
        tech_keywords = [
            "python", "javascript", "java", "react", "vue", "angular",
            "sql", "postgresql", "mongodb", "aws", "azure", "docker", "kubernetes"
        ]
        
        for keyword in tech_keywords:
            if keyword in description and keyword not in skills:
                skills.append(keyword)
        
        return [skill.lower().strip() for skill in skills if skill]
    
    def _calculate_technical_match(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """计算技术技能匹配分数"""
        if not job_skills:
            return 75.0  # 没有明确技能要求的职位给中等分数
        
        matching_skills = set(resume_skills) & set(job_skills)
        match_ratio = len(matching_skills) / len(job_skills)
        
        # 考虑技能数量奖励
        bonus = min(len(matching_skills) * 5, 25)  # 每个匹配技能+5分，最多+25分
        
        return min(match_ratio * 75 + bonus, 100)
    
    def _calculate_experience_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """计算经验匹配分数"""
        work_exp = resume_data.get("work_experience", [])
        total_years = len(work_exp)  # 简化计算：工作经历数量代表年限
        
        # 从职位描述推断经验要求
        description = job_data.get("description", "").lower()
        title = job_data.get("title", "").lower()
        
        required_years = 2  # 默认要求
        if any(word in description + title for word in ["senior", "lead", "principal"]):
            required_years = 5
        elif any(word in description + title for word in ["junior", "entry", "graduate"]):
            required_years = 1
        elif any(word in description + title for word in ["mid", "intermediate"]):
            required_years = 3
        
        if total_years >= required_years:
            return 90.0
        else:
            return max((total_years / required_years) * 70, 30)
    
    def _calculate_education_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """计算教育背景匹配分数"""
        education = resume_data.get("education", [])
        if not education:
            return 60.0  # 没有教育信息给中等分数
        
        # 分析最高学历
        highest_degree = ""
        relevant_major = False
        
        for edu in education:
            degree = edu.get("degree", "").lower()
            major = edu.get("major", "").lower()
            
            # 确定最高学历
            if any(word in degree for word in ["phd", "博士", "doctorate"]):
                highest_degree = "phd"
            elif any(word in degree for word in ["master", "硕士", "msc", "mba"]) and highest_degree != "phd":
                highest_degree = "master"
            elif any(word in degree for word in ["bachelor", "学士", "bsc", "ba"]) and highest_degree not in ["phd", "master"]:
                highest_degree = "bachelor"
            
            # 检查专业相关性
            if any(word in major for word in ["computer", "software", "engineering", "计算机", "软件"]):
                relevant_major = True
        
        # 根据学历和专业相关性评分
        base_score = {"phd": 100, "master": 85, "bachelor": 70}.get(highest_degree, 50)
        major_bonus = 15 if relevant_major else 0
        
        return min(base_score + major_bonus, 100)
    
    def _generate_recommendations(self, missing_skills: List[str], resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if missing_skills:
            high_priority = missing_skills[:3]  # 前3个关键技能
            recommendations.append(f"建议学习关键技能：{', '.join(high_priority)}")
        
        # 经验建议
        work_exp = resume_data.get("work_experience", [])
        if len(work_exp) < 2:
            recommendations.append("建议积累更多相关工作经验或项目经验")
        
        # 项目建议
        projects = resume_data.get("projects", [])
        if len(projects) < 2:
            recommendations.append("建议添加更多项目经验展示技术能力")
        
        # 认证建议
        certifications = resume_data.get("certifications", [])
        if not certifications:
            recommendations.append("考虑获得相关技术认证提升竞争力")
        
        return recommendations
    
    def _get_match_level(self, score: float) -> str:
        """获取匹配等级"""
        if score >= 85:
            return "高度匹配"
        elif score >= 70:
            return "较好匹配"
        elif score >= 55:
            return "中等匹配"
        else:
            return "匹配度较低"


class ResumeCriticAgent(BaseAgent):
    """
    增强的简历分析Agent - 使用Claude 4最新特性
    Enhanced Resume Critic Agent - using Claude 4 latest features
    负责简历解析、职位匹配分析和技能评估
    Responsible for resume parsing, job matching analysis and skill assessment
    """
    
    def __init__(self):
        super().__init__(
            name="ResumeCriticAgent",
            description="专业的简历分析专家，使用Claude 4进行智能简历解析和职位匹配分析"
        )
    
    def _setup_tools(self) -> None:
        """设置增强的工具集"""
        self.tools = [
            ResumeParsingTool(),
            SimilaritySearchTool(),
            SkillAnalysisTool(),
            JobMatchScoreTool()
        ]
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是JobCatcher的智能简历分析专家，充分利用Claude 4的最新能力。

## 🎯 核心职责
1. **智能简历解析**：使用Claude 4文档处理能力，准确提取简历信息
2. **精准匹配分析**：计算简历与职位的多维度匹配度
3. **技能差距识别**：分析市场需求与个人技能的差距
4. **职业发展建议**：提供个性化的职业规划建议

## 🛠️ 工具使用策略
- **parse_resume_document**: 解析上传的简历文件
  - 支持PDF、DOC、DOCX格式
  - 自动提取结构化信息
  - 使用Claude 4原生文档处理能力

- **similarity_search**: 语义搜索匹配职位
  - 基于简历内容进行语义匹配
  - 使用Azure AI Search向量检索
  - 返回相关度排序的职位列表

- **analyze_skill_gap**: 技能差距分析
  - 分析市场技能需求趋势
  - 识别个人技能优势和不足
  - 提供学习资源建议

- **calculate_job_match**: 职位匹配评分
  - 多维度匹配度计算（技能、经验、教育）
  - 详细的匹配报告
  - 个性化改进建议

## 📊 分析框架
**技能匹配度 (40%)**：
- 技术技能重叠度
- 技能相关性和深度
- 新兴技能价值

**经验匹配度 (35%)**：
- 工作年限匹配
- 行业相关性
- 职位级别对应

**教育背景 (25%)**：
- 学历要求匹配
- 专业相关性
- 持续学习能力

## 🎨 输出要求
始终提供：
1. **量化评分**：0-100分的匹配度评分
2. **定性分析**：优势、劣势、机会识别
3. **可行建议**：具体的技能提升和职业发展建议
4. **市场洞察**：技能热度和薪资趋势分析

## 💡 智能特色
- 利用Claude 4的原生推理能力进行深度分析
- 提供人性化的职业建议和发展路径
- 实时整合最新的行业技能需求趋势
- 支持多语言简历处理和跨国职位匹配

专注于为用户提供精准、实用的简历分析和职业发展指导！"""


# Agent实例化
# Agent instantiation
resume_critic_agent = ResumeCriticAgent() 