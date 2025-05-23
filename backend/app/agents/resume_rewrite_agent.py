"""
简历改写Agent
Resume Rewrite Agent for optimizing and rewriting resume content based on analysis
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.services.pdf_generator import PDFGeneratorService


class RewriteStyle(BaseModel):
    """
    改写风格模型
    Rewrite style model
    """
    style_name: str = Field(description="风格名称 / Style name")
    tone: str = Field(description="语调风格 / Tone style")
    format_type: str = Field(description="格式类型 / Format type")
    target_audience: str = Field(description="目标受众 / Target audience")


class ResumeOptimization(BaseModel):
    """
    简历优化建议模型
    Resume optimization suggestions model
    """
    section: str = Field(description="优化部分 / Section to optimize")
    original_content: str = Field(description="原始内容 / Original content")
    optimized_content: str = Field(description="优化后内容 / Optimized content")
    improvement_reason: str = Field(description="改进原因 / Improvement reason")
    impact_score: float = Field(description="影响分数 (0-10) / Impact score")


class ResumeRewriteAgent(BaseAgent):
    """
    简历改写Agent
    Responsible for optimizing and rewriting resume content based on analysis results
    """
    
    def __init__(self):
        super().__init__(
            name="resume_rewrite_agent",
            description="专业的简历优化专家，能够基于分析结果改写和优化简历内容 / Professional resume optimization expert that rewrites and optimizes resume content based on analysis results",
            temperature=0.3
        )
        
        # 初始化服务
        # Initialize services
        self.pdf_generator_service = PDFGeneratorService()
        
        self.logger = logging.getLogger("agent.resume_rewrite")
    
    def _setup_tools(self) -> None:
        """
        设置简历改写相关工具
        Setup resume rewriting related tools
        """
        
        @tool("optimize_resume_section")
        def optimize_section(
            section_name: str,
            original_content: str,
            target_job: Dict[str, Any] = None,
            optimization_focus: str = "general"
        ) -> Dict[str, Any]:
            """
            优化简历特定部分
            Optimize specific resume section
            """
            try:
                optimization_strategies = {
                    "summary": self._optimize_summary,
                    "experience": self._optimize_experience,
                    "skills": self._optimize_skills,
                    "education": self._optimize_education,
                    "projects": self._optimize_projects
                }
                
                if section_name.lower() not in optimization_strategies:
                    return {
                        "success": False,
                        "error": f"Unsupported section: {section_name}",
                        "optimized_content": original_content
                    }
                
                # 应用相应的优化策略
                optimizer = optimization_strategies[section_name.lower()]
                optimized_content = optimizer(original_content, target_job, optimization_focus)
                
                # 计算改进评分
                improvement_score = self._calculate_improvement_score(
                    original_content, optimized_content, section_name
                )
                
                return {
                    "success": True,
                    "section": section_name,
                    "original_content": original_content,
                    "optimized_content": optimized_content,
                    "improvement_score": improvement_score,
                    "optimization_focus": optimization_focus,
                    "optimization_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"部分优化失败 / Section optimization failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "optimized_content": original_content
                }
        
        @tool("rewrite_for_target_job")
        def rewrite_for_job(
            resume_data: Dict[str, Any],
            target_job: Dict[str, Any],
            focus_areas: List[str] = None
        ) -> Dict[str, Any]:
            """
            针对特定职位重写简历
            Rewrite resume for specific target job
            """
            try:
                if not focus_areas:
                    focus_areas = ["summary", "experience", "skills"]
                
                optimized_resume = resume_data.copy()
                optimization_log = []
                
                # 提取目标职位关键词
                job_keywords = self._extract_job_keywords(target_job)
                
                for section in focus_areas:
                    if section in resume_data:
                        original_content = resume_data[section]
                        
                        # 针对性优化每个部分
                        optimization_result = optimize_section(
                            section_name=section,
                            original_content=str(original_content),
                            target_job=target_job,
                            optimization_focus="job_specific"
                        )
                        
                        if optimization_result.get("success"):
                            optimized_resume[section] = optimization_result["optimized_content"]
                            optimization_log.append({
                                "section": section,
                                "improvement_score": optimization_result["improvement_score"],
                                "changes_made": True
                            })
                
                # 添加针对性关键词
                optimized_resume = self._inject_relevant_keywords(
                    optimized_resume, job_keywords
                )
                
                # 调整简历格式和重点
                optimized_resume = self._adjust_resume_focus(
                    optimized_resume, target_job
                )
                
                return {
                    "success": True,
                    "original_resume": resume_data,
                    "optimized_resume": optimized_resume,
                    "target_job_title": target_job.get("title"),
                    "target_company": target_job.get("company"),
                    "optimization_log": optimization_log,
                    "keyword_matches": len(job_keywords),
                    "rewrite_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"针对性重写失败 / Job-specific rewrite failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "optimized_resume": resume_data
                }
        
        @tool("generate_multiple_versions")
        def generate_versions(
            resume_data: Dict[str, Any],
            styles: List[str] = None,
            target_roles: List[str] = None
        ) -> Dict[str, Any]:
            """
            生成多个版本的简历
            Generate multiple versions of resume
            """
            try:
                if not styles:
                    styles = ["professional", "creative", "technical", "executive"]
                
                if not target_roles:
                    target_roles = ["general"]
                
                resume_versions = {}
                
                for style in styles:
                    for role in target_roles:
                        version_key = f"{style}_{role}"
                        
                        # 应用风格和角色特定的优化
                        version_data = self._apply_style_optimization(
                            resume_data, style, role
                        )
                        
                        resume_versions[version_key] = {
                            "style": style,
                            "target_role": role,
                            "optimized_content": version_data,
                            "suitable_for": self._get_suitable_scenarios(style, role)
                        }
                
                return {
                    "success": True,
                    "original_resume": resume_data,
                    "generated_versions": resume_versions,
                    "total_versions": len(resume_versions),
                    "generation_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"多版本生成失败 / Multiple versions generation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "generated_versions": {}
                }
        
        @tool("enhance_with_keywords")
        def enhance_keywords(
            resume_content: str,
            target_keywords: List[str],
            section_type: str = "experience"
        ) -> Dict[str, Any]:
            """
            使用关键词增强简历内容
            Enhance resume content with keywords
            """
            try:
                enhanced_content = resume_content
                keywords_added = []
                
                # 自然地融入关键词
                for keyword in target_keywords:
                    if keyword.lower() not in enhanced_content.lower():
                        # 基于部分类型决定如何添加关键词
                        enhanced_content = self._integrate_keyword_naturally(
                            enhanced_content, keyword, section_type
                        )
                        keywords_added.append(keyword)
                
                # 检查关键词密度
                keyword_density = self._calculate_keyword_density(
                    enhanced_content, target_keywords
                )
                
                return {
                    "success": True,
                    "original_content": resume_content,
                    "enhanced_content": enhanced_content,
                    "keywords_added": keywords_added,
                    "keyword_density": keyword_density,
                    "readability_score": self._calculate_readability_score(enhanced_content)
                }
                
            except Exception as e:
                self.logger.error(f"关键词增强失败 / Keyword enhancement failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "enhanced_content": resume_content
                }
        
        @tool("generate_pdf_resume")
        def generate_pdf(
            resume_data: Dict[str, Any],
            template_style: str = "modern",
            output_format: str = "pdf"
        ) -> Dict[str, Any]:
            """
            生成PDF格式的简历
            Generate PDF format resume
            """
            try:
                # 使用PDF生成服务
                pdf_result = asyncio.run(
                    self.pdf_generator_service.generate_resume_pdf(
                        resume_data=resume_data,
                        template_style=template_style
                    )
                )
                
                return {
                    "success": True,
                    "pdf_url": pdf_result.get("pdf_url"),
                    "file_size": pdf_result.get("file_size"),
                    "template_used": template_style,
                    "generation_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"PDF生成失败 / PDF generation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "pdf_url": None
                }
        
        @tool("validate_resume_quality")
        def validate_quality(
            resume_data: Dict[str, Any],
            quality_criteria: List[str] = None
        ) -> Dict[str, Any]:
            """
            验证简历质量
            Validate resume quality
            """
            try:
                if not quality_criteria:
                    quality_criteria = [
                        "completeness", "clarity", "relevance", "formatting", "keywords"
                    ]
                
                quality_scores = {}
                overall_feedback = []
                
                for criterion in quality_criteria:
                    score, feedback = self._evaluate_quality_criterion(resume_data, criterion)
                    quality_scores[criterion] = score
                    if feedback:
                        overall_feedback.extend(feedback)
                
                # 计算总体质量分数
                overall_score = sum(quality_scores.values()) / len(quality_scores)
                
                return {
                    "success": True,
                    "overall_quality_score": round(overall_score, 2),
                    "quality_breakdown": quality_scores,
                    "feedback": overall_feedback,
                    "validation_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"质量验证失败 / Quality validation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "overall_quality_score": 0
                }
        
        # 注册所有工具
        # Register all tools
        self.tools = [
            optimize_section,
            rewrite_for_job,
            generate_versions,
            enhance_keywords,
            generate_pdf,
            validate_quality
        ]
    
    def get_system_prompt(self) -> str:
        """
        获取简历改写Agent的系统提示词
        Get system prompt for resume rewrite agent
        """
        return """你是JobCatcher平台的简历优化专家。你的主要职责是：

