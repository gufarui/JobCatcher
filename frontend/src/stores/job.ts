/**
 * 职位管理状态存储
 * Job management state store
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

// 类型定义 / Type definitions
interface Job {
  id: string
  title: string
  company: string
  location: string
  salary: string
  source: string
  url: string
  description: string
  posted_date: string
  match_score?: number
}

interface SearchParams {
  query: string
  location: string
  salaryRange: string
  jobType: string
}

interface JobRecommendation {
  job: Job
  match_score: number
  matching_skills: string[]
  missing_skills: string[]
}

export const useJobStore = defineStore('job', () => {
  // 状态 / State
  const jobs = ref<Job[]>([])
  const recommendations = ref<JobRecommendation[]>([])
  const isLoading = ref(false)
  const lastSearchParams = ref<SearchParams | null>(null)
  const searchHistory = ref<SearchParams[]>([])

  // 搜索职位 / Search jobs
  const searchJobs = async (params: SearchParams): Promise<Job[]> => {
    try {
      isLoading.value = true
      lastSearchParams.value = params

      // 构建查询参数 / Build query parameters
      const queryParams = new URLSearchParams()
      if (params.query) queryParams.append('q', params.query)
      if (params.location) queryParams.append('location', params.location)
      if (params.jobType) queryParams.append('type', params.jobType)
      
      // 处理薪资范围 / Handle salary range
      if (params.salaryRange) {
        const [min, max] = params.salaryRange.split('-').map(s => parseInt(s))
        if (min) queryParams.append('salary_min', min.toString())
        if (max && max !== 999999) queryParams.append('salary_max', max.toString())
      }

      // 调用后端API / Call backend API
      const response = await axios.get(`/api/jobs/search?${queryParams.toString()}`)
      
      const searchResults = response.data.jobs || []
      jobs.value = searchResults

      // 保存搜索历史 / Save search history
      addToSearchHistory(params)

      return searchResults
    } catch (error) {
      console.error('Failed to search jobs:', error)
      throw new Error('Failed to search jobs. Please try again.')
    } finally {
      isLoading.value = false
    }
  }

  // 获取职位推荐 / Get job recommendations
  const getRecommendations = async (resumeId?: string): Promise<JobRecommendation[]> => {
    try {
      isLoading.value = true

      const params = new URLSearchParams()
      if (resumeId) params.append('resume_id', resumeId)

      const response = await axios.get(`/api/jobs/recommend?${params.toString()}`)
      const recommendationResults = response.data.recommendations || []
      
      recommendations.value = recommendationResults
      return recommendationResults
    } catch (error) {
      console.error('Failed to get recommendations:', error)
      throw new Error('Failed to get job recommendations.')
    } finally {
      isLoading.value = false
    }
  }

  // 获取职位详情 / Get job details
  const getJobDetails = async (jobId: string): Promise<Job | null> => {
    try {
      const response = await axios.get(`/api/jobs/${jobId}`)
      return response.data.job || null
    } catch (error) {
      console.error('Failed to get job details:', error)
      return null
    }
  }

  // 添加到搜索历史 / Add to search history
  const addToSearchHistory = (params: SearchParams) => {
    // 检查是否已存在相同搜索 / Check if same search already exists
    const existingIndex = searchHistory.value.findIndex(
      item => JSON.stringify(item) === JSON.stringify(params)
    )
    
    if (existingIndex !== -1) {
      // 移除旧记录 / Remove old record
      searchHistory.value.splice(existingIndex, 1)
    }
    
    // 添加到开头 / Add to beginning
    searchHistory.value.unshift(params)
    
    // 保持最多10条历史记录 / Keep max 10 history records
    if (searchHistory.value.length > 10) {
      searchHistory.value = searchHistory.value.slice(0, 10)
    }
    
    // 保存到localStorage / Save to localStorage
    saveSearchHistoryToStorage()
  }

  // 清除搜索历史 / Clear search history
  const clearSearchHistory = () => {
    searchHistory.value = []
    localStorage.removeItem('job_search_history')
  }

  // 保存搜索历史到localStorage / Save search history to localStorage
  const saveSearchHistoryToStorage = () => {
    try {
      localStorage.setItem('job_search_history', JSON.stringify(searchHistory.value))
    } catch (error) {
      console.error('Failed to save search history:', error)
    }
  }

  // 从localStorage加载搜索历史 / Load search history from localStorage
  const loadSearchHistoryFromStorage = () => {
    try {
      const saved = localStorage.getItem('job_search_history')
      if (saved) {
        searchHistory.value = JSON.parse(saved)
      }
    } catch (error) {
      console.error('Failed to load search history:', error)
      searchHistory.value = []
    }
  }

  // 重置状态 / Reset state
  const reset = () => {
    jobs.value = []
    recommendations.value = []
    isLoading.value = false
    lastSearchParams.value = null
  }

  // 获取热门搜索关键词 / Get popular search keywords
  const getPopularKeywords = (): string[] => {
    // 基于搜索历史统计热门关键词 / Get popular keywords based on search history
    const keywords = searchHistory.value
      .map(item => item.query)
      .filter(query => query && query.trim().length > 0)
    
    // 统计频率并返回前5个 / Count frequency and return top 5
    const keywordCount = keywords.reduce((acc, keyword) => {
      acc[keyword] = (acc[keyword] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    return Object.entries(keywordCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([keyword]) => keyword)
  }

  // 按匹配度排序职位 / Sort jobs by match score
  const sortJobsByMatchScore = () => {
    jobs.value.sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
  }

  // 过滤职位 / Filter jobs
  const filterJobs = (filterFn: (job: Job) => boolean): Job[] => {
    return jobs.value.filter(filterFn)
  }

  // 初始化store / Initialize store
  const initialize = () => {
    loadSearchHistoryFromStorage()
  }

  return {
    // 状态 / State
    jobs,
    recommendations,
    isLoading,
    lastSearchParams,
    searchHistory,
    
    // 行为 / Actions
    searchJobs,
    getRecommendations,
    getJobDetails,
    addToSearchHistory,
    clearSearchHistory,
    reset,
    getPopularKeywords,
    sortJobsByMatchScore,
    filterJobs,
    initialize
  }
}) 