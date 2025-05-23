"""
统一异常处理模块
Unified exception handling module for JobCatcher
"""

import logging
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR


class JobCatcherException(Exception):
    """
    JobCatcher 自定义异常基类
    Base class for JobCatcher custom exceptions
    """
    def __init__(
        self, 
        message: str, 
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        details: Union[str, dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(JobCatcherException):
    """
    认证异常
    Authentication exception
    """
    def __init__(self, message: str = "认证失败 / Authentication failed", details: Union[str, dict] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(JobCatcherException):
    """
    授权异常
    Authorization exception
    """
    def __init__(self, message: str = "权限不足 / Insufficient permissions", details: Union[str, dict] = None):
        super().__init__(message, status_code=403, details=details)


class ResourceNotFoundError(JobCatcherException):
    """
    资源未找到异常
    Resource not found exception
    """
    def __init__(self, message: str = "资源未找到 / Resource not found", details: Union[str, dict] = None):
        super().__init__(message, status_code=404, details=details)


class ValidationError(JobCatcherException):
    """
    数据验证异常
    Data validation exception
    """
    def __init__(self, message: str = "数据验证失败 / Data validation failed", details: Union[str, dict] = None):
        super().__init__(message, status_code=HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class ExternalServiceError(JobCatcherException):
    """
    外部服务异常
    External service exception
    """
    def __init__(self, message: str = "外部服务错误 / External service error", details: Union[str, dict] = None):
        super().__init__(message, status_code=502, details=details)


class RateLimitError(JobCatcherException):
    """
    频率限制异常
    Rate limit exception
    """
    def __init__(self, message: str = "请求频率过高 / Rate limit exceeded", details: Union[str, dict] = None):
        super().__init__(message, status_code=429, details=details)


# 异常处理器函数
# Exception handler functions

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    HTTP exception handler
    """
    logging.warning(f"HTTP异常 / HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器
    Request validation exception handler
    """
    logging.warning(f"验证异常 / Validation Exception: {exc.errors()}")
    
    # 格式化验证错误信息
    # Format validation error messages
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "请求数据验证失败 / Request data validation failed",
            "status_code": HTTP_422_UNPROCESSABLE_ENTITY,
            "details": errors,
            "path": str(request.url),
            "method": request.method
        }
    )


async def jobcatcher_exception_handler(request: Request, exc: JobCatcherException) -> JSONResponse:
    """
    JobCatcher 自定义异常处理器
    JobCatcher custom exception handler
    """
    logging.error(f"JobCatcher异常 / JobCatcher Exception: {exc.status_code} - {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器
    General exception handler
    """
    logging.error(f"未处理的异常 / Unhandled Exception: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    # 在开发环境下显示详细错误信息
    # Show detailed error information in development environment
    from app.core.config import settings
    
    response_content = {
        "error": True,
        "message": "服务器内部错误 / Internal server error",
        "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
        "path": str(request.url),
        "method": request.method
    }
    
    if settings.is_development:
        response_content["details"] = {
            "type": type(exc).__name__,
            "description": str(exc)
        }
    
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_content
    ) 