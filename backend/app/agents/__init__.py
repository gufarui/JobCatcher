"""
LangGraph 多Agent架构包
Multi-Agent architecture package using LangGraph for JobCatcher
"""

from app.agents.base import BaseAgent, AgentState
from app.agents.job_search_agent import JobSearchAgent
from app.agents.resume_critic_agent import ResumeCriticAgent
from app.agents.skill_heatmap_agent import SkillHeatmapAgent
from app.agents.resume_rewrite_agent import ResumeRewriteAgent
from app.agents.coordinator import AgentCoordinator

# 导出所有Agent类
# Export all Agent classes
__all__ = [
    "BaseAgent",
    "AgentState", 
    "JobSearchAgent",
    "ResumeCriticAgent",
    "SkillHeatmapAgent", 
    "ResumeRewriteAgent",
    "AgentCoordinator",
] 