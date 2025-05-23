"""
数据库连接和会话管理
Database connection and session management for JobCatcher
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from app.core.config import settings


# 数据库元数据配置
# Database metadata configuration
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)


# SQLAlchemy 基础模型类
# SQLAlchemy base model class
class Base(DeclarativeBase):
    """
    所有ORM模型的基类
    Base class for all ORM models
    """
    metadata = metadata


# 创建异步数据库引擎
# Create async database engine
def create_database_engine():
    """
    创建数据库引擎实例
    Create database engine instance
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        # 连接池配置 - Connection pool configuration
        pool_pre_ping=True,  # 验证连接是否有效 / Validate connections
        pool_recycle=3600,   # 连接回收时间 / Connection recycle time
        echo=settings.is_development,  # 开发环境下显示SQL / Show SQL in development
        # 异步连接配置 - Async connection configuration
        future=True
    )
    return engine


# 全局数据库引擎实例
# Global database engine instance
engine = create_database_engine()

# 创建异步会话工厂
# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数
    Dependency injection function for database session
    
    Yields:
        AsyncSession: 异步数据库会话 / Async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logging.error(f"数据库会话错误 / Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# 别名函数，保持API兼容性
# Alias function for API compatibility
get_async_session = get_database_session


async def init_db() -> None:
    """
    初始化数据库，创建所有表
    Initialize database and create all tables
    """
    try:
        # 导入所有模型以确保它们被注册
        # Import all models to ensure they are registered
        from app.models import user, job, resume, chat_history
        
        async with engine.begin() as conn:
            # 创建所有表 - Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logging.info("✅ 数据库表初始化完成 / Database tables initialized successfully")
        
    except Exception as e:
        logging.error(f"❌ 数据库初始化失败 / Database initialization failed: {e}")
        raise


async def close_db() -> None:
    """
    关闭数据库连接
    Close database connections
    """
    try:
        await engine.dispose()
        logging.info("✅ 数据库连接已关闭 / Database connections closed")
    except Exception as e:
        logging.error(f"❌ 关闭数据库连接失败 / Failed to close database connections: {e}")
        raise 