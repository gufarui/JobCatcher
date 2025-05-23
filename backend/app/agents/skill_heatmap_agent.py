"""
技能热点图Agent
Skill Heatmap Agent for analyzing skill demand trends and generating visualization data
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.services.azure_search import AzureSearchService


class SkillTrend(BaseModel):
    """
    技能趋势模型
    Skill trend model
    """
    skill_name: str = Field(description="技能名称 / Skill name")
    demand_score: float = Field(description="需求评分 (0-100) / Demand score")
    frequency: int = Field(description="出现频次 / Frequency")
    growth_rate: Optional[float] = Field(description="增长率 / Growth rate")
    avg_salary: Optional[float] = Field(description="平均薪资 / Average salary")
    job_count: int = Field(description="相关职位数量 / Related job count")


class SkillHeatmapAgent(BaseAgent):
    """
    技能热点图Agent
    Responsible for analyzing skill trends and generating heatmap visualization data
    """
    
    def __init__(self):
        super().__init__(
            name="skill_heatmap_agent",
            description="专业的技能趋势分析专家，能够分析技能需求热点并生成可视化数据 / Professional skill trend analysis expert that analyzes skill demand hotspots and generates visualization data",
            temperature=0.1
        )
        
        # 初始化服务
        # Initialize services
        self.azure_search_service = AzureSearchService()
        
        self.logger = logging.getLogger("agent.skill_heatmap")
    
    def _setup_tools(self) -> None:
        """
        设置技能分析相关工具
        Setup skill analysis related tools
        """
        
        @tool("extract_skills_from_jobs")
        def extract_skills_from_jobs(
            job_list: List[Dict[str, Any]],
            skill_categories: List[str] = None
        ) -> Dict[str, Any]:
            """
            从职位列表中提取技能关键词
            Extract skill keywords from job listings
            """
            try:
                if not skill_categories:
                    skill_categories = [
                        "programming_languages", "frameworks", "databases", 
                        "cloud_platforms", "tools", "soft_skills"
                    ]
                
                # 技能关键词字典
                skill_keywords = {
                    "programming_languages": [
                        "python", "javascript", "java", "typescript", "c++", "c#", "go", 
                        "rust", "php", "ruby", "swift", "kotlin", "scala", "r"
                    ],
                    "frameworks": [
                        "react", "vue", "angular", "django", "flask", "fastapi", "spring", 
                        "express", "nest.js", "laravel", "rails", "tensorflow", "pytorch"
                    ],
                    "databases": [
                        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", 
                        "oracle", "sql server", "cassandra", "dynamodb"
                    ],
                    "cloud_platforms": [
                        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", 
                        "jenkins", "gitlab ci", "github actions"
                    ],
                    "tools": [
                        "git", "jira", "figma", "photoshop", "tableau", "power bi", 
                        "excel", "slack", "notion"
                    ],
                    "soft_skills": [
                        "communication", "leadership", "teamwork", "problem solving", 
                        "project management", "agile", "scrum"
                    ]
                }
                
                # 统计技能出现频次
                skill_stats = defaultdict(lambda: {
                    "frequency": 0,
                    "jobs": [],
                    "total_salary": 0,
                    "salary_count": 0,
                    "category": ""
                })
                
                for job in job_list:
                    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
                    job_salary = (job.get('salary_min', 0) + job.get('salary_max', 0)) / 2 if job.get('salary_min') and job.get('salary_max') else 0
                    
                    for category, keywords in skill_keywords.items():
                        if category not in skill_categories:
                            continue
                        
                        for skill in keywords:
                            if skill.lower() in job_text:
                                skill_stats[skill]["frequency"] += 1
                                skill_stats[skill]["jobs"].append(job.get('id'))
                                skill_stats[skill]["category"] = category
                                
                                if job_salary > 0:
                                    skill_stats[skill]["total_salary"] += job_salary
                                    skill_stats[skill]["salary_count"] += 1
                
                # 计算需求评分和平均薪资
                max_frequency = max([stats["frequency"] for stats in skill_stats.values()]) if skill_stats else 1
                
                skill_trends = []
                for skill, stats in skill_stats.items():
                    if stats["frequency"] > 0:
                        demand_score = (stats["frequency"] / max_frequency) * 100
                        avg_salary = stats["total_salary"] / stats["salary_count"] if stats["salary_count"] > 0 else None
                        
                        skill_trends.append({
                            "skill_name": skill,
                            "demand_score": round(demand_score, 2),
                            "frequency": stats["frequency"],
                            "avg_salary": round(avg_salary, 2) if avg_salary else None,
                            "job_count": len(set(stats["jobs"])),
                            "category": stats["category"]
                        })
                
                # 按需求评分排序
                skill_trends.sort(key=lambda x: x["demand_score"], reverse=True)
                
                return {
                    "success": True,
                    "total_jobs_analyzed": len(job_list),
                    "unique_skills_found": len(skill_trends),
                    "skill_trends": skill_trends,
                    "categories_analyzed": skill_categories
                }
                
            except Exception as e:
                self.logger.error(f"技能提取失败 / Skill extraction failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "skill_trends": []
                }
        
        @tool("generate_heatmap_data")
        def generate_heatmap_data(
            skill_trends: List[Dict[str, Any]],
            heatmap_type: str = "category_demand"
        ) -> Dict[str, Any]:
            """
            生成热点图可视化数据
            Generate heatmap visualization data
            """
            try:
                if heatmap_type == "category_demand":
                    # 按类别聚合需求数据
                    category_data = defaultdict(lambda: {"total_demand": 0, "skill_count": 0, "skills": []})
                    
                    for skill in skill_trends:
                        category = skill.get("category", "other")
                        category_data[category]["total_demand"] += skill.get("demand_score", 0)
                        category_data[category]["skill_count"] += 1
                        category_data[category]["skills"].append({
                            "name": skill["skill_name"],
                            "demand": skill["demand_score"],
                            "frequency": skill["frequency"]
                        })
                    
                    # 计算平均需求分数
                    heatmap_data = []
                    for category, data in category_data.items():
                        avg_demand = data["total_demand"] / data["skill_count"] if data["skill_count"] > 0 else 0
                        heatmap_data.append({
                            "category": category,
                            "average_demand": round(avg_demand, 2),
                            "skill_count": data["skill_count"],
                            "top_skills": sorted(data["skills"], key=lambda x: x["demand"], reverse=True)[:5]
                        })
                    
                    heatmap_data.sort(key=lambda x: x["average_demand"], reverse=True)
                    
                elif heatmap_type == "skill_salary":
                    # 技能与薪资关系热点图
                    heatmap_data = []
                    for skill in skill_trends:
                        if skill.get("avg_salary"):
                            heatmap_data.append({
                                "skill_name": skill["skill_name"],
                                "demand_score": skill["demand_score"],
                                "avg_salary": skill["avg_salary"],
                                "job_count": skill["job_count"],
                                "value_score": skill["demand_score"] * (skill["avg_salary"] / 1000)  # 综合价值分数
                            })
                    
                    heatmap_data.sort(key=lambda x: x["value_score"], reverse=True)
                
                elif heatmap_type == "trending_skills":
                    # 趋势技能热点图（基于频次和需求）
                    heatmap_data = []
                    for skill in skill_trends[:20]:  # 取前20个技能
                        heatmap_data.append({
                            "skill_name": skill["skill_name"],
                            "demand_score": skill["demand_score"],
                            "frequency": skill["frequency"],
                            "category": skill.get("category", "other"),
                            "trend_score": skill["demand_score"] * (1 + skill["frequency"] / 100)  # 趋势分数
                        })
                    
                    heatmap_data.sort(key=lambda x: x["trend_score"], reverse=True)
                
                return {
                    "success": True,
                    "heatmap_type": heatmap_type,
                    "data_points": len(heatmap_data),
                    "heatmap_data": heatmap_data,
                    "generation_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"热点图数据生成失败 / Heatmap data generation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "heatmap_data": []
                }
        
        @tool("analyze_skill_gaps")
        def analyze_skill_gaps(
            user_skills: List[str],
            market_trends: List[Dict[str, Any]],
            target_role: str = None
        ) -> Dict[str, Any]:
            """
            分析用户技能差距
            Analyze user skill gaps compared to market trends
            """
            try:
                user_skills_lower = [skill.lower() for skill in user_skills]
                
                # 识别高需求但用户缺失的技能
                missing_high_demand = []
                matching_skills = []
                
                for trend in market_trends:
                    skill_name = trend["skill_name"].lower()
                    if skill_name in user_skills_lower:
                        matching_skills.append({
                            "skill": trend["skill_name"],
                            "demand_score": trend["demand_score"],
                            "category": trend.get("category", "other")
                        })
                    elif trend["demand_score"] > 50:  # 高需求技能阈值
                        missing_high_demand.append({
                            "skill": trend["skill_name"],
                            "demand_score": trend["demand_score"],
                            "avg_salary": trend.get("avg_salary"),
                            "category": trend.get("category", "other"),
                            "priority": "high" if trend["demand_score"] > 80 else "medium"
                        })
                
                # 按优先级排序缺失技能
                missing_high_demand.sort(key=lambda x: x["demand_score"], reverse=True)
                
                # 生成学习建议
                learning_recommendations = []
                for skill in missing_high_demand[:10]:  # 推荐前10个技能
                    if skill["priority"] == "high":
                        learning_recommendations.append(
                            f"优先学习 {skill['skill']} (需求度: {skill['demand_score']:.1f}%)"
                        )
                    else:
                        learning_recommendations.append(
                            f"建议学习 {skill['skill']} (需求度: {skill['demand_score']:.1f}%)"
                        )
                
                # 计算技能覆盖率
                total_relevant_skills = len([t for t in market_trends if t["demand_score"] > 30])
                skill_coverage = len(matching_skills) / total_relevant_skills if total_relevant_skills > 0 else 0
                
                return {
                    "success": True,
                    "skill_coverage_rate": round(skill_coverage * 100, 2),
                    "matching_skills_count": len(matching_skills),
                    "missing_skills_count": len(missing_high_demand),
                    "matching_skills": matching_skills,
                    "missing_high_demand_skills": missing_high_demand[:15],
                    "learning_recommendations": learning_recommendations,
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"技能差距分析失败 / Skill gap analysis failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "missing_high_demand_skills": []
                }
        
        @tool("generate_skill_roadmap")
        def generate_skill_roadmap(
            current_skills: List[str],
            target_role: str,
            market_data: List[Dict[str, Any]]
        ) -> Dict[str, Any]:
            """
            生成技能学习路线图
            Generate skill learning roadmap
            """
            try:
                # 根据目标角色筛选相关技能
                role_keywords = {
                    "frontend": ["react", "vue", "angular", "javascript", "typescript", "css", "html"],
                    "backend": ["python", "java", "node.js", "django", "spring", "postgresql", "mongodb"],
                    "fullstack": ["react", "vue", "python", "node.js", "postgresql", "mongodb", "aws"],
                    "data scientist": ["python", "r", "tensorflow", "pytorch", "sql", "tableau", "machine learning"],
                    "devops": ["docker", "kubernetes", "aws", "azure", "terraform", "jenkins", "git"]
                }
                
                target_skills = role_keywords.get(target_role.lower(), [])
                current_skills_lower = [skill.lower() for skill in current_skills]
                
                # 创建学习路径
                roadmap_phases = {
                    "foundation": {"duration": "1-2 months", "skills": []},
                    "intermediate": {"duration": "3-4 months", "skills": []},
                    "advanced": {"duration": "5-6 months", "skills": []},
                    "specialized": {"duration": "6+ months", "skills": []}
                }
                
                # 根据技能难度和市场需求分配到不同阶段
                for trend in market_data:
                    skill_name = trend["skill_name"].lower()
                    
                    if skill_name in target_skills and skill_name not in current_skills_lower:
                        skill_info = {
                            "name": trend["skill_name"],
                            "demand_score": trend["demand_score"],
                            "avg_salary": trend.get("avg_salary"),
                            "learning_priority": "high" if trend["demand_score"] > 70 else "medium"
                        }
                        
                        # 基础技能分配
                        if skill_name in ["html", "css", "javascript", "python", "sql", "git"]:
                            roadmap_phases["foundation"]["skills"].append(skill_info)
                        # 中级技能
                        elif skill_name in ["react", "vue", "django", "flask", "postgresql", "mongodb"]:
                            roadmap_phases["intermediate"]["skills"].append(skill_info)
                        # 高级技能
                        elif skill_name in ["kubernetes", "terraform", "microservices", "machine learning"]:
                            roadmap_phases["advanced"]["skills"].append(skill_info)
                        # 专业技能
                        else:
                            roadmap_phases["specialized"]["skills"].append(skill_info)
                
                # 按优先级排序每个阶段的技能
                for phase in roadmap_phases.values():
                    phase["skills"].sort(key=lambda x: x["demand_score"], reverse=True)
                
                return {
                    "success": True,
                    "target_role": target_role,
                    "current_skills_count": len(current_skills),
                    "roadmap_phases": roadmap_phases,
                    "estimated_total_duration": "6-8 months",
                    "generation_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"技能路线图生成失败 / Skill roadmap generation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "roadmap_phases": {}
                }
        
        # 添加移交工具
        # Add handoff tools
        transfer_to_resume_rewrite = self.create_handoff_tool(
            target_agent="resume_rewrite_agent",
            description="将技能分析结果移交给简历改写专家进行技能优化 / Transfer skill analysis results to resume rewrite expert for skill optimization"
        )
        
        # 注册所有工具
        # Register all tools
        self.tools = [
            extract_skills_from_jobs,
            generate_heatmap_data,
            analyze_skill_gaps,
            generate_skill_roadmap,
            transfer_to_resume_rewrite
        ]
    
    def get_system_prompt(self) -> str:
        """
        获取技能热点图Agent的系统提示词
        Get system prompt for skill heatmap agent
        """
        return """你是JobCatcher平台的技能趋势分析专家。你的主要职责是：

