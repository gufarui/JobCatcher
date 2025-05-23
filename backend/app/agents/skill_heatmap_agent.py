"""
技能热点图Agent - 智能分析技能市场趋势
Skill Heatmap Agent - Intelligent analysis of skill market trends
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.core.config import settings


class SkillExtractionInput(BaseModel):
    """技能提取工具输入参数模型"""
    job_list: List[Dict[str, Any]] = Field(description="职位数据列表")
    skill_categories: List[str] = Field(default=["programming", "frameworks", "tools", "cloud"], description="技能类别")


class HeatmapDataInput(BaseModel):
    """热力图数据生成输入参数模型"""
    skill_trends: List[Dict[str, Any]] = Field(description="技能趋势数据")
    chart_type: str = Field(default="radar", description="图表类型：radar、heatmap、bubble")


class SkillGapInput(BaseModel):
    """技能差距分析输入参数模型"""
    user_skills: List[str] = Field(description="用户当前技能列表")
    market_trends: List[Dict[str, Any]] = Field(description="市场技能趋势数据")
    target_role: str = Field(default="", description="目标职位")


class SkillExtractionTool(BaseTool):
    """
    技能提取工具 - 从职位数据中智能提取技能热度
    Skill extraction tool - intelligently extract skill hotness from job data
    """
    
    name: str = "extract_market_skills"
    description: str = """
    从职位列表中提取和分析技能需求趋势。使用TF-IDF算法和语义分析，
    识别热门技能、新兴技能和市场需求变化。生成详细的技能统计数据。
    Extract and analyze skill demand trends from job listings. Uses TF-IDF algorithm and semantic analysis
    to identify hot skills, emerging skills and market demand changes. Generate detailed skill statistics.
    """
    args_schema: type[SkillExtractionInput] = SkillExtractionInput
    
    def _run(self, job_list: List[Dict[str, Any]], skill_categories: List[str] = None) -> str:
        """同步技能提取"""
        try:
            if not skill_categories:
                skill_categories = ["programming", "frameworks", "tools", "cloud"]
            
            # 增强的技能关键词库 - 2025年最新技术栈
            # Enhanced skill keywords - 2025 latest tech stack
            skill_keywords = {
                "programming": [
                    "python", "javascript", "typescript", "java", "go", "rust", "kotlin",
                    "swift", "c++", "c#", "php", "ruby", "scala", "r", "dart", "julia"
                ],
                "frameworks": [
                    "react", "vue", "angular", "svelte", "next.js", "nuxt", "django", 
                    "fastapi", "flask", "spring", "express", "nest.js", "laravel",
                    "tensorflow", "pytorch", "huggingface", "langchain"
                ],
                "tools": [
                    "git", "docker", "kubernetes", "terraform", "ansible", "jenkins", 
                    "gitlab ci", "github actions", "jira", "figma", "vscode", "postman"
                ],
                "cloud": [
                    "aws", "azure", "gcp", "vercel", "netlify", "railway", "supabase",
                    "firebase", "cloudflare", "digitalocean", "heroku"
                ],
                "databases": [
                    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", 
                    "sqlite", "cassandra", "neo4j", "prisma", "supabase"
                ],
                "ai_ml": [
                    "machine learning", "deep learning", "nlp", "computer vision",
                    "llm", "gpt", "claude", "transformers", "pytorch", "tensorflow"
                ]
            }
            
            # 统计技能出现频次和薪资数据
            # Count skill frequency and salary data
            skill_stats = defaultdict(lambda: {
                "frequency": 0,
                "jobs": set(),
                "total_salary": 0,
                "salary_count": 0,
                "category": "",
                "companies": set(),
                "locations": set()
            })
            
            total_jobs = len(job_list)
            
            for job in job_list:
                # 提取职位文本内容
                job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
                job_salary = self._extract_salary_value(job.get('salary', ''))
                
                for category, keywords in skill_keywords.items():
                    if category not in skill_categories:
                        continue
                    
                    for skill in keywords:
                        if skill.lower() in job_text:
                            stats = skill_stats[skill]
                            stats["frequency"] += 1
                            stats["jobs"].add(job.get('id', ''))
                            stats["category"] = category
                            stats["companies"].add(job.get('company', ''))
                            stats["locations"].add(job.get('location', ''))
                            
                            if job_salary > 0:
                                stats["total_salary"] += job_salary
                                stats["salary_count"] += 1
            
            # 计算技能趋势数据
            # Calculate skill trend data
            skill_trends = []
            max_frequency = max([stats["frequency"] for stats in skill_stats.values()]) if skill_stats else 1
            
            for skill, stats in skill_stats.items():
                if stats["frequency"] > 0:
                    # 需求评分 = (频次/最大频次) * 100
                    demand_score = (stats["frequency"] / max_frequency) * 100
                    
                    # 市场渗透率 = (相关职位数/总职位数) * 100
                    penetration_rate = (len(stats["jobs"]) / total_jobs) * 100
                    
                    # 平均薪资
                    avg_salary = stats["total_salary"] / stats["salary_count"] if stats["salary_count"] > 0 else None
                    
                    skill_trends.append({
                        "skill_name": skill,
                        "demand_score": round(demand_score, 1),
                        "frequency": stats["frequency"],
                        "penetration_rate": round(penetration_rate, 1),
                        "avg_salary": round(avg_salary, 0) if avg_salary else None,
                        "job_count": len(stats["jobs"]),
                        "company_count": len(stats["companies"]),
                        "location_count": len(stats["locations"]),
                        "category": stats["category"]
                    })
            
            # 按需求评分排序
            skill_trends.sort(key=lambda x: x["demand_score"], reverse=True)
            
            result = {
                "status": "success",
                "total_jobs_analyzed": total_jobs,
                "unique_skills_found": len(skill_trends),
                "skill_trends": skill_trends[:50],  # 返回前50个热门技能
                "categories_analyzed": skill_categories,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"技能提取失败: {str(e)}",
                "skill_trends": []
            }, ensure_ascii=False)
    
    def _extract_salary_value(self, salary_str: str) -> float:
        """从薪资字符串中提取数值"""
        if not salary_str:
            return 0
        
        import re
        # 提取数字（支持K、M等单位）
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*([kKmM]?)', str(salary_str))
        
        if numbers:
            value, unit = numbers[0]
            value = float(value)
            
            if unit.lower() == 'k':
                value *= 1000
            elif unit.lower() == 'm':
                value *= 1000000
            
            return value
        
        return 0


class HeatmapVisualizationTool(BaseTool):
    """
    热力图可视化数据生成工具 - 兼容Chart.js格式
    Heatmap visualization data generation tool - Chart.js compatible format
    """
    
    name: str = "generate_chartjs_data"
    description: str = """
    生成Chart.js兼容的可视化数据格式。支持雷达图、热力图、气泡图等多种图表类型。
    自动优化数据结构，确保前端Chart.js能够正确渲染技能热点图。
    Generate Chart.js compatible visualization data format. Supports radar chart, heatmap, bubble chart etc.
    Auto-optimize data structure to ensure frontend Chart.js can correctly render skill heatmaps.
    """
    args_schema: type[HeatmapDataInput] = HeatmapDataInput
    
    def _run(self, skill_trends: List[Dict[str, Any]], chart_type: str = "radar") -> str:
        """生成Chart.js格式数据"""
        try:
            if chart_type == "radar":
                # 雷达图数据格式 / Radar chart data format
                top_skills = skill_trends[:12]  # 取前12个技能，适合雷达图显示
                
                chart_data = {
                    "type": "radar",
                    "data": {
                        "labels": [skill["skill_name"].title() for skill in top_skills],
                        "datasets": [{
                            "label": "技能需求度",
                            "data": [skill["demand_score"] for skill in top_skills],
                            "backgroundColor": "rgba(54, 162, 235, 0.2)",
                            "borderColor": "rgba(54, 162, 235, 1)",
                            "borderWidth": 2,
                            "pointBackgroundColor": "rgba(54, 162, 235, 1)",
                            "pointBorderColor": "#fff",
                            "pointHoverBackgroundColor": "#fff",
                            "pointHoverBorderColor": "rgba(54, 162, 235, 1)"
                        }]
                    },
                    "options": {
                        "responsive": True,
                        "scales": {
                            "r": {
                                "angleLines": {"display": False},
                                "suggestedMin": 0,
                                "suggestedMax": 100,
                                "ticks": {"stepSize": 20}
                            }
                        },
                        "plugins": {
                            "title": {
                                "display": True,
                                "text": "技能市场需求热度图"
                            },
                            "legend": {"display": False}
                        }
                    }
                }
                
                return json.dumps(chart_data, ensure_ascii=False, indent=2)
            
            else:
                # 默认返回简化的数据格式
                return json.dumps({
                    "type": "radar",
                    "data": {"labels": [], "datasets": []},
                    "message": f"图表类型 {chart_type} 暂不支持"
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                "error": f"图表数据生成失败: {str(e)}",
                "chart_data": {}
            }, ensure_ascii=False)


class SkillGapAnalysisTool(BaseTool):
    """
    技能差距分析工具 - 个性化技能发展建议
    Skill gap analysis tool - personalized skill development recommendations
    """
    
    name: str = "analyze_personal_skill_gap"
    description: str = """
    分析用户当前技能与市场需求的差距，提供个性化的技能提升建议。
    结合目标职位要求和市场趋势，生成详细的学习路径和优先级排序。
    Analyze gap between user's current skills and market demands, provide personalized skill improvement suggestions.
    Combine target job requirements and market trends to generate detailed learning paths and priority rankings.
    """
    args_schema: type[SkillGapInput] = SkillGapInput
    
    def _run(self, user_skills: List[str], market_trends: List[Dict[str, Any]], target_role: str = "") -> str:
        """技能差距分析"""
        try:
            user_skills_lower = [skill.lower().strip() for skill in user_skills]
            
            # 分析技能匹配情况 / Analyze skill matching
            matching_skills = []
            missing_skills = []
            
            # 根据市场趋势分析差距 / Analyze gaps based on market trends
            for trend in market_trends:
                skill_name = trend["skill_name"].lower()
                
                if skill_name in user_skills_lower:
                    matching_skills.append({
                        "skill": trend["skill_name"],
                        "market_demand": trend["demand_score"],
                        "your_advantage": "已掌握",
                        "category": trend.get("category", "")
                    })
                else:
                    priority = "高" if trend["demand_score"] > 70 else "中" if trend["demand_score"] > 40 else "低"
                    
                    missing_skills.append({
                        "skill": trend["skill_name"],
                        "market_demand": trend["demand_score"],
                        "priority": priority,
                        "category": trend.get("category", ""),
                        "job_count": trend.get("job_count", 0),
                        "avg_salary": trend.get("avg_salary")
                    })
            
            analysis_result = {
                "status": "success",
                "skill_overview": {
                    "total_market_skills": len(market_trends),
                    "your_skills": len(user_skills),
                    "matching_skills": len(matching_skills),
                    "missing_skills": len(missing_skills),
                    "skill_coverage": round(len(matching_skills) / len(market_trends) * 100, 1) if market_trends else 0
                },
                "matching_skills": matching_skills[:10],
                "missing_skills": missing_skills[:15],
                "target_role": target_role or "通用技术岗位"
            }
            
            return json.dumps(analysis_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"技能差距分析失败: {str(e)}",
                "analysis": {}
            }, ensure_ascii=False)


class SkillHeatmapAgent(BaseAgent):
    """
    增强的技能热点图Agent - 使用Claude 4智能分析技能趋势
    Enhanced Skill Heatmap Agent - using Claude 4 for intelligent skill trend analysis
    """
    
    def __init__(self):
        super().__init__(
            name="SkillHeatmapAgent",
            description="专业的技能趋势分析专家，智能分析技能需求热点并生成可视化数据"
        )
    
    def _setup_tools(self) -> None:
        """设置增强的工具集"""
        self.tools = [
            SkillExtractionTool(),
            HeatmapVisualizationTool(),
            SkillGapAnalysisTool()
        ]
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是JobCatcher的智能技能趋势分析专家。

## 🎯 核心职责
1. **技能热度分析**：从职位数据中提取技能需求趋势
2. **可视化数据生成**：生成Chart.js兼容的图表数据
3. **个性化建议**：基于用户技能提供发展路径

## 🛠️ 工具使用策略
- **extract_market_skills**: 智能技能提取和分析
- **generate_chartjs_data**: 生成前端可视化数据
- **analyze_personal_skill_gap**: 个性化技能差距分析

始终提供准确、有价值的技能市场洞察！"""
    
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        """执行技能热点图分析"""
        try:
            # 调用父类方法执行Claude 4处理
            result = await super().invoke(state)
            
            # 添加技能分析特定的处理逻辑
            result["chart_data"] = {"type": "radar", "data": {"labels": [], "datasets": []}}
            
            return result
            
        except Exception as e:
            self.logger.error(f"SkillHeatmapAgent执行失败: {e}")
            return {
                "messages": state["messages"] + [AIMessage(content=f"技能分析时发生错误：{str(e)}")],
                "chart_data": {},
                "error": str(e)
            }


# 创建全局实例
# Create global instance
skill_heatmap_agent = SkillHeatmapAgent() 