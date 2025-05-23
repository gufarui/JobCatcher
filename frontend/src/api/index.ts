/**
 * API 配置和 Axios 实例
 * API configuration and Axios instance for JobCatcher
 */

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

// API 基础配置 / API base configuration
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000, // 30秒超时 / 30 seconds timeout
  withCredentials: true, // 支持跨域cookie / Support cross-domain cookies
}

// 创建 Axios 实例 / Create Axios instance
export const api: AxiosInstance = axios.create(API_CONFIG)

// 请求拦截器 / Request interceptor
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 添加认证token / Add authentication token
    const token = localStorage.getItem('jobcatcher_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加请求时间戳 / Add request timestamp
    if (config.headers) {
      config.headers['X-Request-Time'] = Date.now().toString()
    }

    // 添加语言标识 / Add language identifier
    const language = localStorage.getItem('jobcatcher_language') || 'zh-CN'
    if (config.headers) {
      config.headers['Accept-Language'] = language
    }

    // 开发环境下打印请求信息 / Print request info in development
    if (import.meta.env.DEV) {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
        headers: config.headers
      })
    }

    return config
  },
  (error) => {
    console.error('❌ Request Error:', error)
    ElMessage.error('请求配置错误 / Request configuration error')
    return Promise.reject(error)
  }
)

// 响应拦截器 / Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // 开发环境下打印响应信息 / Print response info in development
    if (import.meta.env.DEV) {
      console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data
      })
    }

    // 检查业务状态码 / Check business status code
    const { code, message, data } = response.data
    
    if (code !== undefined && code !== 200 && code !== 0) {
      // 业务错误处理 / Business error handling
      ElMessage.error(message || '操作失败 / Operation failed')
      return Promise.reject(new Error(message || 'Business error'))
    }

    return response
  },
  async (error) => {
    const { response, config } = error

    // 开发环境下打印错误信息 / Print error info in development
    if (import.meta.env.DEV) {
      console.error(`❌ API Error: ${config?.method?.toUpperCase()} ${config?.url}`, {
        status: response?.status,
        data: response?.data,
        message: error.message
      })
    }

    // 网络错误处理 / Network error handling
    if (!response) {
      ElMessage.error('网络连接失败，请检查网络设置 / Network connection failed')
      return Promise.reject(error)
    }

    // HTTP状态码错误处理 / HTTP status code error handling
    const { status, data } = response
    
    switch (status) {
      case 400:
        ElMessage.error(data?.message || '请求参数错误 / Invalid request parameters')
        break
        
      case 401:
        // 未授权，清除token并跳转登录 / Unauthorized, clear token and redirect to login
        localStorage.removeItem('jobcatcher_token')
        delete api.defaults.headers.common['Authorization']
        
        ElMessageBox.confirm(
          '登录状态已过期，请重新登录 / Login session expired, please login again',
          '提示 / Notice',
          {
            confirmButtonText: '重新登录 / Login Again',
            cancelButtonText: '取消 / Cancel',
            type: 'warning'
          }
        ).then(() => {
          // 跳转到登录页 / Redirect to login page
          window.location.href = '/'
        }).catch(() => {
          // 用户取消，不做处理 / User cancelled, do nothing
        })
        break
        
      case 403:
        ElMessage.error('权限不足，无法访问 / Insufficient permissions')
        break
        
      case 404:
        ElMessage.error('请求的资源不存在 / Requested resource not found')
        break
        
      case 422:
        // 表单验证错误 / Form validation error
        const errors = data?.errors || {}
        const errorMessages = Object.values(errors).flat()
        if (errorMessages.length > 0) {
          ElMessage.error(errorMessages[0] as string)
        } else {
          ElMessage.error('数据验证失败 / Data validation failed')
        }
        break
        
      case 429:
        ElMessage.error('请求过于频繁，请稍后再试 / Too many requests, please try again later')
        break
        
      case 500:
        ElMessage.error('服务器内部错误 / Internal server error')
        break
        
      case 502:
      case 503:
      case 504:
        ElMessage.error('服务暂时不可用，请稍后再试 / Service temporarily unavailable')
        break
        
      default:
        ElMessage.error(data?.message || `请求失败 (${status}) / Request failed (${status})`)
    }

    return Promise.reject(error)
  }
)

// API 请求方法封装 / API request method wrapper
export const request = {
  /**
   * GET 请求 / GET request
   */
  get<T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> {
    return api.get(url, { params, ...config }).then(res => res.data)
  },

  /**
   * POST 请求 / POST request
   */
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return api.post(url, data, config).then(res => res.data)
  },

  /**
   * PUT 请求 / PUT request
   */
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return api.put(url, data, config).then(res => res.data)
  },

  /**
   * DELETE 请求 / DELETE request
   */
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return api.delete(url, config).then(res => res.data)
  },

  /**
   * PATCH 请求 / PATCH request
   */
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return api.patch(url, data, config).then(res => res.data)
  },

  /**
   * 文件上传 / File upload
   */
  upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    return api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    }).then(res => res.data)
  },

  /**
   * 文件下载 / File download
   */
  download(url: string, filename?: string, params?: any): Promise<void> {
    return api.get(url, {
      params,
      responseType: 'blob'
    }).then(response => {
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
  }
}

// 导出默认实例 / Export default instance
export default api 