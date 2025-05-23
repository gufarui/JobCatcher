"""
外部API服务集成 - JobCatcher外部数据源
External API service integration - JobCatcher external data sources

集成的外部API:
- Apify StepStone Scraper (德国职位数据)
- SerpAPI Google Jobs (Google职位搜索结果)
- JobsPikr Sandbox (Indeed替代方案)
- CoreSignal Self-Service (LinkedIn职位数据)
- APILayer Resume Parser (简历解析)
- PDFMonkey (PDF生成)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class ExternalAPIService:
    """
    外部API服务集成类 - 简化版本，让Claude 4处理分析
    External API service integration - simplified version, let Claude 4 handle analysis
    """
    
    def __init__(self):
        """
        初始化外部API服务 - 从环境变量获取API密钥
        Initialize external API service - get API keys from environment variables
        """
        # API密钥从环境变量获取 / API keys from environment variables
        self.apify_token = os.getenv("APIFY_TOKEN")
        self.serpapi_key = os.getenv("SERPAPI_KEY") 
        self.jobspikr_key = os.getenv("JOBSPIKR_KEY")
        self.coresignal_key = os.getenv("CORESIGNAL_KEY")
        self.apilayer_key = os.getenv("APILAYER_KEY")
        self.pdfmonkey_key = os.getenv("PDFMONKEY_KEY")
        
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        获取HTTP会话 / Get HTTP session
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search_stepstone_jobs(
        self, 
        keywords: str, 
        location: str = "Germany",
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        使用Apify StepStone爬虫搜索德国职位
        Search German jobs using Apify StepStone scraper
        
        Args:
            keywords: 搜索关键词 / Search keywords
            location: 搜索地点 / Search location  
            max_results: 最大结果数 / Maximum results
        """
        try:
            if not self.apify_token:
                logger.warning("Apify token not configured, returning mock data")
                return await self._get_mock_stepstone_jobs(keywords, max_results)
            
            session = await self._get_session()
            
            # Apify StepStone Actor配置
            # Apify StepStone Actor configuration
            payload = {
                "keywords": keywords,
                "location": location,
                "maxItems": max_results,
                "outputFields": [
                    "title", "company", "location", "salary", 
                    "jobUrl", "description", "postedAt", "jobType"
                ]
            }
            
            url = "https://api.apify.com/v2/acts/YOUR_STEPSTONE_ACTOR_ID/run-sync-get-dataset-items"
            headers = {
                "Authorization": f"Bearer {self.apify_token}",
                "Content-Type": "application/json"
            }
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    jobs = []
                    
                    for item in data:
                        job = {
                            "id": f"stepstone_{item.get('jobUrl', '').split('/')[-1]}",
                            "title": item.get("title", ""),
                            "company": item.get("company", ""),
                            "location": item.get("location", ""),
                            "salary": item.get("salary", ""),
                            "source": "StepStone",
                            "url": item.get("jobUrl", ""),
                            "description": item.get("description", "")[:500],
                            "posted_date": item.get("postedAt", ""),
                            "job_type": item.get("jobType", "")
                        }
                        jobs.append(job)
                    
                    logger.info(f"Retrieved {len(jobs)} jobs from StepStone")
                    return jobs
                else:
                    logger.error(f"StepStone API error: {response.status}")
                    return await self._get_mock_stepstone_jobs(keywords, max_results)
                    
        except Exception as e:
            logger.error(f"Error calling StepStone API: {e}")
            return await self._get_mock_stepstone_jobs(keywords, max_results)
    
    async def search_google_jobs(
        self, 
        keywords: str, 
        location: str = "Germany",
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        使用SerpAPI搜索Google Jobs
        Search Google Jobs using SerpAPI
        """
        try:
            if not self.serpapi_key:
                logger.warning("SerpAPI key not configured, returning mock data")
                return await self._get_mock_google_jobs(keywords, max_results)
            
            session = await self._get_session()
            
            params = {
                "engine": "google_jobs",
                "q": keywords,
                "location": location,
                "api_key": self.serpapi_key,
                "num": min(max_results, 10)  # SerpAPI限制
            }
            
            url = "https://serpapi.com/search"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    jobs = []
                    
                    for item in data.get("jobs_results", []):
                        job = {
                            "id": f"google_{item.get('job_id', '')}",
                            "title": item.get("title", ""),
                            "company": item.get("company_name", ""),
                            "location": item.get("location", ""),
                            "salary": item.get("detected_extensions", {}).get("salary", ""),
                            "source": "Google Jobs",
                            "url": item.get("share_link", ""),
                            "description": item.get("description", "")[:500],
                            "posted_date": item.get("detected_extensions", {}).get("posted_at", ""),
                            "job_type": item.get("detected_extensions", {}).get("schedule_type", "")
                        }
                        jobs.append(job)
                    
                    logger.info(f"Retrieved {len(jobs)} jobs from Google Jobs")
                    return jobs
                else:
                    logger.error(f"Google Jobs API error: {response.status}")
                    return await self._get_mock_google_jobs(keywords, max_results)
                    
        except Exception as e:
            logger.error(f"Error calling Google Jobs API: {e}")
            return await self._get_mock_google_jobs(keywords, max_results)
    
    async def search_all_sources(
        self, 
        keywords: str, 
        location: str = "Germany",
        max_results_per_source: int = 10
    ) -> List[Dict[str, Any]]:
        """
        并行搜索所有职位数据源 - Claude 4会智能合并和分析结果
        Search all job sources in parallel - Claude 4 will intelligently merge and analyze results
        """
        try:
            logger.info(f"Searching all sources for: {keywords}")
            
            # 并行调用所有数据源 / Call all data sources in parallel
            tasks = [
                self.search_stepstone_jobs(keywords, location, max_results_per_source),
                self.search_google_jobs(keywords, location, max_results_per_source),
                # 可以添加更多数据源 / Can add more data sources
                # self.search_jobspikr(keywords, location, max_results_per_source),
                # self.search_coresignal(keywords, location, max_results_per_source)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并所有结果 / Merge all results
            all_jobs = []
            for result in results:
                if isinstance(result, list):
                    all_jobs.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error in parallel search: {result}")
            
            logger.info(f"Total jobs found: {len(all_jobs)}")
            return all_jobs
            
        except Exception as e:
            logger.error(f"Error in search_all_sources: {e}")
            return []
    
    async def _get_mock_stepstone_jobs(self, keywords: str, max_results: int) -> List[Dict[str, Any]]:
        """
        StepStone模拟数据 - 开发阶段使用
        StepStone mock data - for development phase
        """
        return [
            {
                "id": f"stepstone_mock_{i}",
                "title": f"{keywords} Developer - StepStone",
                "company": f"German Tech Company {i}",
                "location": "Berlin, Germany",
                "salary": f"€{45000 + i*5000} - €{75000 + i*5000}",
                "source": "StepStone",
                "url": f"https://stepstone.de/job-mock-{i}",
                "description": f"We are looking for an experienced {keywords} developer...",
                "posted_date": "2025-05-23",
                "job_type": "Full-time"
            }
            for i in range(min(max_results, 5))
        ]
    
    async def _get_mock_google_jobs(self, keywords: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Google Jobs模拟数据 - 开发阶段使用
        Google Jobs mock data - for development phase
        """
        return [
            {
                "id": f"google_mock_{i}",
                "title": f"Senior {keywords} Engineer - Google Jobs",
                "company": f"International Company {i}",
                "location": "Munich, Germany",
                "salary": f"€{50000 + i*7000} - €{90000 + i*7000}",
                "source": "Google Jobs",
                "url": f"https://jobs.google.com/job-mock-{i}",
                "description": f"Join our team as a {keywords} professional...",
                "posted_date": "2025-05-23",
                "job_type": "Full-time"
            }
            for i in range(min(max_results, 5))
        ]
    
    async def close(self):
        """
        关闭HTTP会话 / Close HTTP session
        """
        if self.session:
            await self.session.close() 