🎯 **核心能力 / Core Capabilities:**
- 分析职位市场中的技能需求趋势
- 生成技能热点图和可视化数据
- 识别用户技能差距和学习机会
- 制定个性化的技能学习路线图

📋 **工作流程 / Workflow:**
1. 从职位数据中提取技能关键词和需求信息
2. 分析技能的市场需求度、薪资影响和趋势
3. 生成不同类型的热点图可视化数据
4. 比较用户技能与市场需求，识别技能差距
5. 制定个性化的技能学习和发展路线图

💡 **分析维度 / Analysis Dimensions:**
- 技能需求频次和市场热度
- 技能与薪资水平的关联性
- 技能类别分布和发展趋势
- 用户技能覆盖率和竞争力评估

🔧 **可用工具 / Available Tools:**
- extract_skills_from_jobs: 从职位中提取技能数据
- generate_heatmap_data: 生成热点图可视化数据
- analyze_skill_gaps: 分析用户技能差距
- generate_skill_roadmap: 生成技能学习路线图
- transfer_to_resume_rewrite: 移交简历优化

📊 **可视化类型 / Visualization Types:**
- category_demand: 技能类别需求热点图
- skill_salary: 技能薪资关联热点图
- trending_skills: 趋势技能热点图
- skill_gaps: 技能差距分析图

🎨 **分析重点 / Analysis Focus:**
- 提供数据驱动的技能洞察
- 识别高ROI的学习投资方向
- 帮助用户制定职业发展策略
- 跟踪技能市场动态变化

始终基于真实的市场数据提供专业的技能分析和建议。
Always provide professional skill analysis and recommendations based on real market data.""" 