"""
Azure AI Search服务 - JobCatcher RAG检索系统
Azure AI Search service - JobCatcher RAG retrieval system
基于开发文档要求实现职位数据向量化和语义检索
Implementing job data vectorization and semantic retrieval as per development documentation
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.core.credentials import AzureKeyCredential
from langchain_core.tools import BaseTool
from langchain_openai import AzureOpenAIEmbeddings
from pydantic import BaseModel, Field

from app.core.config import settings


class JobDocument(BaseModel):
    """
    职位文档模型 - 用于Azure AI Search索引
    Job document model for Azure AI Search indexing
    """
    id: str = Field(..., description="职位唯一标识符")
    title: str = Field(..., description="职位标题")
    company: str = Field(..., description="公司名称")
    location: str = Field(..., description="工作地点")
    salary: Optional[str] = Field(None, description="薪资范围")
    description: str = Field(..., description="职位描述")
    skills: List[str] = Field(default_factory=list, description="技能要求")
    source: str = Field(..., description="数据来源：stepstone/google/jobspikr/coresignal")
    url: str = Field(..., description="原始链接")
    indexed_at: datetime = Field(default_factory=datetime.utcnow, description="索引时间")
    expired: bool = Field(default=False, description="是否过期")


class JobSearchTool(BaseTool):
    """
    职位搜索工具 - 供Claude 4使用的RAG检索工具
    Job search tool - RAG retrieval tool for Claude 4 to use
    """
    
    name: str = "query_local_jobs"
    description: str = """
    搜索本地职位数据库。使用语义搜索找到与查询最相关的职位。
    Search local job database. Use semantic search to find jobs most relevant to the query.
    Args:
        query: 搜索查询，可以是职位名称、技能或描述
        top_k: 返回结果数量，默认10条
    """
    
    search_service: 'AzureSearchService'
    
    def _run(self, query: str, top_k: int = 10) -> str:
        """同步运行搜索"""
        # 在实际实现中，这应该调用异步方法
        # In actual implementation, this should call async method
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(self._arun(query, top_k))
        return result
    
    async def _arun(self, query: str, top_k: int = 10) -> str:
        """异步搜索职位"""
        try:
            jobs = await self.search_service.search_jobs(query, top_k)
            
            if not jobs:
                return "未找到相关职位。建议扩大搜索范围或调整关键词。"
            
            # 格式化搜索结果供Claude 4分析
            # Format search results for Claude 4 analysis
            results = []
            for job in jobs:
                results.append({
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "salary": job.get("salary", ""),
                    "source": job.get("source", ""),
                    "skills": job.get("skills", []),
                    "description_preview": job.get("description", "")[:200] + "..." if len(job.get("description", "")) > 200 else job.get("description", ""),
                    "url": job.get("url", ""),
                    "relevance_score": job.get("@search.score", 0)
                })
            
            return json.dumps(results, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"搜索时发生错误：{str(e)}"


class AzureSearchService:
    """
    Azure AI Search服务类 - 实现RAG检索核心功能
    Azure AI Search service class - implementing core RAG retrieval functionality
    """
    
    def __init__(self):
        """
        初始化Azure AI Search客户端
        Initialize Azure AI Search client
        """
        self.logger = logging.getLogger("azure_search")
        
        # 验证配置 - Validate configuration
        if not settings.AZURE_SEARCH_ENDPOINT or not settings.AZURE_SEARCH_KEY:
            raise ValueError("Azure Search endpoint 和 key 必须在环境变量中配置")
        
        # 初始化客户端 - Initialize clients
        credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        self.search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name="jobs-index",  # 根据开发文档配置
            credential=credential
        )
        self.index_client = SearchIndexClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            credential=credential
        )
        
        # 初始化嵌入模型 - Initialize embedding model
        self.embeddings = AzureOpenAIEmbeddings(
            model="text-embedding-ada-002",  # 使用Azure OpenAI嵌入模型
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version="2024-02-01"
        )
        
        self.index_name = "jobs-index"
    
    async def ensure_index_exists(self) -> None:
        """
        确保搜索索引存在，如不存在则创建
        Ensure search index exists, create if not exists
        """
        try:
            # 检查索引是否存在 - Check if index exists
            try:
                await self.index_client.get_index(self.index_name)
                self.logger.info(f"Azure Search索引 '{self.index_name}' 已存在")
                return
            except Exception:
                self.logger.info(f"创建新的Azure Search索引: {self.index_name}")
            
            # 创建索引配置 - Create index configuration
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
                SearchableField(name="company", type=SearchFieldDataType.String),
                SearchableField(name="location", type=SearchFieldDataType.String),
                SimpleField(name="salary", type=SearchFieldDataType.String, facetable=True),
                SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
                SimpleField(name="skills", type=SearchFieldDataType.Collection(SearchFieldDataType.String), facetable=True),
                SimpleField(name="source", type=SearchFieldDataType.String, facetable=True),
                SimpleField(name="url", type=SearchFieldDataType.String),
                SimpleField(name="indexed_at", type=SearchFieldDataType.DateTimeOffset),
                SimpleField(name="expired", type=SearchFieldDataType.Boolean, facetable=True),
                
                # 向量字段 - Vector field for semantic search
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,  # 基于text-embedding-3-small模型维度
                    vector_search_profile_name="jobs-profile"
                )
            ]
            
            # 向量搜索配置 - Vector search configuration
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="jobs-profile",
                        algorithm_configuration_name="jobs-hnsw"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="jobs-hnsw",
                        parameters={
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    )
                ]
            )
            
            # 创建索引 - Create index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            await self.index_client.create_index(index)
            self.logger.info(f"成功创建Azure Search索引: {self.index_name}")
            
        except Exception as e:
            self.logger.error(f"创建Azure Search索引失败: {e}")
            raise
    
    async def index_job(self, job: JobDocument) -> bool:
        """
        将单个职位文档索引到Azure AI Search
        Index a single job document to Azure AI Search
        """
        try:
            # 生成内容向量 - Generate content vector
            content_text = f"{job.title} {job.company} {job.description} {' '.join(job.skills)}"
            content_vector = await self.embeddings.aembed_query(content_text)
            
            # 构建文档 - Build document
            doc = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary": job.salary,
                "description": job.description,
                "skills": job.skills,
                "source": job.source,
                "url": job.url,
                "indexed_at": job.indexed_at.isoformat(),
                "expired": job.expired,
                "content_vector": content_vector
            }
            
            # 上传文档 - Upload document
            result = await self.search_client.upload_documents([doc])
            
            if result[0].succeeded:
                self.logger.debug(f"成功索引职位: {job.id} - {job.title}")
                return True
            else:
                self.logger.error(f"索引职位失败: {job.id} - {result[0].error_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"索引职位 {job.id} 时发生错误: {e}")
            return False
    
    async def index_jobs_batch(self, jobs: List[JobDocument]) -> int:
        """
        批量索引职位文档
        Batch index job documents
        """
        success_count = 0
        for job in jobs:
            if await self.index_job(job):
                success_count += 1
        
        self.logger.info(f"批量索引完成: {success_count}/{len(jobs)} 成功")
        return success_count
    
    async def search_jobs(
        self, 
        query: str, 
        top_k: int = 10,
        filters: Optional[str] = None,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        使用语义搜索查找相关职位
        Use semantic search to find relevant jobs
        """
        try:
            # 生成查询向量 - Generate query vector
            query_vector = await self.embeddings.aembed_query(query)
            
            # 构建向量查询 - Build vector query
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            # 构建过滤条件 - Build filter conditions
            filter_expression = "expired eq false" if not include_expired else None
            if filters:
                if filter_expression:
                    filter_expression += f" and {filters}"
                else:
                    filter_expression = filters
            
            # 执行搜索 - Execute search
            results = await self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=filter_expression,
                top=top_k,
                include_total_count=True
            )
            
            # 处理结果 - Process results
            jobs = []
            async for result in results:
                jobs.append(dict(result))
            
            self.logger.info(f"搜索查询 '{query}' 返回 {len(jobs)} 个结果")
            return jobs
            
        except Exception as e:
            self.logger.error(f"搜索查询 '{query}' 失败: {e}")
            return []
    
    async def delete_expired_jobs(self) -> int:
        """
        删除过期的职位记录
        Delete expired job records
        """
        try:
            # 搜索过期职位 - Search for expired jobs
            results = await self.search_client.search(
                search_text="*",
                filter="expired eq true",
                select=["id"]
            )
            
            # 收集要删除的ID - Collect IDs to delete
            ids_to_delete = []
            async for result in results:
                ids_to_delete.append({"id": result["id"]})
            
            if not ids_to_delete:
                return 0
            
            # 执行删除 - Execute deletion
            delete_results = await self.search_client.delete_documents(ids_to_delete)
            
            success_count = sum(1 for result in delete_results if result.succeeded)
            self.logger.info(f"删除过期职位: {success_count}/{len(ids_to_delete)} 成功")
            
            return success_count
            
        except Exception as e:
            self.logger.error(f"删除过期职位失败: {e}")
            return 0
    
    def get_search_tool(self) -> JobSearchTool:
        """
        获取供Claude 4使用的搜索工具
        Get search tool for Claude 4 to use
        """
        return JobSearchTool(search_service=self)


# 全局服务实例 - Global service instance
search_service = None


async def get_search_service() -> AzureSearchService:
    """
    获取Azure Search服务实例 - 依赖注入
    Get Azure Search service instance - dependency injection
    """
    global search_service
    if search_service is None:
        search_service = AzureSearchService()
        await search_service.ensure_index_exists()
    return search_service 