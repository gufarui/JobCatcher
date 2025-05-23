"""
JobSearchAgent - 职位搜索Agent
JobSearchAgent - Job search agent using Claude 4 and external APIs
根据开发文档第5节要求实现多源职位搜索和聚合
Implementing multi-source job search and aggregation as per section 5 of development documentation
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

import httpx
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.services.azure_search import get_search_service, JobDocument
from app.core.config import settings


class WebSearchInput(BaseModel):
    """Web搜索工具输入参数模型"""
    query: str = Field(description="搜索关键词，如'python developer'或'data scientist'")
    location: str = Field(default="Berlin", description="工作地点，如'Berlin'、'Munich'或'Remote'")
    limit: int = Field(default=20, description="返回结果数量，默认20，最大50")


class LocalJobSearchInput(BaseModel):
    """本地职位搜索工具输入参数模型"""
    search_text: str = Field(description="搜索文本，支持职位标题、技能、公司名")
    top: int = Field(default=10, description="返回结果数量，默认10")


class WebSearchTool(BaseTool):
    """
    增强的网络搜索工具 - 整合多个数据源
    Enhanced web search tool - integrates multiple data sources
    """
    
    name: str = "web_search_20250305"
    description: str = """
    使用外部API搜索最新职位信息。整合StepStone、Google Jobs等多个数据源。
    返回JSON格式的职位列表，包含标题、公司、地点、薪资等信息。
    Search for latest job information using external APIs. Integrates StepStone, Google Jobs and other sources.
    Returns JSON formatted job list with title, company, location, salary and other details.
    """
    args_schema: type[WebSearchInput] = WebSearchInput
    
    def _run(self, query: str, location: str = "Berlin", limit: int = 20) -> str:
        """同步搜索包装器"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._arun(query, location, limit))
    
    async def _arun(self, query: str, location: str = "Berlin", limit: int = 20) -> str:
        """
        异步搜索外部API - 并行调用提高效率
        Asynchronous external API search - parallel calls for efficiency
        """
        results = []
        
        # 并行调用多个数据源 / Parallel calls to multiple data sources
        tasks = []
        
        # 1. StepStone via Apify
        if settings.APIFY_TOKEN:
            tasks.append(self._search_stepstone(query, location, limit // 2))
        
        # 2. Google Jobs via SerpAPI
        if settings.SERPAPI_KEY:
            tasks.append(self._search_google_jobs(query, location, limit // 2))
        
        if not tasks:
            return json.dumps({
                "status": "error",
                "message": "未配置外部API密钥，无法搜索外部职位数据",
                "jobs": []
            }, ensure_ascii=False)
        
        # 并行执行所有搜索任务 / Execute all search tasks in parallel
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果 / Merge results
        for result in search_results:
            if isinstance(result, list):
                results.extend(result)
            elif isinstance(result, Exception):
                logging.error(f"搜索任务失败: {result}")
        
        # 去重和排序 / Deduplicate and sort
        unique_results = self._deduplicate_jobs(results)
        
        return json.dumps({
            "status": "success",
            "total": len(unique_results),
            "sources": ["stepstone", "google"] if len(tasks) > 1 else ["stepstone" if settings.APIFY_TOKEN else "google"],
            "jobs": unique_results[:limit]
        }, ensure_ascii=False, indent=2)
    
    async def _search_stepstone(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """
        搜索StepStone职位 - 德国主要求职平台
        Search StepStone jobs - major German job platform
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # 根据开发文档使用Apify StepStone Scraper
                url = "https://api.apify.com/v2/acts/apify~stepstone-scraper/run-sync-get-dataset-items"
                params = {"token": settings.APIFY_TOKEN}
                data = {
                    "search": query,
                    "location": location,
                    "maxItems": limit,
                    "extendOutputFunction": "",
                    "customMapFunction": ""
                }
                
                response = await client.post(url, params=params, json=data)
                response.raise_for_status()
                
                jobs_data = response.json()
                jobs = []
                
                for item in jobs_data[:limit]:
                    job = {
                        "id": f"stepstone_{item.get('id', hash(item.get('url', '')))}",
                        "title": item.get("positionName", "").strip(),
                        "company": item.get("companyName", "").strip(),
                        "location": item.get("location", location).strip(),
                        "salary": item.get("salary", "").strip(),
                        "description": self._clean_description(item.get("description", "")),
                        "url": item.get("url", ""),
                        "source": "stepstone",
                        "skills": item.get("skills", []) or self._extract_skills_from_text(item.get("description", "")),
                        "posted_date": item.get("postedTime", ""),
                        "job_type": item.get("jobType", ""),
                        "experience_level": item.get("experienceLevel", "")
                    }
                    
                    # 过滤无效职位 / Filter invalid jobs
                    if job["title"] and job["company"]:
                        jobs.append(job)
                
                logging.info(f"StepStone搜索 '{query}' 在 '{location}' 返回 {len(jobs)} 个职位")
                return jobs
                
        except Exception as e:
            logging.error(f"StepStone搜索失败: {e}")
            return []
    
    async def _search_google_jobs(self, query: str, location: str, limit: int) -> List[Dict[str, Any]]:
        """
        搜索Google Jobs - 整合LinkedIn和Indeed
        Search Google Jobs - integrates LinkedIn and Indeed
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # 根据开发文档使用SerpAPI Google Jobs
                url = "https://serpapi.com/search.json"
                params = {
                    "q": f"{query} jobs",
                    "location": location,
                    "engine": "google_jobs",
                    "api_key": settings.SERPAPI_KEY,
                    "num": limit,
                    "hl": "en",  # 英文结果
                    "gl": "de"   # 德国地区
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                jobs = []
                
                for item in data.get("jobs_results", [])[:limit]:
                    # 提取薪资信息 / Extract salary information
                    salary_info = ""
                    if "salary" in item:
                        salary_info = item["salary"]
                    elif "extensions" in item:
                        salary_extensions = [ext for ext in item["extensions"] if any(char.isdigit() for char in ext)]
                        if salary_extensions:
                            salary_info = salary_extensions[0]
                    
                    job = {
                        "id": f"google_{item.get('job_id', hash(item.get('link', '')))}",
                        "title": item.get("title", "").strip(),
                        "company": item.get("company_name", "").strip(),
                        "location": item.get("location", location).strip(),
                        "salary": salary_info,
                        "description": self._clean_description(item.get("description", "")),
                        "url": item.get("link", item.get("share_link", "")),
                        "source": "google_jobs",
                        "skills": self._extract_skills_from_text(item.get("description", "")),
                        "posted_date": item.get("detected_extensions", {}).get("posted_at", ""),
                        "job_type": item.get("schedule_type", ""),
                        "via": item.get("via", "")
                    }
                    
                    # 过滤无效职位 / Filter invalid jobs
                    if job["title"] and job["company"]:
                        jobs.append(job)
                
                logging.info(f"Google Jobs搜索 '{query}' 在 '{location}' 返回 {len(jobs)} 个职位")
                return jobs
                
        except Exception as e:
            logging.error(f"Google Jobs搜索失败: {e}")
            return []
    
    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        职位去重 - 基于标题和公司名
        Job deduplication - based on title and company
        """
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # 创建去重键 / Create deduplication key
            key = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            if key not in seen and key != "_":
                seen.add(key)
                unique_jobs.append(job)
        
        # 按照来源和发布时间排序 / Sort by source and posting time
        return sorted(unique_jobs, key=lambda x: (x.get('source') == 'stepstone', x.get('posted_date', '')), reverse=True)
    
    def _clean_description(self, description: str, max_length: int = 500) -> str:
        """清理职位描述文本"""
        if not description:
            return ""
        
        # 移除HTML标签和多余空白 / Remove HTML tags and excess whitespace
        import re
        cleaned = re.sub(r'<[^>]+>', '', description)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 限制长度 / Limit length
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
        
        return cleaned
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """从文本中提取技能关键词"""
        if not text:
            return []
        
        # 常见技能关键词 / Common skill keywords
        common_skills = [
            "python", "java", "javascript", "react", "node.js", "typescript",
            "sql", "postgresql", "mysql", "mongodb", "redis",
            "aws", "azure", "docker", "kubernetes", "terraform",
            "git", "ci/cd", "jenkins", "jira", "agile", "scrum",
            "machine learning", "data science", "ai", "tensorflow", "pytorch"
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in common_skills if skill in text_lower]
        
        return found_skills[:10]  # 限制数量


class LocalJobSearchTool(BaseTool):
    """
    本地职位搜索工具 - Azure AI Search
    Local job search tool - Azure AI Search
    """
    
    name: str = "query_local_jobs"
    description: str = """
    搜索本地数据库中已索引的职位信息。使用Azure AI Search进行语义检索。
    适用于查找已缓存的职位数据，速度快且成本低。
    Search indexed job information in local database using Azure AI Search semantic retrieval.
    Suitable for finding cached job data with fast speed and low cost.
    """
    args_schema: type[LocalJobSearchInput] = LocalJobSearchInput
    
    def __init__(self):
        super().__init__()
    
    def _run(self, search_text: str, top: int = 10) -> str:
        """同步搜索包装器"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._arun(search_text, top))
    
    async def _arun(self, search_text: str, top: int = 10) -> str:
        """异步本地搜索"""
        try:
            # 每次都获取搜索服务 / Get search service each time
            search_service = await get_search_service()
            
            # 执行语义搜索 / Perform semantic search
            results = await search_service.search_jobs(
                query=search_text,
                top=top
            )
            
            # 转换为统一格式 / Convert to unified format
            jobs = []
            for result in results:
                job = {
                    "id": result.get("id", ""),
                    "title": result.get("title", ""),
                    "company": result.get("company", ""),
                    "location": result.get("location", ""),
                    "salary": result.get("salary", ""),
                    "description": result.get("description", ""),
                    "url": result.get("url", ""),
                    "source": result.get("source", "local"),
                    "skills": result.get("skills", []),
                    "posted_date": result.get("posted_date", ""),
                    "score": result.get("@search.score", 0)
                }
                jobs.append(job)
            
            return json.dumps({
                "status": "success",
                "total": len(jobs),
                "source": "local_database",
                "jobs": jobs
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logging.error(f"本地职位搜索失败: {e}")
            return json.dumps({
                "status": "error",
                "message": f"本地搜索失败: {str(e)}",
                "jobs": []
            }, ensure_ascii=False)


class JobSearchAgent(BaseAgent):
    """
    增强的职位搜索Agent - 实现多源数据聚合
    Enhanced job search agent - implementing multi-source data aggregation
    """
    
    def __init__(self):
        super().__init__(
            name="JobSearchAgent",
            description="智能职位搜索专家，整合多个数据源提供全面的职位信息，支持实时搜索和本地缓存"
        )
        self.search_service = None
    
    def _setup_tools(self) -> None:
        """设置增强的工具集"""
        self.tools = [
            WebSearchTool(),
            LocalJobSearchTool()
        ]
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是JobCatcher的智能职位搜索专家。你的核心职责：

## 🎯 主要功能
1. **多源数据聚合**：整合StepStone、Google Jobs、LinkedIn、Indeed等数据源
2. **智能搜索策略**：优化搜索关键词，提高结果相关性
3. **数据质量控制**：去重、清理、验证职位信息
4. **缓存管理**：更新本地数据库，提高后续搜索效率

## 🛠️ 工具使用策略
- **web_search_20250305**: 获取最新外部职位数据
  - 并行调用StepStone和Google Jobs API
  - 支持地点、关键词、数量等参数
  - 自动去重和数据清理
  
- **query_local_jobs**: 搜索本地缓存数据
  - 使用Azure AI Search语义检索
  - 速度快，成本低，适合首次查询
  - 提供相关性评分

## 📋 工作流程
1. **首先搜索本地**：检查是否有相关缓存数据
2. **补充外部数据**：调用外部API获取最新职位
3. **数据整合**：合并、去重、排序结果
4. **缓存更新**：将新职位数据存储到本地数据库
5. **结果优化**：按相关性和新鲜度排序

## 🎨 输出格式
始终返回结构化的JSON数据，包含：
- status: 搜索状态
- total: 结果总数
- sources: 数据来源
- jobs: 职位详细信息数组

每个职位包含：title, company, location, salary, description, url, source, skills, posted_date

## 🔍 搜索优化
- 理解用户意图，优化搜索关键词
- 支持技能、职位级别、工作类型等多维度搜索
- 自动处理地点信息（Berlin, Munich, Remote等）
- 智能匹配用户技能和职位要求

始终提供高质量、相关性强的职位搜索结果！"""
    
    async def invoke(self, state: AgentState) -> Dict[str, Any]:
        """执行职位搜索"""
        try:
            # 获取搜索服务和工具
            search_service = await get_search_service()
            local_search_tool = search_service.get_search_tool()
            
            # 临时添加本地搜索工具
            if local_search_tool not in self.tools:
                self.tools.append(local_search_tool)
                self.llm_with_tools = self.llm.bind_tools(self.tools)
            
            # 提取搜索查询
            search_query = state.get("search_query", "")
            if not search_query:
                # 从最新消息中提取查询
                messages = state.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        search_query = last_message.content
                    elif isinstance(last_message, dict):
                        search_query = last_message.get("content", "")
            
            if not search_query:
                return {
                    "messages": state["messages"] + [AIMessage(content="请提供搜索关键词，例如：'Python开发工程师'或'Frontend Developer'")],
                    "job_results": []
                }
            
            self.logger.info(f"开始职位搜索：{search_query}")
            
            # 调用父类方法执行Claude 4处理
            result = await super().invoke(state)
            
            # 解析和处理搜索结果
            try:
                response_content = result.get("last_response", "")
                
                # Claude 4应该返回结构化的职位数据
                # 这里添加解析逻辑，提取JSON格式的职位列表
                jobs = self._extract_jobs_from_response(response_content)
                
                # 缓存新职位到数据库
                await self._cache_jobs_to_database(jobs, search_service)
                
                result["job_results"] = jobs
                result["search_query"] = search_query
                
                self.logger.info(f"职位搜索完成，返回 {len(jobs)} 个职位")
                
            except Exception as e:
                self.logger.error(f"处理搜索结果失败: {e}")
                result["job_results"] = []
            
            return result
            
        except Exception as e:
            self.logger.error(f"JobSearchAgent执行失败: {e}")
            return {
                "messages": state["messages"] + [AIMessage(content=f"搜索时发生错误：{str(e)}")],
                "job_results": [],
                "error": str(e)
            }
    
    def _extract_jobs_from_response(self, response: str) -> List[Dict[str, Any]]:
        """从Claude 4响应中提取职位数据"""
        try:
            # 查找JSON格式的职位数据
            import re
            
            # 尝试提取JSON数组
            json_pattern = r'\[[\s\S]*?\]'
            matches = re.findall(json_pattern, response)
            
            for match in matches:
                try:
                    jobs = json.loads(match)
                    if isinstance(jobs, list) and jobs:
                        return jobs
                except json.JSONDecodeError:
                    continue
            
            # 如果找不到JSON，返回空列表
            return []
            
        except Exception as e:
            self.logger.error(f"提取职位数据失败: {e}")
            return []
    
    async def _cache_jobs_to_database(self, jobs: List[Dict[str, Any]], search_service) -> None:
        """将新职位缓存到数据库"""
        try:
            job_documents = []
            
            for job in jobs:
                if not job.get("id") or not job.get("title"):
                    continue
                
                job_doc = JobDocument(
                    id=job["id"],
                    title=job["title"],
                    company=job.get("company", ""),
                    location=job.get("location", ""),
                    salary=job.get("salary"),
                    description=job.get("description", ""),
                    skills=job.get("skills", []),
                    source=job.get("source", "unknown"),
                    url=job.get("url", ""),
                    indexed_at=datetime.now(timezone.utc),
                    expired=False
                )
                job_documents.append(job_doc)
            
            if job_documents:
                success_count = await search_service.index_jobs_batch(job_documents)
                self.logger.info(f"成功缓存 {success_count}/{len(job_documents)} 个职位到数据库")
            
        except Exception as e:
            self.logger.error(f"缓存职位到数据库失败: {e}")


# Agent实例化
# Agent instantiation
job_search_agent = JobSearchAgent() 