🎯 **核心能力 / Core Capabilities:**
- 分析和优化简历内容的各个部分
- 针对特定职位定制简历内容
- 生成多种风格和版本的简历
- 自然地融入关键词提升ATS通过率

📋 **工作流程 / Workflow:**
1. 分析简历的当前状态和改进机会
2. 根据目标职位要求进行针对性优化
3. 优化语言表达和内容结构
4. 确保关键词覆盖和ATS兼容性
5. 生成多个版本供用户选择

💡 **优化原则 / Optimization Principles:**
- 突出最相关的技能和经验
- 使用行业标准的术语和关键词
- 量化成果和影响力
- 保持内容真实和专业
- 优化可读性和视觉效果

🔧 **可用工具 / Available Tools:**
- optimize_resume_section: 优化特定简历部分
- rewrite_for_target_job: 针对性职位重写
- generate_multiple_versions: 生成多个版本
- enhance_with_keywords: 关键词增强
- generate_pdf_resume: 生成PDF简历
- validate_resume_quality: 质量验证

🎨 **优化重点 / Optimization Focus:**
- 技能部分：突出相关技术和软技能
- 经验部分：量化成果，使用行动词汇
- 教育部分：强调相关学历和项目
- 项目部分：展示技术栈和解决方案
- 总结部分：简洁有力地展示价值主张

