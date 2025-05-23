"""
JobCatcher 主应用入口
FastAPI application entry point for JobCatcher job assistant platform
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 导入核心配置
# Import core configuration
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# 导入API路由
# Import API routes
from app.api import api_router


# 应用生命周期管理
# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用启动和关闭时的生命周期管理
    Application startup and shutdown lifecycle management
    """
    # 启动时执行 - Startup tasks
    logging.info("🚀 JobCatcher 应用启动中... / Starting JobCatcher application...")
    
    # 初始化数据库
    # Initialize database
    try:
        await init_db()
        logging.info("✅ 数据库初始化完成 / Database initialized successfully")
    except Exception as e:
        logging.error(f"❌ 数据库初始化失败 / Database initialization failed: {e}")
        raise
    
    logging.info("🎉 JobCatcher 应用启动完成! / JobCatcher application started successfully!")
    
    yield
    
    # 关闭时执行 - Shutdown tasks
    logging.info("⏹️ JobCatcher 应用关闭中... / Shutting down JobCatcher application...")
    logging.info("👋 JobCatcher 应用已关闭 / JobCatcher application shutdown complete")


# 创建FastAPI应用实例
# Create FastAPI application instance
app = FastAPI(
    title="JobCatcher API",
    description="智能求职辅助平台 - AI-powered job search assistant platform",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/api/openapi.json" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# 配置CORS中间件
# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 异常处理器注册
# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# API路由注册
# Register API routes
app.include_router(api_router, prefix="/api/v1")

# 静态文件服务 (生产环境前端文件)
# Static files serving (production frontend files)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logging.info(f"📁 静态文件目录已挂载 / Static files mounted: {static_dir}")


# 健康检查端点
# Health check endpoint
@app.get("/health", tags=["系统 / System"])
async def health_check():
    """
    健康检查端点，用于监控服务状态
    Health check endpoint for service monitoring
    """
    return {
        "status": "healthy",
        "message": "JobCatcher 服务运行正常 / JobCatcher service is running normally",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# 根路径处理 (SPA支持)
# Root path handler (SPA support)
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_frontend():
    """
    为单页应用提供前端文件服务
    Serve frontend files for Single Page Application
    """
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        # 开发环境下的简单欢迎页面
        # Simple welcome page for development environment
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>JobCatcher - 智能求职辅助平台</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .logo { font-size: 3em; color: #2c3e50; margin-bottom: 20px; }
                .subtitle { font-size: 1.2em; color: #7f8c8d; margin-bottom: 30px; }
                .api-link { 
                    display: inline-block; 
                    padding: 10px 20px; 
                    background: #3498db; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 10px;
                }
                .feature-list {
                    max-width: 800px;
                    margin: 30px auto;
                    text-align: left;
                }
                .feature-item {
                    padding: 15px;
                    margin: 10px 0;
                    background: #ecf0f1;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                }
            </style>
        </head>
        <body>
            <div class="logo">🎯 JobCatcher</div>
            <div class="subtitle">智能求职辅助平台 - AI-powered Job Search Assistant</div>
            
            <div class="feature-list">
                <div class="feature-item">
                    <strong>🔍 智能职位搜索</strong> - 多数据源聚合，AI驱动的职位匹配
                </div>
                <div class="feature-item">
                    <strong>📄 简历智能分析</strong> - 深度分析简历质量和职位匹配度
                </div>
                <div class="feature-item">
                    <strong>📊 技能热点图</strong> - 分析技能市场需求趋势
                </div>
                <div class="feature-item">
                    <strong>✨ 简历智能优化</strong> - AI辅助简历改写和优化
                </div>
                <div class="feature-item">
                    <strong>💬 智能聊天助手</strong> - 实时WebSocket支持，多Agent协作
                </div>
            </div>
            
            <div>
                <a href="/api/docs" class="api-link">📖 API 文档 / API Docs</a>
                <a href="/health" class="api-link">💚 健康检查 / Health Check</a>
                <a href="/api/v1/agents/capabilities" class="api-link">🤖 Agent 能力 / Agent Capabilities</a>
            </div>
        </body>
        </html>
        """)


# SPA路由支持 - 捕获所有未匹配的路径
# SPA routing support - catch all unmatched paths
@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
async def serve_spa(request: Request, full_path: str):
    """
    为SPA路由提供回退支持
    Fallback support for SPA routing
    """
    # 如果是API路径，返回404
    # If it's an API path, return 404
    if full_path.startswith("api/"):
        return HTMLResponse(content="API endpoint not found", status_code=404)
    
    # 对于其他路径，返回前端应用
    # For other paths, return frontend application
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return HTMLResponse(content="Page not found", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    ) 