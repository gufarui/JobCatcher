"""
Agent协调器
Agent Coordinator for managing and orchestrating multi-agent workflows
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.agents.job_search_agent import JobSearchAgent
from app.agents.resume_critic_agent import ResumeCriticAgent
from app.agents.skill_heatmap_agent import SkillHeatmapAgent
from app.agents.resume_rewrite_agent import ResumeRewriteAgent


class WorkflowType(str, Enum):
    """
    工作流类型枚举
    Workflow type enumeration
    """
    JOB_SEARCH = "job_search"
    RESUME_ANALYSIS = "resume_analysis"
    SKILL_ANALYSIS = "skill_analysis"
    RESUME_OPTIMIZATION = "resume_optimization"
    COMPREHENSIVE = "comprehensive"


class WorkflowStep(BaseModel):
    """
    工作流步骤模型
    Workflow step model
    """
    step_name: str = Field(description="步骤名称 / Step name")
    agent_name: str = Field(description="负责的Agent / Responsible agent")
    input_data: Dict[str, Any] = Field(description="输入数据 / Input data")
    output_data: Optional[Dict[str, Any]] = Field(description="输出数据 / Output data")
    status: str = Field(description="执行状态 / Execution status")
    start_time: Optional[datetime] = Field(description="开始时间 / Start time")
    end_time: Optional[datetime] = Field(description="结束时间 / End time")
    error_message: Optional[str] = Field(description="错误信息 / Error message")


class AgentCoordinator:
    """
    Agent协调器
    Responsible for coordinating and managing multi-agent workflows
    """
    
    def __init__(self):
        """
        初始化Agent协调器
        Initialize Agent Coordinator
        """
        # 初始化所有Agent
        # Initialize all agents
        self.agents = {
            "job_search_agent": JobSearchAgent(),
            "resume_critic_agent": ResumeCriticAgent(),
            "skill_heatmap_agent": SkillHeatmapAgent(),
            "resume_rewrite_agent": ResumeRewriteAgent()
        }
        
        # 工作流图
        # Workflow graph
        self.workflow_graph = None
        self._build_workflow_graph()
        
        self.logger = logging.getLogger("agent.coordinator")
    
    def _build_workflow_graph(self) -> None:
        """
        构建工作流图
        Build workflow graph
        """
        # 创建状态图
        # Create state graph
        workflow = StateGraph(AgentState)
        
        # 添加节点
        # Add nodes
        workflow.add_node("job_search_agent", self._job_search_node)
        workflow.add_node("resume_critic_agent", self._resume_critic_node)
        workflow.add_node("skill_heatmap_agent", self._skill_heatmap_node)
        workflow.add_node("resume_rewrite_agent", self._resume_rewrite_node)
        workflow.add_node("coordinator", self._coordinator_node)
        
        # 添加边和条件路由
        # Add edges and conditional routing
        workflow.add_edge(START, "coordinator")
        
        # 从协调器到各个Agent的路由
        workflow.add_conditional_edges(
            "coordinator",
            self._route_to_agent,
            {
                "job_search_agent": "job_search_agent",
                "resume_critic_agent": "resume_critic_agent", 
                "skill_heatmap_agent": "skill_heatmap_agent",
                "resume_rewrite_agent": "resume_rewrite_agent",
                "end": END
            }
        )
        
        # Agent间的相互转移
        # Inter-agent transfers
        for agent_name in self.agents.keys():
            workflow.add_conditional_edges(
                agent_name,
                self._determine_next_agent,
                {
                    "job_search_agent": "job_search_agent",
                    "resume_critic_agent": "resume_critic_agent",
                    "skill_heatmap_agent": "skill_heatmap_agent", 
                    "resume_rewrite_agent": "resume_rewrite_agent",
                    "coordinator": "coordinator",
                    "end": END
                }
            )
        
        self.workflow_graph = workflow.compile()
    
    async def execute_workflow(
        self,
        workflow_type: WorkflowType,
        user_input: Dict[str, Any],
        user_id: int,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        Execute workflow
        """
        try:
            self.logger.info(f"开始执行工作流 / Starting workflow: {workflow_type}")
            
            # 初始化状态
            # Initialize state
            initial_state = AgentState(
                messages=[],
                user_id=user_id,
                session_id=session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                session_start_time=datetime.now(),
                workflow_type=workflow_type,
                user_input=user_input
            )
            
            # 执行工作流图
            # Execute workflow graph
            final_state = await self.workflow_graph.ainvoke(initial_state)
            
            # 生成执行报告
            # Generate execution report
            execution_report = self._generate_execution_report(final_state)
            
            return {
                "success": True,
                "workflow_type": workflow_type,
                "execution_report": execution_report,
                "final_state": final_state,
                "session_id": session_id
            }
            
        except Exception as e:
            self.logger.error(f"工作流执行失败 / Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow_type": workflow_type
            }
    
    async def _job_search_node(self, state: AgentState) -> AgentState:
        """
        职位搜索节点
        Job search node
        """
        try:
            agent = self.agents["job_search_agent"]
            result = await agent.invoke(state)
            
            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"职位搜索节点执行失败 / Job search node failed: {e}")
            return state
    
    async def _resume_critic_node(self, state: AgentState) -> AgentState:
        """
        简历分析节点
        Resume critic node
        """
        try:
            agent = self.agents["resume_critic_agent"]
            result = await agent.invoke(state)
            
            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"简历分析节点执行失败 / Resume critic node failed: {e}")
            return state
    
    async def _skill_heatmap_node(self, state: AgentState) -> AgentState:
        """
        技能热点图节点
        Skill heatmap node
        """
        try:
            agent = self.agents["skill_heatmap_agent"]
            result = await agent.invoke(state)
            
            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"技能热点图节点执行失败 / Skill heatmap node failed: {e}")
            return state
    
    async def _resume_rewrite_node(self, state: AgentState) -> AgentState:
        """
        简历改写节点
        Resume rewrite node
        """
        try:
            agent = self.agents["resume_rewrite_agent"]
            result = await agent.invoke(state)
            
            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"简历改写节点执行失败 / Resume rewrite node failed: {e}")
            return state
    
    async def _coordinator_node(self, state: AgentState) -> AgentState:
        """
        协调器节点
        Coordinator node
        """
        # 分析用户输入和当前状态，决定下一步行动
        # Analyze user input and current state to decide next action
        workflow_type = state.get("workflow_type")
        user_input = state.get("user_input", {})
        
        # 设置下一个要执行的Agent
        # Set next agent to execute
        if workflow_type == WorkflowType.JOB_SEARCH:
            state["next_agent"] = "job_search_agent"
        elif workflow_type == WorkflowType.RESUME_ANALYSIS:
            state["next_agent"] = "resume_critic_agent"
        elif workflow_type == WorkflowType.SKILL_ANALYSIS:
            state["next_agent"] = "skill_heatmap_agent"
        elif workflow_type == WorkflowType.RESUME_OPTIMIZATION:
            state["next_agent"] = "resume_rewrite_agent"
        elif workflow_type == WorkflowType.COMPREHENSIVE:
            # 综合工作流的复杂逻辑
            state["next_agent"] = self._determine_comprehensive_flow(state)
        else:
            state["next_agent"] = "end"
        
        return state
    
    def _route_to_agent(self, state: AgentState) -> str:
        """
        路由到下一个Agent
        Route to next agent
        """
        next_agent = state.get("next_agent", "end")
        return next_agent
    
    def _determine_next_agent(self, state: AgentState) -> str:
        """
        确定下一个Agent
        Determine next agent
        """
        # 检查是否有Agent移交命令
        # Check for agent handoff commands
        last_message = state.get("messages", [])[-1] if state.get("messages") else None
        
        if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                if tool_call["name"].startswith("transfer_to_"):
                    target_agent = tool_call["name"].replace("transfer_to_", "")
                    return target_agent
        
        # 检查工作流是否完成
        # Check if workflow is complete
        current_agent = state.get("current_agent")
        workflow_type = state.get("workflow_type")
        
        if self._is_workflow_complete(state):
            return "end"
        
        # 返回协调器进行下一步决策
        # Return to coordinator for next decision
        return "coordinator"
    
    def _determine_comprehensive_flow(self, state: AgentState) -> str:
        """
        确定综合工作流的下一步
        Determine next step in comprehensive workflow
        """
        # 综合工作流的执行顺序：
        # 1. 职位搜索 -> 2. 简历分析 -> 3. 技能分析 -> 4. 简历优化
        
        completed_agents = state.get("completed_agents", [])
        
        if "job_search_agent" not in completed_agents:
            return "job_search_agent"
        elif "resume_critic_agent" not in completed_agents:
            return "resume_critic_agent"
        elif "skill_heatmap_agent" not in completed_agents:
            return "skill_heatmap_agent"
        elif "resume_rewrite_agent" not in completed_agents:
            return "resume_rewrite_agent"
        else:
            return "end"
    
    def _is_workflow_complete(self, state: AgentState) -> bool:
        """
        检查工作流是否完成
        Check if workflow is complete
        """
        workflow_type = state.get("workflow_type")
        completed_agents = state.get("completed_agents", [])
        error_count = state.get("error_count", 0)
        
        # 如果错误过多，终止工作流
        # Terminate workflow if too many errors
        if error_count > 5:
            return True
        
        # 根据工作流类型检查完成条件
        # Check completion condition based on workflow type
        if workflow_type == WorkflowType.JOB_SEARCH:
            return "job_search_agent" in completed_agents
        elif workflow_type == WorkflowType.RESUME_ANALYSIS:
            return "resume_critic_agent" in completed_agents
        elif workflow_type == WorkflowType.SKILL_ANALYSIS:
            return "skill_heatmap_agent" in completed_agents
        elif workflow_type == WorkflowType.RESUME_OPTIMIZATION:
            return "resume_rewrite_agent" in completed_agents
        elif workflow_type == WorkflowType.COMPREHENSIVE:
            required_agents = ["job_search_agent", "resume_critic_agent", "skill_heatmap_agent", "resume_rewrite_agent"]
            return all(agent in completed_agents for agent in required_agents)
        
        return False
    
    def _generate_execution_report(self, final_state: AgentState) -> Dict[str, Any]:
        """
        生成执行报告
        Generate execution report
        """
        report = {
            "workflow_type": final_state.get("workflow_type"),
            "session_id": final_state.get("session_id"),
            "start_time": final_state.get("session_start_time"),
            "end_time": datetime.now(),
            "total_agents_executed": len(final_state.get("completed_agents", [])),
            "total_tokens_used": final_state.get("total_tokens_used", 0),
            "error_count": final_state.get("error_count", 0),
            "execution_steps": [],
            "final_results": {}
        }
        
        # 计算执行时长
        if report["start_time"]:
            duration = report["end_time"] - report["start_time"]
            report["execution_duration_seconds"] = duration.total_seconds()
        
        # 提取各Agent的结果
        # Extract results from each agent
        completed_agents = final_state.get("completed_agents", [])
        for agent_name in completed_agents:
            agent_result = final_state.get(f"{agent_name}_result")
            if agent_result:
                report["final_results"][agent_name] = agent_result
        
        return report
    
    async def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """
        获取工作流状态
        Get workflow status
        """
        # 这里可以实现会话状态的持久化存储和查询
        # Here can implement persistent storage and querying of session states
        return {
            "session_id": session_id,
            "status": "completed",  # running, completed, failed
            "current_agent": None,
            "progress": 100,
            "last_updated": datetime.now().isoformat()
        }
    
    async def cancel_workflow(self, session_id: str) -> Dict[str, Any]:
        """
        取消工作流
        Cancel workflow
        """
        try:
            # 实现工作流取消逻辑
            # Implement workflow cancellation logic
            self.logger.info(f"取消工作流 / Canceling workflow: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "工作流已取消 / Workflow cancelled"
            }
            
        except Exception as e:
            self.logger.error(f"取消工作流失败 / Workflow cancellation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """
        获取可用的工作流类型
        Get available workflow types
        """
        return [
            {
                "type": WorkflowType.JOB_SEARCH,
                "name": "职位搜索 / Job Search",
                "description": "搜索和聚合多个来源的职位信息 / Search and aggregate job information from multiple sources",
                "estimated_duration": "2-5分钟 / 2-5 minutes",
                "agents_involved": ["job_search_agent"]
            },
            {
                "type": WorkflowType.RESUME_ANALYSIS,
                "name": "简历分析 / Resume Analysis", 
                "description": "分析简历质量和与职位的匹配度 / Analyze resume quality and job match scores",
                "estimated_duration": "3-7分钟 / 3-7 minutes",
                "agents_involved": ["resume_critic_agent"]
            },
            {
                "type": WorkflowType.SKILL_ANALYSIS,
                "name": "技能分析 / Skill Analysis",
                "description": "分析技能需求趋势和生成热点图 / Analyze skill demand trends and generate heatmaps",
                "estimated_duration": "4-8分钟 / 4-8 minutes", 
                "agents_involved": ["skill_heatmap_agent"]
            },
            {
                "type": WorkflowType.RESUME_OPTIMIZATION,
                "name": "简历优化 / Resume Optimization",
                "description": "优化和改写简历内容 / Optimize and rewrite resume content",
                "estimated_duration": "5-10分钟 / 5-10 minutes",
                "agents_involved": ["resume_rewrite_agent"]
            },
            {
                "type": WorkflowType.COMPREHENSIVE,
                "name": "综合分析 / Comprehensive Analysis",
                "description": "完整的求职辅助流程，包含所有功能 / Complete job hunting assistance process with all features",
                "estimated_duration": "15-30分钟 / 15-30 minutes",
                "agents_involved": ["job_search_agent", "resume_critic_agent", "skill_heatmap_agent", "resume_rewrite_agent"]
            }
        ]
    
    def get_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有Agent的能力描述
        Get capabilities description of all agents
        """
        capabilities = {}
        
        for agent_name, agent in self.agents.items():
            capabilities[agent_name] = agent.get_agent_info()
        
        return capabilities 