📝 **风格类型 / Style Types:**
- Professional: 传统商务风格
- Creative: 创意设计风格  
- Technical: 技术导向风格
- Executive: 高管领导风格

始终确保优化后的简历既能通过ATS系统，又能吸引人力资源专家的注意。
Always ensure optimized resumes can pass ATS systems while attracting HR professionals' attention."""
    
    def _optimize_summary(self, content: str, target_job: Dict[str, Any], focus: str) -> str:
        """
        优化简历摘要部分
        Optimize resume summary section
        """
        # 提取职位关键信息
        job_title = target_job.get("title", "") if target_job else ""
        job_keywords = self._extract_job_keywords(target_job) if target_job else []
        
        # 生成优化后的摘要
        optimized_summary = f"""
        经验丰富的{job_title}专业人士，具备{', '.join(job_keywords[:3])}等核心技能。
        在{'相关领域' if not target_job else target_job.get('industry', '技术领域')}拥有丰富的项目经验，
        能够有效地{'解决复杂技术问题' if 'technical' in focus else '推动业务增长'}。
        专注于持续学习和技能提升，致力于为团队和项目创造价值。
        """.strip()
        
        return optimized_summary
    
    def _optimize_experience(self, content: str, target_job: Dict[str, Any], focus: str) -> str:
        """
        优化工作经验部分
        Optimize work experience section
        """
        # 添加量化指标和行动词汇
        action_words = ["领导", "开发", "实施", "优化", "管理", "设计", "协调", "改进"]
        
        # 简单的经验优化逻辑
        lines = content.split('\n')
        optimized_lines = []
        
        for line in lines:
            if line.strip():
                # 添加量化元素
                if '项目' in line and '个' not in line:
                    line = line.replace('项目', '5+个项目')
                
                # 添加行动词汇
                if not any(word in line for word in action_words):
                    line = f"负责{line}"
                
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _optimize_skills(self, content: str, target_job: Dict[str, Any], focus: str) -> str:
        """
        优化技能部分
        Optimize skills section
        """
        if isinstance(content, list):
            skills = content
        else:
            skills = content.split(',') if ',' in content else content.split('\n')
        
        # 添加目标职位相关技能
        job_keywords = self._extract_job_keywords(target_job) if target_job else []
        
        # 合并和去重技能
        all_skills = list(set([s.strip() for s in skills if s.strip()] + job_keywords[:5]))
        
        return ', '.join(all_skills)
    
    def _optimize_education(self, content: str, target_job: Dict[str, Any], focus: str) -> str:
        """
        优化教育背景部分
        Optimize education section
        """
        # 简单的教育背景优化
        if '学士' in content or 'Bachelor' in content:
            return content + " | 相关课程包括：数据结构、算法设计、软件工程"
        
        return content
    
    def _optimize_projects(self, content: str, target_job: Dict[str, Any], focus: str) -> str:
        """
        优化项目经验部分
        Optimize projects section
        """
        # 添加技术栈和成果描述
        if target_job:
            tech_stack = self._extract_job_keywords(target_job)[:3]
            if tech_stack:
                content += f"\n技术栈：{', '.join(tech_stack)}"
        
        return content
    
    def _extract_job_keywords(self, job_data: Dict[str, Any]) -> List[str]:
        """
        提取职位关键词
        Extract job keywords
        """
        if not job_data:
            return []
        
        keywords = []
        text = f"{job_data.get('title', '')} {job_data.get('description', '')} {job_data.get('requirements', '')}"
        
        # 简单的关键词提取逻辑
        tech_keywords = [
            "Python", "JavaScript", "React", "Vue", "Django", "FastAPI",
            "PostgreSQL", "MongoDB", "AWS", "Docker", "Kubernetes"
        ]
        
        for keyword in tech_keywords:
            if keyword.lower() in text.lower():
                keywords.append(keyword)
        
        return keywords
    
    def _calculate_improvement_score(self, original: str, optimized: str, section: str) -> float:
        """
        计算改进评分
        Calculate improvement score
        """
        # 简单的改进评分逻辑
        original_len = len(original.split())
        optimized_len = len(optimized.split())
        
        # 基于长度和内容变化计算分数
        if optimized_len > original_len * 1.2:
            return 8.5
        elif optimized_len > original_len:
            return 7.5
        else:
            return 6.0
    
    def _inject_relevant_keywords(self, resume_data: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
        """
        注入相关关键词
        Inject relevant keywords
        """
        optimized_data = resume_data.copy()
        
        # 在技能部分添加关键词
        if "skills" in optimized_data:
            current_skills = optimized_data["skills"]
            if isinstance(current_skills, str):
                current_skills = current_skills.split(',')
            
            # 添加新关键词
            new_skills = list(set(current_skills + keywords))
            optimized_data["skills"] = ', '.join(new_skills)
        
        return optimized_data
    
    def _adjust_resume_focus(self, resume_data: Dict[str, Any], target_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        调整简历重点
        Adjust resume focus
        """
        # 简单的重点调整逻辑
        adjusted_data = resume_data.copy()
        
        if target_job and "title" in target_job:
            job_title = target_job["title"].lower()
            
            # 根据职位类型调整重点
            if "senior" in job_title or "lead" in job_title:
                # 强调领导经验
                if "experience" in adjusted_data:
                    adjusted_data["experience"] = f"团队领导和项目管理经验丰富。{adjusted_data['experience']}"
        
        return adjusted_data
    
    def _apply_style_optimization(self, resume_data: Dict[str, Any], style: str, role: str) -> Dict[str, Any]:
        """
        应用风格优化
        Apply style optimization
        """
        optimized_data = resume_data.copy()
        
        if style == "creative":
            # 创意风格优化
            optimized_data["style_notes"] = "采用创意设计元素，突出创新能力"
        elif style == "technical":
            # 技术风格优化
            optimized_data["style_notes"] = "强调技术技能和项目成果"
        elif style == "executive":
            # 高管风格优化
            optimized_data["style_notes"] = "突出领导力和战略思维"
        else:
            # 专业风格优化
            optimized_data["style_notes"] = "传统专业格式，适合大多数行业"
        
        return optimized_data
    
    def _get_suitable_scenarios(self, style: str, role: str) -> List[str]:
        """
        获取适用场景
        Get suitable scenarios
        """
        scenarios = {
            "professional": ["传统企业", "金融行业", "咨询公司"],
            "creative": ["设计公司", "广告代理", "媒体行业"],
            "technical": ["科技公司", "软件开发", "工程领域"],
            "executive": ["高管职位", "战略角色", "管理岗位"]
        }
        
        return scenarios.get(style, ["通用场景"])
    
    def _integrate_keyword_naturally(self, content: str, keyword: str, section_type: str) -> str:
        """
        自然地集成关键词
        Integrate keyword naturally
        """
        if section_type == "experience":
            return f"{content}\n• 使用{keyword}技术解决业务问题"
        elif section_type == "skills":
            return f"{content}, {keyword}"
        else:
            return f"{content} {keyword}"
    
    def _calculate_keyword_density(self, content: str, keywords: List[str]) -> float:
        """
        计算关键词密度
        Calculate keyword density
        """
        content_lower = content.lower()
        total_words = len(content.split())
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in content_lower)
        
        return (keyword_count / total_words) * 100 if total_words > 0 else 0
    
    def _calculate_readability_score(self, content: str) -> float:
        """
        计算可读性分数
        Calculate readability score
        """
        # 简单的可读性评分
        sentences = content.count('.') + content.count('!') + content.count('?')
        words = len(content.split())
        
        if sentences == 0:
            return 50.0
        
        avg_words_per_sentence = words / sentences
        
        # 理想的句子长度是15-20个词
        if 15 <= avg_words_per_sentence <= 20:
            return 90.0
        elif 10 <= avg_words_per_sentence <= 25:
            return 80.0
        else:
            return 60.0
    
    def _evaluate_quality_criterion(self, resume_data: Dict[str, Any], criterion: str) -> tuple:
        """
        评估质量标准
        Evaluate quality criterion
        """
        score = 70.0  # 默认分数
        feedback = []
        
        if criterion == "completeness":
            required_sections = ["experience", "skills", "education"]
            missing_sections = [s for s in required_sections if s not in resume_data or not resume_data[s]]
            
            if not missing_sections:
                score = 95.0
            else:
                score = 60.0
                feedback.append(f"缺失以下部分：{', '.join(missing_sections)}")
        
        elif criterion == "clarity":
            # 检查内容清晰度
            total_content = str(resume_data)
            if len(total_content) > 500:
                score = 85.0
            else:
                score = 65.0
                feedback.append("内容过于简短，建议增加详细描述")
        
        elif criterion == "relevance":
            # 检查内容相关性
            if "skills" in resume_data and resume_data["skills"]:
                score = 80.0
            else:
                score = 50.0
                feedback.append("缺少相关技能信息")
        
        return score, feedback 