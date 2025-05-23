"""
Agent系统API路由
Agent system API routes for JobCatcher multi-agent workflows
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.models.user import User
from app.api.auth import get_current_user
from app.agents.coordinator import AgentCoordinator, WorkflowType

router = APIRouter()

# 初始化Agent协调器
# Initialize Agent Coordinator
coordinator = AgentCoordinator()


class WorkflowRequest(BaseModel):
    """
    工作流请求模型
    Workflow request model
    """
    workflow_type: WorkflowType
    user_input: Dict[str, Any]
    session_id: Optional[str] = None


class WorkflowResponse(BaseModel):
    """
    工作流响应模型
    Workflow response model
    """
    success: bool
    workflow_type: str
    session_id: str
    execution_report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """
    工作流状态响应模型
    Workflow status response model
    """
    session_id: str
    status: str  # running, completed, failed
    current_agent: Optional[str]
    progress: int  # 0-100
    last_updated: str


@router.get("/capabilities")
async def get_agent_capabilities():
    """
    获取所有Agent的能力描述
    Get capabilities description of all agents
    """
    try:
        capabilities = coordinator.get_agent_capabilities()
        return {
            "success": True,
            "agents": capabilities,
            "total_agents": len(capabilities)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Agent能力失败 / Failed to get agent capabilities: {str(e)}"
        )


@router.get("/workflows")
async def get_available_workflows():
    """
    获取可用的工作流类型
    Get available workflow types
    """
    try:
        workflows = coordinator.get_available_workflows()
        return {
            "success": True,
            "workflows": workflows,
            "total_workflows": len(workflows)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流类型失败 / Failed to get workflow types: {str(e)}"
        )


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_request: WorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    执行Agent工作流
    Execute Agent workflow
    """
    try:
        # 验证工作流类型
        # Validate workflow type
        if workflow_request.workflow_type not in [wf.value for wf in WorkflowType]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的工作流类型 / Unsupported workflow type: {workflow_request.workflow_type}"
            )
        
        # 生成会话ID
        # Generate session ID
        session_id = workflow_request.session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id}"
        
        # 在后台执行工作流
        # Execute workflow in background
        result = await coordinator.execute_workflow(
            workflow_type=workflow_request.workflow_type,
            user_input=workflow_request.user_input,
            user_id=current_user.id,
            session_id=session_id
        )
        
        return WorkflowResponse(
            success=result["success"],
            workflow_type=str(workflow_request.workflow_type),
            session_id=session_id,
            execution_report=result.get("execution_report"),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"工作流执行失败 / Workflow execution failed: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取工作流执行状态
    Get workflow execution status
    """
    try:
        status_info = await coordinator.get_workflow_status(session_id)
        
        return WorkflowStatusResponse(
            session_id=status_info["session_id"],
            status=status_info["status"],
            current_agent=status_info.get("current_agent"),
            progress=status_info.get("progress", 0),
            last_updated=status_info.get("last_updated", datetime.now().isoformat())
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流状态失败 / Failed to get workflow status: {str(e)}"
        )


@router.post("/cancel/{session_id}")
async def cancel_workflow(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    取消工作流执行
    Cancel workflow execution
    """
    try:
        result = await coordinator.cancel_workflow(session_id)
        
        return {
            "success": result["success"],
            "session_id": session_id,
            "message": result.get("message", "工作流已取消 / Workflow cancelled"),
            "error": result.get("error")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消工作流失败 / Failed to cancel workflow: {str(e)}"
        )


# 各个Agent的单独调用接口
# Individual agent invocation endpoints

@router.post("/job-search")
async def search_jobs(
    search_criteria: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    直接调用职位搜索Agent
    Direct invocation of job search agent
    """
    try:
        result = await coordinator.execute_workflow(
            workflow_type=WorkflowType.JOB_SEARCH,
            user_input={"search_criteria": search_criteria},
            user_id=current_user.id
        )
        
        return {
            "success": result["success"],
            "job_results": result.get("execution_report", {}).get("final_results"),
            "error": result.get("error")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"职位搜索失败 / Job search failed: {str(e)}"
        )


@router.post("/resume-analysis")
async def analyze_resume(
    resume_data: Dict[str, Any],
    job_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    直接调用简历分析Agent
    Direct invocation of resume analysis agent
    """
    try:
        user_input = {
            "resume_data": resume_data,
            "job_data": job_data
        }
        
        result = await coordinator.execute_workflow(
            workflow_type=WorkflowType.RESUME_ANALYSIS,
            user_input=user_input,
            user_id=current_user.id
        )
        
        return {
            "success": result["success"],
            "analysis_results": result.get("execution_report", {}).get("final_results"),
            "error": result.get("error")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"简历分析失败 / Resume analysis failed: {str(e)}"
        )


@router.post("/skill-analysis")
async def analyze_skills(
    job_data: List[Dict[str, Any]],
    user_skills: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    直接调用技能分析Agent
    Direct invocation of skill analysis agent
    """
    try:
        user_input = {
            "job_data": job_data,
            "user_skills": user_skills or []
        }
        
        result = await coordinator.execute_workflow(
            workflow_type=WorkflowType.SKILL_ANALYSIS,
            user_input=user_input,
            user_id=current_user.id
        )
        
        return {
            "success": result["success"],
            "skill_analysis": result.get("execution_report", {}).get("final_results"),
            "error": result.get("error")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"技能分析失败 / Skill analysis failed: {str(e)}"
        )


@router.post("/resume-optimization")
async def optimize_resume(
    resume_data: Dict[str, Any],
    target_job: Optional[Dict[str, Any]] = None,
    optimization_style: str = "professional",
    current_user: User = Depends(get_current_user)
):
    """
    直接调用简历优化Agent
    Direct invocation of resume optimization agent
    """
    try:
        user_input = {
            "resume_data": resume_data,
            "target_job": target_job,
            "optimization_style": optimization_style
        }
        
        result = await coordinator.execute_workflow(
            workflow_type=WorkflowType.RESUME_OPTIMIZATION,
            user_input=user_input,
            user_id=current_user.id
        )
        
        return {
            "success": result["success"],
            "optimized_resume": result.get("execution_report", {}).get("final_results"),
            "error": result.get("error")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"简历优化失败 / Resume optimization failed: {str(e)}"
        )


@router.post("/comprehensive-analysis")
async def comprehensive_analysis(
    resume_data: Dict[str, Any],
    search_criteria: Dict[str, Any],
    optimization_preferences: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    综合分析：包含所有Agent功能的完整流程
    Comprehensive analysis: complete workflow with all agent functionalities
    """
    try:
        user_input = {
            "resume_data": resume_data,
            "search_criteria": search_criteria,
            "optimization_preferences": optimization_preferences or {}
        }
        
        result = await coordinator.execute_workflow(
            workflow_type=WorkflowType.COMPREHENSIVE,
            user_input=user_input,
            user_id=current_user.id
        )
        
        return {
            "success": result["success"],
            "comprehensive_results": result.get("execution_report", {}).get("final_results"),
            "execution_summary": result.get("execution_report"),
            "error": result.get("error")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"综合分析失败 / Comprehensive analysis failed: {str(e)}"
        )


@router.get("/health")
async def agent_health_check():
    """
    Agent系统健康检查
    Agent system health check
    """
    try:
        # 检查所有Agent的状态
        # Check status of all agents
        agent_status = {}
        for agent_name, agent in coordinator.agents.items():
            try:
                # 简单的健康检查 - 获取Agent信息
                agent_info = agent.get_agent_info()
                agent_status[agent_name] = {
                    "status": "healthy",
                    "info": agent_info
                }
            except Exception as e:
                agent_status[agent_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # 检查协调器状态
        # Check coordinator status
        coordinator_healthy = coordinator.workflow_graph is not None
        
        return {
            "success": True,
            "coordinator_status": "healthy" if coordinator_healthy else "unhealthy",
            "agents_status": agent_status,
            "total_agents": len(coordinator.agents),
            "healthy_agents": len([s for s in agent_status.values() if s["status"] == "healthy"]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败 / Health check failed: {str(e)}"
        ) 