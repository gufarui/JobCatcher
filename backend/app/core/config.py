"""
JobCatcher 应用配置
Application configuration for JobCatcher
"""

import os
from typing import List, Optional, Union
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类，使用Pydantic管理环境变量
    Application settings class using Pydantic for environment variable management
    """
    
    # ==============================================
    # 基础应用配置 - Basic Application Settings
    # ==============================================
    ENVIRONMENT: str = Field(default="development", description="应用运行环境 / Application environment")
    APP_DOMAIN: str = Field(default="localhost:8000", description="应用域名 / Application domain")
    LOG_LEVEL: str = Field(default="INFO", description="日志级别 / Log level")
    
    # CORS配置 - CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="允许的跨域源 / Allowed CORS origins"
    )
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """
        解析CORS_ORIGINS，支持字符串和列表格式
        Parse CORS_ORIGINS to support both string and list formats
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ==============================================
    # LLM配置 - Language Model Configuration
    # ==============================================
    ANTHROPIC_API_KEY: str = Field(
        default="demo_key", 
        description="Anthropic Claude 4 API密钥 / Anthropic Claude 4 API key"
    )
    
    ANTHROPIC_BASE_URL: str = Field(
        default="https://claude.cloudapi.vip",
        description="Anthropic API基础URL / Anthropic API base URL"
    )
    
    CLAUDE_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Claude模型温度设置 (0.0-1.0) / Claude model temperature setting"
    )
    
    # ==============================================
    # 职位数据源配置 - Job Data Source Configuration
    # ==============================================
    APIFY_TOKEN: str = Field(
        default="demo_token", 
        description="Apify StepStone爬虫令牌 / Apify StepStone scraper token"
    )
    
    SERPAPI_KEY: str = Field(
        default="demo_key", 
        description="SerpAPI Google Jobs密钥 / SerpAPI Google Jobs key"
    )
    
    JOBSPIKR_KEY: Optional[str] = Field(
        default=None, 
        description="JobsPikr API密钥 / JobsPikr API key"
    )
    
    CORESIGNAL_KEY: Optional[str] = Field(
        default=None, 
        description="CoreSignal API密钥 / CoreSignal API key"
    )
    
    # ==============================================
    # 简历处理和PDF服务配置 - Resume & PDF Service Configuration
    # ==============================================
    APILAYER_RESUME_KEY: str = Field(
        default="demo_key", 
        description="APILayer简历解析器密钥 / APILayer resume parser key"
    )
    
    PDFMONKEY_KEY: str = Field(
        default="demo_key", 
        description="PDFMonkey PDF生成服务密钥 / PDFMonkey PDF generation service key"
    )
    
    PDFMONKEY_BASE_URL: str = Field(
        default="https://api.pdfmonkey.io/api/v1",
        description="PDFMonkey API基础URL / PDFMonkey API base URL"
    )
    
    # ==============================================
    # Azure云服务配置 - Azure Cloud Service Configuration
    # ==============================================
    
    # Azure OpenAI配置 - Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = Field(
        default="https://demo.openai.azure.com", 
        description="Azure OpenAI端点 / Azure OpenAI endpoint"
    )
    
    AZURE_OPENAI_API_KEY: str = Field(
        default="demo_key", 
        description="Azure OpenAI API密钥 / Azure OpenAI API key"
    )
    
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-02-01", 
        description="Azure OpenAI API版本 / Azure OpenAI API version"
    )
    
    # Azure AI Search配置 - Azure AI Search Configuration
    AZURE_SEARCH_ENDPOINT: str = Field(
        default="https://demo.search.windows.net", 
        description="Azure AI Search端点 / Azure AI Search endpoint"
    )
    
    AZURE_SEARCH_KEY: str = Field(
        default="demo_key", 
        description="Azure AI Search密钥 / Azure AI Search key"
    )
    
    AZURE_SEARCH_INDEX_NAME: str = Field(
        default="jobs-index", 
        description="Azure搜索索引名称 / Azure search index name"
    )
    
    # Azure Blob Storage配置 - Azure Blob Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: str = Field(
        default="DefaultEndpointsProtocol=https;AccountName=demo;AccountKey=demo;EndpointSuffix=core.windows.net", 
        description="Azure Blob存储连接字符串 / Azure Blob Storage connection string"
    )
    
    # ==============================================
    # 数据库配置 - Database Configuration
    # ==============================================
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./jobcatcher.db", 
        description="数据库URL / Database URL"
    )
    
    # ==============================================
    # OAuth认证配置 - OAuth Authentication Configuration
    # ==============================================
    GOOGLE_CLIENT_ID: str = Field(
        default="demo_client_id", 
        description="Google OAuth客户端ID / Google OAuth client ID"
    )
    
    GOOGLE_CLIENT_SECRET: str = Field(
        default="demo_client_secret", 
        description="Google OAuth客户端密钥 / Google OAuth client secret"
    )
    
    # JWT认证配置 - JWT Authentication Configuration
    SECRET_KEY: str = Field(
        default="your_secret_key_here_change_this_in_production_it_must_be_very_long_and_random", 
        description="JWT令牌加密密钥 / JWT token encryption secret key"
    )
    
    ALGORITHM: str = Field(
        default="HS256", 
        description="JWT签名算法 / JWT signing algorithm"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,  # 24小时 / 24 hours
        description="访问令牌过期时间(分钟) / Access token expiration time in minutes"
    )
    
    SESSION_SECRET: str = Field(
        default="your_session_secret_here_change_this_in_production", 
        description="会话密钥 / Session secret key"
    )
    
    # ==============================================
    # 可选服务配置 - Optional Service Configuration
    # ==============================================
    REDIS_URL: Optional[str] = Field(
        default=None, 
        description="Redis缓存URL / Redis cache URL"
    )
    
    SENTRY_DSN: Optional[str] = Field(
        default=None, 
        description="Sentry错误监控DSN / Sentry error monitoring DSN"
    )
    
    # LangSmith配置 - LangSmith Configuration
    LANGSMITH_TRACING: bool = Field(
        default=False, 
        description="是否启用LangSmith追踪 / Enable LangSmith tracing"
    )
    
    LANGSMITH_API_KEY: Optional[str] = Field(
        default=None, 
        description="LangSmith API密钥 / LangSmith API key"
    )
    
    LANGSMITH_PROJECT: str = Field(
        default="jobcatcher", 
        description="LangSmith项目名称 / LangSmith project name"
    )
    
    # ==============================================
    # 计算属性 - Computed Properties
    # ==============================================
    @property
    def is_development(self) -> bool:
        """
        检查是否为开发环境
        Check if running in development environment
        """
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """
        检查是否为生产环境
        Check if running in production environment
        """
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def database_url_sync(self) -> str:
        """
        同步数据库URL (用于Alembic等工具)
        Sync database URL (for tools like Alembic)
        """
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        将CORS_ORIGINS转换为列表格式
        Convert CORS_ORIGINS to list format
        """
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    class Config:
        """Pydantic配置 / Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # 允许从字符串解析复杂类型
        # Allow parsing complex types from strings
        json_encoders = {
            # 列表类型的环境变量支持逗号分隔
            # Support comma-separated values for list types
        }


# 创建全局设置实例
# Create global settings instance
settings = Settings()

# 配置LangSmith (如果启用)
# Configure LangSmith (if enabled)
if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT

# 配置Sentry (如果提供DSN)
# Configure Sentry (if DSN provided)
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1 if settings.is_production else 1.0,
        environment=settings.ENVIRONMENT,
    ) 