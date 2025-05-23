"""
基础Agent类和状态管理
Base Agent class and state management for JobCatcher multi-agent system
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Annotated
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.core.config import settings


class AgentState(MessagesState):
    """
    JobCatcher Agent状态类
    Extended state class for JobCatcher agents
    """
    # 用户信息
    # User information
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    
    # 上下文数据
    # Context data
    current_resume_id: Optional[str] = None
    search_criteria: Optional[Dict[str, Any]] = None
    job_results: Optional[List[Dict[str, Any]]] = None
    
    # Agent执行状态
    # Agent execution state
    current_agent: Optional[str] = None
    next_agent: Optional[str] = None
    completed_agents: List[str] = []
    last_tool_output: Optional[Dict[str, Any]] = None
    error_count: int = 0
    
    # 工作流状态
    # Workflow state
    workflow_type: Optional[str] = None
    user_input: Optional[Dict[str, Any]] = None
    
    # 元数据
    # Metadata
    session_start_time: Optional[datetime] = None
    total_tokens_used: int = 0


class BaseAgent(ABC):
    """
    基础Agent抽象类
    Abstract base class for all JobCatcher agents
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        model_name: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.1,
        max_tokens: int = 4000
    ):
        """
        初始化Agent
        Initialize the agent
        
        Args:
            name: Agent名称 / Agent name
            description: Agent描述 / Agent description  
            model_name: 使用的模型名称 / Model name to use
            temperature: 模型温度参数 / Model temperature
            max_tokens: 最大token数 / Maximum tokens
        """
        self.name = name
        self.description = description
        self.model_name = model_name
        
        # 初始化LLM
        # Initialize LLM
        self.llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.ANTHROPIC_API_KEY
        )
        
        # 初始化工具列表
        # Initialize tools list
        self.tools: List[BaseTool] = []
        self._setup_tools()
        
        # 绑定工具到LLM
        # Bind tools to LLM
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm
            
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def _setup_tools(self) -> None:
        """
        设置Agent专用工具 (子类实现)
        Setup agent-specific tools (implemented by subclasses)
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词 (子类实现)
        Get system prompt (implemented by subclasses)
        """
        pass
    
    def create_handoff_tool(self, target_agent: str, description: str) -> BaseTool:
        """
        创建移交工具，用于转移到其他Agent
        Create handoff tool for transferring to other agents
        """
        from langchain_core.tools import tool
        from langgraph.prebuilt import InjectedState, InjectedToolCallId
        
        @tool(f"transfer_to_{target_agent}", description=description)
        def handoff_tool(
            reason: str,
            state: Annotated[AgentState, InjectedState],
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            """
            移交到其他Agent
            Transfer to another agent
            """
            tool_message = ToolMessage(
                content=f"Successfully transferred to {target_agent}. Reason: {reason}",
                tool_call_id=tool_call_id
            )
            
            return Command(
                goto=target_agent,
                update={
                    "messages": state["messages"] + [tool_message],
                    "current_agent": target_agent
                },
                graph=Command.PARENT
            )
        
        return handoff_tool
    
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        """
        调用Agent处理请求
        Invoke agent to process request
        """
        try:
            self.logger.info(f"Agent {self.name} 开始处理请求 / Starting to process request")
            
            # 获取系统提示词
            # Get system prompt
            system_prompt = self.get_system_prompt()
            
            # 构建消息历史
            # Build message history
            messages = []
            
            # 添加系统消息
            # Add system message
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 添加用户消息历史
            # Add user message history
            messages.extend([
                {"role": msg.type, "content": msg.content}
                for msg in state.get("messages", [])
                if isinstance(msg, (HumanMessage, AIMessage))
            ])
            
            # 调用LLM
            # Invoke LLM
            response = await self.llm_with_tools.ainvoke(messages)
            
            # 更新token使用统计
            # Update token usage statistics
            token_count = getattr(response, 'usage', {}).get('total_tokens', 0)
            
            # 记录日志
            # Log response
            self.logger.info(f"Agent {self.name} 处理完成 / Processing completed")
            
            return {
                "messages": [response],
                "current_agent": self.name,
                "total_tokens_used": state.get("total_tokens_used", 0) + token_count,
                "last_tool_output": None
            }
            
        except Exception as e:
            self.logger.error(f"Agent {self.name} 处理失败 / Processing failed: {str(e)}")
            
            error_message = AIMessage(
                content=f"抱歉，{self.name} 处理请求时出现错误：{str(e)} / Sorry, {self.name} encountered an error: {str(e)}"
            )
            
            return {
                "messages": [error_message],
                "current_agent": self.name,
                "error_count": state.get("error_count", 0) + 1
            }
    
    def should_continue(self, state: AgentState) -> bool:
        """
        判断Agent是否应该继续处理
        Determine if agent should continue processing
        """
        # 检查错误次数
        # Check error count
        if state.get("error_count", 0) > 3:
            return False
        
        # 检查最后一条消息是否有工具调用
        # Check if last message has tool calls
        last_message = state.get("messages", [])[-1] if state.get("messages") else None
        if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return True
        
        return False
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取Agent信息
        Get agent information
        """
        return {
            "name": self.name,
            "description": self.description,
            "model_name": self.model_name,
            "tools_count": len(self.tools),
            "tools": [tool.name for tool in self.tools] if self.tools else []
        } 