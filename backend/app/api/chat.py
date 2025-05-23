"""
聊天对话API路由
Chat API routes for JobCatcher with WebSocket support
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_async_session
from app.models.user import User
from app.models.chat_history import ChatHistory, MessageRole, MessageType
from app.api.auth import get_current_user
from app.agents.coordinator import AgentCoordinator, WorkflowType

router = APIRouter()
logger = logging.getLogger("api.chat")

# WebSocket连接管理器
# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"用户 {user_id} WebSocket连接已建立 / User {user_id} WebSocket connected")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"用户 {user_id} WebSocket连接已断开 / User {user_id} WebSocket disconnected")
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(json.dumps(message, ensure_ascii=False))


manager = ConnectionManager()
coordinator = AgentCoordinator()


class ChatMessage(BaseModel):
    """
    聊天消息模型
    Chat message model
    """
    content: str
    message_type: MessageType = MessageType.TEXT
    context_data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """
    聊天响应模型
    Chat response model
    """
    message_id: int
    content: str
    role: MessageRole
    message_type: MessageType
    timestamp: datetime
    context_data: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    """
    聊天会话响应模型
    Chat session response model
    """
    session_id: str
    user_id: int
    created_at: datetime
    message_count: int
    last_message_at: Optional[datetime]


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket聊天连接端点
    WebSocket chat connection endpoint
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 接收用户消息
            # Receive user message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 处理消息
            # Process message
            await handle_websocket_message(user_id, message_data, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"用户 {user_id} WebSocket连接断开 / User {user_id} WebSocket disconnected")


async def handle_websocket_message(user_id: str, message_data: dict, websocket: WebSocket):
    """
    处理WebSocket消息
    Handle WebSocket message
    """
    try:
        # 解析消息
        # Parse message
        content = message_data.get("content", "")
        message_type = message_data.get("type", "text")
        context_data = message_data.get("context", {})
        session_id = message_data.get("session_id")
        
        # 保存用户消息到数据库
        # Save user message to database
        async with get_async_session() as db:
            chat_history = ChatHistory(
                user_id=int(user_id),
                session_id=session_id,
                role=MessageRole.USER,
                content=content,
                message_type=MessageType(message_type),
                context_data=context_data
            )
            db.add(chat_history)
            await db.commit()
            await db.refresh(chat_history)
        
        # 发送确认消息
        # Send confirmation message
        await manager.send_personal_message({
            "type": "message_received",
            "message_id": chat_history.id,
            "timestamp": chat_history.created_at.isoformat()
        }, user_id)
        
        # 根据消息类型处理
        # Process based on message type
        if message_type == "agent_request":
            await handle_agent_request(user_id, content, context_data, session_id)
        elif message_type == "workflow_request":
            await handle_workflow_request(user_id, context_data, session_id)
        else:
            # 普通聊天消息
            await handle_chat_message(user_id, content, session_id)
            
    except Exception as e:
        logger.error(f"处理WebSocket消息失败 / Failed to handle WebSocket message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"消息处理失败 / Message processing failed: {str(e)}"
        }, user_id)


async def handle_agent_request(user_id: str, content: str, context_data: dict, session_id: str):
    """
    处理Agent请求
    Handle agent request
    """
    try:
        # 确定要调用的Agent类型
        # Determine agent type to invoke
        agent_type = context_data.get("agent_type", "job_search")
        
        workflow_map = {
            "job_search": WorkflowType.JOB_SEARCH,
            "resume_analysis": WorkflowType.RESUME_ANALYSIS,
            "skill_analysis": WorkflowType.SKILL_ANALYSIS,
            "resume_optimization": WorkflowType.RESUME_OPTIMIZATION,
            "comprehensive": WorkflowType.COMPREHENSIVE
        }
        
        workflow_type = workflow_map.get(agent_type, WorkflowType.JOB_SEARCH)
        
        # 发送处理中状态
        # Send processing status
        await manager.send_personal_message({
            "type": "agent_processing",
            "agent_type": agent_type,
            "message": f"正在调用 {agent_type} Agent处理您的请求... / Invoking {agent_type} Agent to process your request..."
        }, user_id)
        
        # 执行Agent工作流
        # Execute agent workflow
        result = await coordinator.execute_workflow(
            workflow_type=workflow_type,
            user_input={
                "user_message": content,
                **context_data
            },
            user_id=int(user_id),
            session_id=session_id
        )
        
        # 保存Agent响应
        # Save agent response
        async with get_async_session() as db:
            agent_response = ChatHistory(
                user_id=int(user_id),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=json.dumps(result, ensure_ascii=False),
                message_type=MessageType.AGENT_RESPONSE,
                context_data={
                    "agent_type": agent_type,
                    "workflow_type": str(workflow_type),
                    "execution_report": result.get("execution_report")
                }
            )
            db.add(agent_response)
            await db.commit()
        
        # 发送Agent响应结果
        # Send agent response result
        await manager.send_personal_message({
            "type": "agent_response",
            "agent_type": agent_type,
            "success": result.get("success", False),
            "result": result.get("execution_report", {}),
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat()
        }, user_id)
        
    except Exception as e:
        logger.error(f"处理Agent请求失败 / Failed to handle agent request: {e}")
        await manager.send_personal_message({
            "type": "agent_error",
            "message": f"Agent处理失败 / Agent processing failed: {str(e)}"
        }, user_id)


async def handle_workflow_request(user_id: str, context_data: dict, session_id: str):
    """
    处理工作流请求
    Handle workflow request
    """
    try:
        workflow_type = WorkflowType(context_data.get("workflow_type", "job_search"))
        user_input = context_data.get("user_input", {})
        
        # 发送工作流开始状态
        # Send workflow start status
        await manager.send_personal_message({
            "type": "workflow_started",
            "workflow_type": str(workflow_type),
            "session_id": session_id
        }, user_id)
        
        # 执行工作流
        # Execute workflow
        result = await coordinator.execute_workflow(
            workflow_type=workflow_type,
            user_input=user_input,
            user_id=int(user_id),
            session_id=session_id
        )
        
        # 发送工作流完成状态
        # Send workflow completion status
        await manager.send_personal_message({
            "type": "workflow_completed",
            "workflow_type": str(workflow_type),
            "session_id": session_id,
            "success": result.get("success", False),
            "result": result.get("execution_report", {}),
            "error": result.get("error")
        }, user_id)
        
    except Exception as e:
        logger.error(f"处理工作流请求失败 / Failed to handle workflow request: {e}")
        await manager.send_personal_message({
            "type": "workflow_error",
            "message": f"工作流执行失败 / Workflow execution failed: {str(e)}"
        }, user_id)


async def handle_chat_message(user_id: str, content: str, session_id: str):
    """
    处理普通聊天消息
    Handle regular chat message
    """
    try:
        # 这里可以集成简单的聊天AI或规则引擎
        # Here can integrate simple chat AI or rule engine
        
        # 简单的响应逻辑
        # Simple response logic
        response_content = f"您好！我是JobCatcher AI助手。您说：'{content}'。我能帮您进行职位搜索、简历分析、技能评估和简历优化。请告诉我您需要什么帮助！"
        
        # 保存助手响应
        # Save assistant response
        async with get_async_session() as db:
            assistant_response = ChatHistory(
                user_id=int(user_id),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=response_content,
                message_type=MessageType.TEXT
            )
            db.add(assistant_response)
            await db.commit()
        
        # 发送响应
        # Send response
        await manager.send_personal_message({
            "type": "chat_response",
            "content": response_content,
            "timestamp": datetime.now().isoformat()
        }, user_id)
        
    except Exception as e:
        logger.error(f"处理聊天消息失败 / Failed to handle chat message: {e}")


@router.post("/send", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    发送聊天消息 (HTTP API)
    Send chat message (HTTP API)
    """
    try:
        # 保存用户消息
        # Save user message
        chat_history = ChatHistory(
            user_id=current_user.id,
            session_id=session_id,
            role=MessageRole.USER,
            content=message.content,
            message_type=message.message_type,
            context_data=message.context_data
        )
        db.add(chat_history)
        await db.commit()
        await db.refresh(chat_history)
        
        return ChatResponse(
            message_id=chat_history.id,
            content=chat_history.content,
            role=chat_history.role,
            message_type=chat_history.message_type,
            timestamp=chat_history.created_at,
            context_data=chat_history.context_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败 / Failed to send message: {str(e)}"
        )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取聊天历史
    Get chat history
    """
    try:
        # 查询聊天历史
        # Query chat history
        from sqlalchemy import select, desc
        
        query = (
            select(ChatHistory)
            .where(
                ChatHistory.user_id == current_user.id,
                ChatHistory.session_id == session_id
            )
            .order_by(desc(ChatHistory.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        chat_messages = result.scalars().all()
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": [
                ChatResponse(
                    message_id=msg.id,
                    content=msg.content,
                    role=msg.role,
                    message_type=msg.message_type,
                    timestamp=msg.created_at,
                    context_data=msg.context_data
                )
                for msg in reversed(chat_messages)
            ],
            "total_messages": len(chat_messages),
            "has_more": len(chat_messages) == limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取聊天历史失败 / Failed to get chat history: {str(e)}"
        )


@router.get("/sessions")
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取用户的聊天会话列表
    Get user's chat sessions
    """
    try:
        from sqlalchemy import select, func, desc
        
        # 查询会话信息
        # Query session information
        query = (
            select(
                ChatHistory.session_id,
                func.count(ChatHistory.id).label("message_count"),
                func.min(ChatHistory.created_at).label("created_at"),
                func.max(ChatHistory.created_at).label("last_message_at")
            )
            .where(ChatHistory.user_id == current_user.id)
            .group_by(ChatHistory.session_id)
            .order_by(desc("last_message_at"))
        )
        
        result = await db.execute(query)
        sessions = result.all()
        
        return {
            "success": True,
            "sessions": [
                ChatSessionResponse(
                    session_id=session.session_id,
                    user_id=current_user.id,
                    created_at=session.created_at,
                    message_count=session.message_count,
                    last_message_at=session.last_message_at
                )
                for session in sessions
            ],
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取聊天会话失败 / Failed to get chat sessions: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    删除聊天会话
    Delete chat session
    """
    try:
        from sqlalchemy import delete
        
        # 删除会话中的所有消息
        # Delete all messages in session
        query = delete(ChatHistory).where(
            ChatHistory.user_id == current_user.id,
            ChatHistory.session_id == session_id
        )
        
        result = await db.execute(query)
        await db.commit()
        
        return {
            "success": True,
            "session_id": session_id,
            "deleted_messages": result.rowcount,
            "message": f"会话 {session_id} 已删除 / Session {session_id} deleted"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除聊天会话失败 / Failed to delete chat session: {str(e)}"
        ) 