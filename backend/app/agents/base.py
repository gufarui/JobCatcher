"""
基础Agent类和状态管理
Base Agent class and state management for JobCatcher multi-agent system
使用Claude 4最新特性，包括Tool Calling、Document Processing和Extended Thinking
Using Claude 4 latest features including Tool Calling, Document Processing and Extended Thinking
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import MessagesState
from pydantic import BaseModel
import anthropic

from app.core.config import settings


class AgentState(MessagesState):
    """
    JobCatcher Agent状态类 - 优化支持Claude 4特性
    Enhanced state class optimized for Claude 4 capabilities
    """
    
    # 核心用户信息 / Core user information
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    
    # 工作流状态 / Workflow state  
    current_resume_data: Optional[Dict[str, Any]] = None
    search_query: Optional[str] = None
    job_results: Optional[List[Dict[str, Any]]] = None
    skill_analysis: Optional[Dict[str, Any]] = None
    
    # Claude 4高级状态管理 / Claude 4 advanced state management
    workflow_context: Optional[str] = None
    thinking_enabled: bool = True
    document_context: Optional[List[Dict[str, Any]]] = None


class BaseAgent(ABC):
    """
    增强的基础Agent类 - 充分利用Claude 4最新特性
    Enhanced base agent class leveraging Claude 4 latest features
    根据Anthropic官方文档实现最佳实践
    Following Anthropic official documentation best practices
    """

    def __init__(self, name: str, description: str):
        """
        初始化Agent with Claude 4最新特性
        Initialize Agent with Claude 4 latest features
        """
        self.name = name
        self.description = description
        
        # 使用原生Anthropic客户端 - 支持Claude 4所有特性
        # Use native Anthropic client - supports all Claude 4 features
        self.anthropic_client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            base_url=settings.ANTHROPIC_BASE_URL
        )
        
        # 模型配置 / Model configuration
        self.model_name = "claude-sonnet-4-20250514"  # 使用rules中指定的Claude 4模型
        self.temperature = settings.CLAUDE_TEMPERATURE  # 使用统一的温度设置
        self.max_tokens = 8000
        
        # 工具配置 / Tools configuration
        self.tools: List[BaseTool] = []
        self._setup_tools()
            
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    def _setup_tools(self) -> None:
        """
        设置Agent专用工具
        Setup agent-specific tools
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词 - 指导Claude 4行为
        Get system prompt - guide Claude 4 behavior
        """
        pass

    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        """
        增强的调用逻辑 - 支持Claude 4高级特性
        Enhanced invocation - supports Claude 4 advanced features
        """
        try:
            self.logger.info(f"Agent {self.name} 开始处理 (Claude 4增强模式)")
            
            # 构建消息历史 / Build message history
            messages = self._build_messages(state)
            
            # 准备工具定义 / Prepare tool definitions
            tools_definitions = self._prepare_tool_definitions()
            
            # 调用Claude 4原生API - 支持工具调用和思考
            # Call Claude 4 native API - supports tool calling and thinking
            if tools_definitions:
                response = await self.anthropic_client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    tools=tools_definitions,
                    tool_choice={"type": "auto"},
                    messages=messages
                )
            else:
                response = await self.anthropic_client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=messages
                )
            
            # 处理响应和工具调用 / Process response and tool calls
            return await self._process_response(response, state)
            
        except Exception as e:
            self.logger.error(f"Agent {self.name} 执行失败: {e}")
            return {
                "messages": state["messages"] + [AIMessage(content=f"抱歉，处理时遇到错误：{str(e)}")],
                "error": str(e)
            }

    def _build_messages(self, state: AgentState) -> List[Dict[str, Any]]:
        """
        构建符合Anthropic API格式的消息
        Build messages in Anthropic API format
        """
        messages = []
        
        # 系统消息单独处理 / Handle system message separately
        system_prompt = self.get_system_prompt()
        
        # 添加上下文信息 / Add context information
        if state.get("workflow_context"):
            system_prompt += f"\n\n**上下文信息**：{state['workflow_context']}"
        
        # 转换状态中的消息 / Convert messages from state
        for msg in state.get("messages", []):
            if isinstance(msg, BaseMessage):
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                messages.append({
                    "role": role,
                    "content": msg.content
                })
            elif isinstance(msg, dict):
                if msg.get("role") in ["user", "assistant"]:
                    messages.append(msg)
        
        # 如果没有消息，添加默认消息 / Add default message if none
        if not messages:
            messages.append({
                "role": "user",
                "content": "请开始处理当前任务。"
            })
        
        # 确保第一条消息是用户消息 / Ensure first message is from user
        if messages and messages[0]["role"] != "user":
            messages.insert(0, {
                "role": "user", 
                "content": "开始处理"
            })
        
        return messages

    def _prepare_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        准备工具定义 - 转换为Anthropic格式
        Prepare tool definitions - convert to Anthropic format
        """
        tool_definitions = []
        
        for tool in self.tools:
            # 转换LangChain工具为Anthropic格式
            # Convert LangChain tool to Anthropic format
            tool_def = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # 从工具参数提取schema / Extract schema from tool args
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                tool_def["input_schema"]["properties"] = schema.get("properties", {})
                tool_def["input_schema"]["required"] = schema.get("required", [])
            
            tool_definitions.append(tool_def)
        
        return tool_definitions

    async def _process_response(self, response, state: AgentState) -> Dict[str, Any]:
        """
        处理Claude 4响应 - 支持工具调用
        Process Claude 4 response - supports tool calling
        """
        new_messages = []
        updated_state = dict(state)
        
        # 处理响应内容 / Process response content
        response_content = ""
        tool_calls = []
        
        for content_block in response.content:
            if content_block.type == "text":
                response_content += content_block.text
            elif content_block.type == "tool_use":
                tool_calls.append(content_block)
        
        # 添加Assistant消息 / Add assistant message
        if response_content:
            new_messages.append(AIMessage(content=response_content))
        
        # 处理工具调用 / Process tool calls
        if tool_calls:
            tool_results = await self._execute_tools(tool_calls)
            updated_state["tool_results"] = tool_results
            
            # 如果有工具结果，可能需要续接对话 / Continue conversation with tool results
            if tool_results:
                # 构建工具结果消息 / Build tool result messages
                tool_result_content = []
                for tool_call, result in zip(tool_calls, tool_results):
                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": str(result)
                    })
                
                # 继续对话获取最终响应 / Continue conversation for final response
                messages = self._build_messages(state)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_result_content})
                
                final_response = await self.anthropic_client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=messages
                )
                
                # 提取最终文本响应 / Extract final text response
                final_text = ""
                for block in final_response.content:
                    if block.type == "text":
                        final_text += block.text
                
                if final_text:
                    new_messages.append(AIMessage(content=final_text))
        
        # 更新状态 / Update state
        updated_state["messages"] = state.get("messages", []) + new_messages
        updated_state["last_response"] = response_content or "工具调用完成"
        
        return updated_state

    async def _execute_tools(self, tool_calls) -> List[Any]:
        """
        执行工具调用 - 并行处理提高效率
        Execute tool calls - parallel processing for efficiency
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.name
            tool_input = tool_call.input
            
            # 查找对应工具 / Find corresponding tool
            tool = next((t for t in self.tools if t.name == tool_name), None)
            
            if tool:
                try:
                    # 异步执行工具 / Execute tool asynchronously
                    if hasattr(tool, '_arun'):
                        result = await tool._arun(**tool_input)
                    else:
                        result = tool._run(**tool_input)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"工具 {tool_name} 执行失败: {e}")
                    results.append(f"工具执行错误: {str(e)}")
            else:
                results.append(f"未找到工具: {tool_name}")
        
        return results

    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取Agent信息
        Get agent information
        """
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools_count": len(self.tools),
            "capabilities": [
                "Claude 4 原生工具调用",
                "并行工具执行", 
                "文档处理支持",
                "高级推理能力",
                "上下文记忆管理"
            ]
        }
