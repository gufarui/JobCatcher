"""
简历分析Agent
Resume Critic Agent for analyzing resume-job matching and scoring
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.services.resume_parser import ResumeParserService
from app.services.azure_search import AzureSearchService


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


class ResumeCriticAgent(BaseAgent):
    """
    简历分析Agent
    Responsible for analyzing resumes and calculating job match scores
    """
    
    def __init__(self):
        super().__init__(
            name="resume_critic_agent",
            description="专业的简历分析专家，能够分析简历质量并计算与职位的匹配度 / Professional resume analysis expert that analyzes resume quality and calculates job match scores",
            temperature=0.2
        )
        
        # 初始化服务
        # Initialize services
        self.resume_parser_service = ResumeParserService()
        self.azure_search_service = AzureSearchService()
        
        self.logger = logging.getLogger("agent.resume_critic")
    
    def _setup_tools(self) -> None:
        """
        设置简历分析相关工具
        Setup resume analysis related tools
        """
        
        @tool("parse_resume_file")
        def parse_resume(
            file_path: str,
            file_type: str = "pdf"
        ) -> Dict[str, Any]:
            """
            解析简历文件，提取结构化信息
            Parse resume file and extract structured information
            """
            try:
                result = asyncio.run(
                    self.resume_parser_service.parse_resume(
                        file_path=file_path,
                        file_type=file_type
                    )
                )
                return {
                    "success": True,
                    "parsed_data": result,
                    "extraction_timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                self.logger.error(f"简历解析失败 / Resume parsing failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "parsed_data": None
                }
        
        @tool("analyze_resume_quality")
        def analyze_resume_quality(
            resume_data: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            分析简历质量和完整性
            Analyze resume quality and completeness
            """
            try:
                # 评估简历各个部分的完整性
                # Evaluate completeness of resume sections
                quality_score = 0
                feedback = []
                
                # 基本信息检查 (20分)
                # Basic information check (20 points)
                if resume_data.get("personal_info"):
                    personal_info = resume_data["personal_info"]
                    if personal_info.get("name"):
                        quality_score += 5
                    if personal_info.get("email"):
                        quality_score += 5
                    if personal_info.get("phone"):
                        quality_score += 5
                    if personal_info.get("location"):
                        quality_score += 5
                else:
                    feedback.append("缺失基本个人信息 / Missing basic personal information")
                
                # 工作经验检查 (30分)
                # Work experience check (30 points)
                work_exp = resume_data.get("work_experience", [])
                if work_exp and len(work_exp) > 0:
                    quality_score += 15
                    # 检查经验描述的详细程度
                    detailed_descriptions = sum(1 for exp in work_exp if len(exp.get("description", "")) > 100)
                    if detailed_descriptions >= len(work_exp) * 0.7:
                        quality_score += 15
                    else:
                        feedback.append("工作经验描述过于简单 / Work experience descriptions are too brief")
                else:
                    feedback.append("缺失工作经验信息 / Missing work experience information")
                
                # 技能检查 (25分)
                # Skills check (25 points)
                skills = resume_data.get("skills", [])
                if skills and len(skills) >= 5:
                    quality_score += 15
                    # 检查技能的多样性
                    if len(skills) >= 10:
                        quality_score += 10
                    else:
                        feedback.append("建议添加更多相关技能 / Suggest adding more relevant skills")
                else:
                    feedback.append("技能列表过少 / Too few skills listed")
                
                # 教育背景检查 (15分)
                # Education check (15 points)
                education = resume_data.get("education", [])
                if education and len(education) > 0:
                    quality_score += 15
                else:
                    feedback.append("缺失教育背景信息 / Missing education information")
                
                # 项目经验检查 (10分)
                # Project experience check (10 points)
                projects = resume_data.get("projects", [])
                if projects and len(projects) > 0:
                    quality_score += 10
                else:
                    feedback.append("建议添加项目经验 / Suggest adding project experience")
                
                return {
                    "success": True,
                    "quality_score": min(quality_score, 100),
                    "feedback": feedback,
                    "strengths": self._identify_strengths(resume_data),
                    "improvement_areas": feedback
                }
                
            except Exception as e:
                self.logger.error(f"简历质量分析失败 / Resume quality analysis failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "quality_score": 0
                }
        
        @tool("calculate_job_match_score")
        def calculate_match_score(
            resume_data: Dict[str, Any],
            job_data: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            计算简历与职位的匹配度分数
            Calculate match score between resume and job
            """
            try:
                # 提取简历和职位的技能关键词
                resume_skills = self._extract_skills(resume_data)
                job_skills = self._extract_job_requirements(job_data)
                
                # 技术技能匹配 (40%)
                technical_score = self._calculate_technical_match(resume_skills, job_skills)
                
                # 经验匹配 (35%)
                experience_score = self._calculate_experience_match(resume_data, job_data)
                
                # 教育背景匹配 (15%)
                education_score = self._calculate_education_match(resume_data, job_data)
                
                # 其他因素 (10%)
                other_score = self._calculate_other_factors(resume_data, job_data)
                
                # 计算总体分数
                overall_score = (
                    technical_score * 0.4 +
                    experience_score * 0.35 +
                    education_score * 0.15 +
                    other_score * 0.1
                )
                
                # 识别匹配和缺失的技能
                matching_skills = list(set(resume_skills) & set(job_skills))
                missing_skills = list(set(job_skills) - set(resume_skills))
                
                return {
                    "success": True,
                    "overall_score": round(overall_score, 2),
                    "technical_score": round(technical_score, 2),
                    "experience_score": round(experience_score, 2),
                    "education_score": round(education_score, 2),
                    "other_score": round(other_score, 2),
                    "matching_skills": matching_skills,
                    "missing_skills": missing_skills,
                    "recommendations": self._generate_recommendations(missing_skills, resume_data, job_data)
                }
                
            except Exception as e:
                self.logger.error(f"匹配度计算失败 / Match score calculation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "overall_score": 0
                }
        
        @tool("batch_analyze_jobs")
        def batch_analyze_job_matches(
            resume_data: Dict[str, Any],
            job_list: List[Dict[str, Any]],
            top_k: int = 10
        ) -> Dict[str, Any]:
            """
            批量分析简历与多个职位的匹配度
            Batch analyze resume matches with multiple jobs
            """
            try:
                matches = []
                
                for job in job_list:
                    match_result = calculate_match_score(resume_data, job)
                    if match_result.get("success"):
                        matches.append({
                            "job_id": job.get("id"),
                            "job_title": job.get("title"),
                            "company": job.get("company"),
                            "match_score": match_result["overall_score"],
                            "technical_score": match_result["technical_score"],
                            "experience_score": match_result["experience_score"],
                            "education_score": match_result["education_score"],
                            "matching_skills": match_result["matching_skills"],
                            "missing_skills": match_result["missing_skills"]
                        })
                
                # 按匹配度排序
                matches.sort(key=lambda x: x["match_score"], reverse=True)
                
                return {
                    "success": True,
                    "total_analyzed": len(job_list),
                    "successful_matches": len(matches),
                    "top_matches": matches[:top_k],
                    "average_match_score": sum(m["match_score"] for m in matches) / len(matches) if matches else 0
                }
                
            except Exception as e:
                self.logger.error(f"批量分析失败 / Batch analysis failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "top_matches": []
                }
        
        # 添加移交工具
        # Add handoff tools
        transfer_to_rewrite = self.create_handoff_tool(
            target_agent="resume_rewrite_agent",
            description="将分析结果移交给简历改写专家进行优化 / Transfer analysis results to resume rewrite expert for optimization"
        )
        
        transfer_to_skill_heatmap = self.create_handoff_tool(
            target_agent="skill_heatmap_agent",
            description="将技能数据移交给技能分析专家生成热点图 / Transfer skill data to skill analysis expert for heatmap generation"
        )
        
        # 注册所有工具
        # Register all tools
        self.tools = [
            parse_resume,
            analyze_resume_quality,
            calculate_match_score,
            batch_analyze_job_matches,
            transfer_to_rewrite,
            transfer_to_skill_heatmap
        ]
    
    def get_system_prompt(self) -> str:
        """
        获取简历分析Agent的系统提示词
        Get system prompt for resume critic agent
        """
        return """你是JobCatcher平台的简历分析专家。你的主要职责是：

🎯 **核心能力 / Core Capabilities:**
- 解析和分析简历文件（PDF、DOCX等格式）
- 评估简历质量和完整性
- 计算简历与职位的匹配度分数
- 提供详细的改进建议和优化方案

📋 **工作流程 / Workflow:**
1. 接收简历文件并进行结构化解析
2. 分析简历的各个组成部分（技能、经验、教育等）
3. 计算与目标职位的匹配度（技术技能、经验、教育背景）
4. 生成详细的分析报告和改进建议
5. 如需要，移交给其他专家Agent进行进一步处理

💡 **评分标准 / Scoring Criteria:**
- 技术技能匹配 (40%): 关键技能覆盖度和熟练程度
- 工作经验匹配 (35%): 相关经验年限和项目复杂度
- 教育背景匹配 (15%): 学历要求和专业相关性
- 其他因素 (10%): 语言能力、认证资格、软技能等

🔧 **可用工具 / Available Tools:**
- parse_resume_file: 解析简历文件
- analyze_resume_quality: 分析简历质量
- calculate_job_match_score: 计算职位匹配度
- batch_analyze_jobs: 批量分析多个职位
- transfer_to_rewrite: 移交简历改写
- transfer_to_skill_heatmap: 移交技能分析

🎨 **分析重点 / Analysis Focus:**
- 客观、准确地评估简历质量
- 提供具体、可操作的改进建议
- 识别候选人的优势和不足
- 帮助用户了解市场需求和技能差距

始终保持专业和建设性的态度，帮助用户提升简历质量和求职竞争力。
Always maintain a professional and constructive attitude to help users improve resume quality and job competitiveness."""
    
    def _identify_strengths(self, resume_data: Dict[str, Any]) -> List[str]:
        """
        识别简历优势
        Identify resume strengths
        """
        strengths = []
        
        # 技能多样性
        skills = resume_data.get("skills", [])
        if len(skills) >= 10:
            strengths.append("技能范围广泛 / Wide range of skills")
        
        # 工作经验
        work_exp = resume_data.get("work_experience", [])
        if len(work_exp) >= 3:
            strengths.append("工作经验丰富 / Rich work experience")
        
        # 教育背景
        education = resume_data.get("education", [])
        for edu in education:
            if edu.get("degree") in ["Master", "PhD", "硕士", "博士"]:
                strengths.append("高等教育背景 / Advanced education background")
                break
        
        # 项目经验
        projects = resume_data.get("projects", [])
        if len(projects) >= 2:
            strengths.append("项目经验丰富 / Rich project experience")
        
        return strengths
    
    def _extract_skills(self, resume_data: Dict[str, Any]) -> List[str]:
        """
        提取简历中的技能关键词
        Extract skill keywords from resume
        """
        skills = []
        
        # 从技能部分提取
        if "skills" in resume_data:
            skills.extend(resume_data["skills"])
        
        # 从工作经验描述中提取技术关键词
        work_exp = resume_data.get("work_experience", [])
        tech_keywords = [
            "python", "javascript", "java", "react", "vue", "angular", "node.js", 
            "sql", "mongodb", "postgresql", "aws", "azure", "docker", "kubernetes",
            "machine learning", "ai", "data analysis", "tensorflow", "pytorch"
        ]
        
        for exp in work_exp:
            description = exp.get("description", "").lower()
            for keyword in tech_keywords:
                if keyword in description and keyword not in skills:
                    skills.append(keyword)
        
        return skills
    
    def _extract_job_requirements(self, job_data: Dict[str, Any]) -> List[str]:
        """
        提取职位要求中的技能关键词
        Extract skill keywords from job requirements
        """
        requirements = []
        
        # 从职位描述和要求中提取
        description = job_data.get("description", "")
        job_requirements = job_data.get("requirements", "")
        
        text = f"{description} {job_requirements}".lower()
        
        # 常见技术技能关键词
        tech_keywords = [
            "python", "javascript", "java", "react", "vue", "angular", "node.js",
            "sql", "mongodb", "postgresql", "aws", "azure", "docker", "kubernetes",
            "machine learning", "ai", "data analysis", "tensorflow", "pytorch",
            "git", "ci/cd", "microservices", "restful", "graphql"
        ]
        
        for keyword in tech_keywords:
            if keyword in text:
                requirements.append(keyword)
        
        return requirements
    
    def _calculate_technical_match(self, resume_skills: List[str], job_skills: List[str]) -> float:
        """
        计算技术技能匹配分数
        Calculate technical skills match score
        """
        if not job_skills:
            return 80.0  # 如果职位没有明确技能要求，给予中等分数
        
        matching_skills = set(resume_skills) & set(job_skills)
        match_ratio = len(matching_skills) / len(job_skills)
        
        return min(match_ratio * 100, 100)
    
    def _calculate_experience_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """
        计算经验匹配分数
        Calculate experience match score
        """
        # 简单的经验年限匹配计算
        work_exp = resume_data.get("work_experience", [])
        total_experience = len(work_exp)  # 简化计算
        
        # 从职位描述中推断所需经验
        required_exp = 2  # 默认要求2年经验
        description = job_data.get("description", "").lower()
        
        if "senior" in description or "lead" in description:
            required_exp = 5
        elif "junior" in description or "entry" in description:
            required_exp = 1
        
        if total_experience >= required_exp:
            return 90.0
        else:
            return (total_experience / required_exp) * 70
    
    def _calculate_education_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """
        计算教育背景匹配分数
        Calculate education background match score
        """
        education = resume_data.get("education", [])
        if not education:
            return 50.0
        
        # 检查最高学历
        highest_degree = ""
        for edu in education:
            degree = edu.get("degree", "").lower()
            if "phd" in degree or "博士" in degree:
                highest_degree = "phd"
            elif "master" in degree or "硕士" in degree and highest_degree != "phd":
                highest_degree = "master"
            elif "bachelor" in degree or "学士" in degree and highest_degree not in ["phd", "master"]:
                highest_degree = "bachelor"
        
        # 根据学历给分
        if highest_degree == "phd":
            return 100.0
        elif highest_degree == "master":
            return 90.0
        elif highest_degree == "bachelor":
            return 80.0
        else:
            return 60.0
    
    def _calculate_other_factors(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> float:
        """
        计算其他因素分数
        Calculate other factors score
        """
        score = 70.0  # 基础分数
        
        # 语言能力
        languages = resume_data.get("languages", [])
        if len(languages) > 1:
            score += 15
        
        # 认证资格
        certifications = resume_data.get("certifications", [])
        if certifications:
            score += 10
        
        # 项目经验
        projects = resume_data.get("projects", [])
        if len(projects) >= 2:
            score += 5
        
        return min(score, 100)
    
    def _generate_recommendations(self, missing_skills: List[str], resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> List[str]:
        """
        生成改进建议
        Generate improvement recommendations
        """
        recommendations = []
        
        if missing_skills:
            recommendations.append(f"建议学习以下技能：{', '.join(missing_skills[:5])} / Suggest learning these skills: {', '.join(missing_skills[:5])}")
        
        work_exp = resume_data.get("work_experience", [])
        if len(work_exp) < 2:
            recommendations.append("建议增加更多相关工作经验 / Suggest adding more relevant work experience")
        
        projects = resume_data.get("projects", [])
        if len(projects) < 2:
            recommendations.append("建议添加项目经验展示技能应用 / Suggest adding project experience to demonstrate skill application")
        
        skills = resume_data.get("skills", [])
        if len(skills) < 8:
            recommendations.append("建议补充更多相关技能 / Suggest adding more relevant skills")
        
        return recommendations 