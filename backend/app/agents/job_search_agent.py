"""
职位搜索Agent
Job Search Agent for aggregating job data from multiple sources
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentState
from app.services.job_sources import StepStoneService, GoogleJobsService
from app.services.azure_search import AzureSearchService


class JobSearchCriteria(BaseModel):
    """
    职位搜索条件模型
    Job search criteria model
    """
    keywords: str = Field(description="搜索关键词 / Search keywords")
    location: Optional[str] = Field(default=None, description="工作地点 / Job location")
    job_type: Optional[str] = Field(default=None, description="工作类型 / Job type")
    salary_min: Optional[int] = Field(default=None, description="最低薪资 / Minimum salary")
    salary_max: Optional[int] = Field(default=None, description="最高薪资 / Maximum salary")
    experience_level: Optional[str] = Field(default=None, description="经验水平 / Experience level")
    remote_allowed: bool = Field(default=False, description="是否允许远程 / Remote work allowed")
    max_results: int = Field(default=20, description="最大结果数 / Maximum results")


class JobSearchAgent(BaseAgent):
    """
    职位搜索Agent
    Responsible for searching and aggregating job postings from multiple sources
    """
    
    def __init__(self):
        super().__init__(
            name="job_search_agent",
            description="专业的职位搜索专家，能够从多个数据源聚合职位信息 / Professional job search expert that aggregates job information from multiple sources",
            temperature=0.1
        )
        
        # 初始化服务
        # Initialize services
        self.stepstone_service = StepStoneService()
        self.google_jobs_service = GoogleJobsService()
        self.azure_search_service = AzureSearchService()
        
        self.logger = logging.getLogger("agent.job_search")
    
    def _setup_tools(self) -> None:
        """
        设置职位搜索相关工具
        Setup job search related tools
        """
        
        @tool("search_jobs_stepstone")
        def search_stepstone(
            keywords: str,
            location: str = None,
            max_results: int = 10
        ) -> Dict[str, Any]:
            """
            从StepStone搜索职位
            Search jobs from StepStone platform
            """
            try:
                results = asyncio.run(
                    self.stepstone_service.search_jobs(
                        keywords=keywords,
                        location=location,
                        max_results=max_results
                    )
                )
                return {
                    "success": True,
                    "source": "stepstone",
                    "count": len(results),
                    "jobs": results
                }
            except Exception as e:
                self.logger.error(f"StepStone搜索失败 / StepStone search failed: {e}")
                return {
                    "success": False,
                    "source": "stepstone",
                    "error": str(e),
                    "jobs": []
                }
        
        @tool("search_jobs_google")
        def search_google_jobs(
            keywords: str,
            location: str = None,
            max_results: int = 10
        ) -> Dict[str, Any]:
            """
            从Google Jobs搜索职位
            Search jobs from Google Jobs
            """
            try:
                results = asyncio.run(
                    self.google_jobs_service.search_jobs(
                        keywords=keywords,
                        location=location,
                        max_results=max_results
                    )
                )
                return {
                    "success": True,
                    "source": "google_jobs",
                    "count": len(results),
                    "jobs": results
                }
            except Exception as e:
                self.logger.error(f"Google Jobs搜索失败 / Google Jobs search failed: {e}")
                return {
                    "success": False,
                    "source": "google_jobs", 
                    "error": str(e),
                    "jobs": []
                }
        
        @tool("search_jobs_vector")
        def search_jobs_semantic(
            query: str,
            filters: Dict[str, Any] = None,
            max_results: int = 10
        ) -> Dict[str, Any]:
            """
            使用向量语义搜索职位
            Search jobs using vector semantic search
            """
            try:
                results = asyncio.run(
                    self.azure_search_service.semantic_search(
                        query=query,
                        filters=filters,
                        top_k=max_results
                    )
                )
                return {
                    "success": True,
                    "source": "vector_search",
                    "count": len(results),
                    "jobs": results
                }
            except Exception as e:
                self.logger.error(f"向量搜索失败 / Vector search failed: {e}")
                return {
                    "success": False,
                    "source": "vector_search",
                    "error": str(e),
                    "jobs": []
                }
        
        @tool("aggregate_job_results")
        def aggregate_and_deduplicate(
            job_lists: List[Dict[str, Any]],
            max_final_results: int = 20
        ) -> Dict[str, Any]:
            """
            聚合和去重职位结果
            Aggregate and deduplicate job results
            """
            try:
                all_jobs = []
                source_stats = {}
                
                # 合并所有来源的职位
                # Merge jobs from all sources
                for job_list in job_lists:
                    if job_list.get("success") and job_list.get("jobs"):
                        source = job_list.get("source", "unknown")
                        jobs = job_list["jobs"]
                        
                        source_stats[source] = len(jobs)
                        all_jobs.extend(jobs)
                
                # 去重 (基于职位标题和公司名称)
                # Deduplicate based on job title and company
                seen = set()
                unique_jobs = []
                
                for job in all_jobs:
                    key = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
                    if key not in seen:
                        seen.add(key)
                        unique_jobs.append(job)
                
                # 按相关性和时间排序
                # Sort by relevance and time
                unique_jobs.sort(
                    key=lambda x: (
                        x.get('relevance_score', 0),
                        x.get('posted_at', datetime.min)
                    ),
                    reverse=True
                )
                
                # 限制结果数量
                # Limit results
                final_jobs = unique_jobs[:max_final_results]
                
                return {
                    "success": True,
                    "total_found": len(all_jobs),
                    "unique_count": len(unique_jobs),
                    "final_count": len(final_jobs),
                    "source_stats": source_stats,
                    "jobs": final_jobs
                }
                
            except Exception as e:
                self.logger.error(f"聚合失败 / Aggregation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "jobs": []
                }
        
        # 添加移交工具
        # Add handoff tools
        transfer_to_resume_critic = self.create_handoff_tool(
            target_agent="resume_critic_agent",
            description="将职位结果移交给简历分析专家进行匹配度分析 / Transfer job results to resume analysis expert for match scoring"
        )
        
        transfer_to_skill_heatmap = self.create_handoff_tool(
            target_agent="skill_heatmap_agent", 
            description="将职位数据移交给技能分析专家生成热点图 / Transfer job data to skill analysis expert for heatmap generation"
        )
        
        # 注册所有工具
        # Register all tools
        self.tools = [
            search_stepstone,
            search_google_jobs,
            search_jobs_semantic,
            aggregate_and_deduplicate,
            transfer_to_resume_critic,
            transfer_to_skill_heatmap
        ]
    
    def get_system_prompt(self) -> str:
        """
        获取职位搜索Agent的系统提示词
        Get system prompt for job search agent
        """
        return """你是JobCatcher平台的职位搜索专家。你的主要职责是：

🎯 **核心能力 / Core Capabilities:**
- 从多个数据源（StepStone、Google Jobs、Azure搜索）聚合职位信息
- 智能解析用户的搜索需求和偏好
- 提供高质量的职位推荐和匹配
- 去重和排序职位结果

📋 **工作流程 / Workflow:**
1. 理解用户的职位搜索需求（关键词、地点、薪资等）
2. 使用多个工具并行搜索不同数据源
3. 聚合和去重搜索结果
4. 按相关性对职位进行排序
5. 如需要，移交给其他专家Agent进行进一步分析

💡 **最佳实践 / Best Practices:**
- 优先使用用户提供的具体搜索条件
- 如果搜索结果过少，尝试扩展搜索范围
- 为用户提供多样化的职位选择
- 实时监控搜索质量和用户满意度

🔧 **可用工具 / Available Tools:**
- search_jobs_stepstone: StepStone职位搜索
- search_jobs_google: Google Jobs搜索  
- search_jobs_vector: 向量语义搜索
- aggregate_job_results: 聚合去重结果
- transfer_to_resume_critic: 移交简历分析
- transfer_to_skill_heatmap: 移交技能分析

始终以用户为中心，提供最相关和有价值的职位推荐。
Always be user-centric and provide the most relevant and valuable job recommendations."""
    
    async def search_jobs_comprehensive(
        self,
        criteria: JobSearchCriteria,
        enable_parallel: bool = True
    ) -> Dict[str, Any]:
        """
        全面的职位搜索
        Comprehensive job search across multiple sources
        """
        try:
            self.logger.info(f"开始搜索职位 / Starting job search: {criteria.keywords}")
            
            search_tasks = []
            
            if enable_parallel:
                # 并行搜索所有数据源
                # Parallel search across all sources
                search_tasks = [
                    self.stepstone_service.search_jobs(
                        keywords=criteria.keywords,
                        location=criteria.location,
                        max_results=criteria.max_results // 3
                    ),
                    self.google_jobs_service.search_jobs(
                        keywords=criteria.keywords,
                        location=criteria.location,
                        max_results=criteria.max_results // 3
                    ),
                    self.azure_search_service.semantic_search(
                        query=f"{criteria.keywords} {criteria.location or ''}",
                        top_k=criteria.max_results // 3
                    )
                ]
                
                results = await asyncio.gather(*search_tasks, return_exceptions=True)
            else:
                # 顺序搜索
                # Sequential search
                results = []
                
                for service, method in [
                    (self.stepstone_service, "search_jobs"),
                    (self.google_jobs_service, "search_jobs"),
                    (self.azure_search_service, "semantic_search")
                ]:
                    try:
                        if method == "semantic_search":
                            result = await service.semantic_search(
                                query=f"{criteria.keywords} {criteria.location or ''}",
                                top_k=criteria.max_results // 3
                            )
                        else:
                            result = await service.search_jobs(
                                keywords=criteria.keywords,
                                location=criteria.location,
                                max_results=criteria.max_results // 3
                            )
                        results.append(result)
                    except Exception as e:
                        self.logger.warning(f"搜索源失败 / Search source failed: {e}")
                        results.append([])
            
            # 聚合结果
            # Aggregate results
            all_jobs = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"搜索任务 {i} 失败 / Search task {i} failed: {result}")
                    continue
                
                if isinstance(result, list):
                    all_jobs.extend(result)
            
            # 应用过滤条件
            # Apply filters
            filtered_jobs = self._apply_filters(all_jobs, criteria)
            
            # 去重和排序
            # Deduplicate and sort
            final_jobs = self._deduplicate_and_sort(filtered_jobs, criteria.max_results)
            
            return {
                "success": True,
                "criteria": criteria.dict(),
                "total_found": len(all_jobs),
                "filtered_count": len(filtered_jobs),
                "final_count": len(final_jobs),
                "jobs": final_jobs,
                "search_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"综合搜索失败 / Comprehensive search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "jobs": []
            }
    
    def _apply_filters(self, jobs: List[Dict], criteria: JobSearchCriteria) -> List[Dict]:
        """
        应用搜索过滤条件
        Apply search filters
        """
        filtered = jobs
        
        # 薪资过滤
        # Salary filtering
        if criteria.salary_min:
            filtered = [
                job for job in filtered
                if job.get('salary_min', 0) >= criteria.salary_min
            ]
        
        if criteria.salary_max:
            filtered = [
                job for job in filtered
                if job.get('salary_max', float('inf')) <= criteria.salary_max
            ]
        
        # 远程工作过滤
        # Remote work filtering
        if criteria.remote_allowed:
            filtered = [
                job for job in filtered
                if job.get('is_remote') or 'remote' in job.get('location', '').lower()
            ]
        
        return filtered
    
    def _deduplicate_and_sort(self, jobs: List[Dict], max_results: int) -> List[Dict]:
        """
        去重和排序职位
        Deduplicate and sort jobs
        """
        # 去重
        # Deduplicate
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = f"{job.get('title', '').lower()}_{job.get('company', '').lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        # 排序（按相关性、薪资、发布时间）
        # Sort by relevance, salary, posting time
        unique_jobs.sort(
            key=lambda x: (
                x.get('relevance_score', 0),
                x.get('salary_max', 0),
                x.get('posted_at', datetime.min)
            ),
            reverse=True
        )
        
        return unique_jobs[:max_results] 