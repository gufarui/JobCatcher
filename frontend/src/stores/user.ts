/**
 * 用户状态管理
 * User state management store for JobCatcher
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'
import { ElMessage } from 'element-plus'
import type { User, LoginResponse } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  // 状态 / State
  const user = ref<User | null>(null)
  const token = ref<string>('')
  const isLoading = ref(false)
  const error = ref<string>('')

  // 计算属性 / Computed
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userName = computed(() => user.value?.name || '未知用户')
  const userEmail = computed(() => user.value?.email || '')
  const userAvatar = computed(() => user.value?.avatar || '')

  // 操作 / Actions
  
  /**
   * 初始化用户认证状态 / Initialize user authentication status
   */
  const initAuth = () => {
    const savedToken = localStorage.getItem('jobcatcher_token')
    if (savedToken) {
      token.value = savedToken
      // 设置API默认headers / Set API default headers
      api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
    }
  }

  /**
   * 检查用户认证状态 / Check user authentication status
   */
  const checkAuthStatus = async () => {
    if (!token.value) return false

    try {
      isLoading.value = true
      const response = await api.get('/auth/me')
      user.value = response.data
      return true
    } catch (err: any) {
      console.error('Auth check failed:', err)
      logout()
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Google OAuth登录 / Google OAuth login
   */
  const loginWithGoogle = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    const redirectUri = `${window.location.origin}/auth/callback`
    
    // 生成随机state参数用于CSRF保护 / Generate random state parameter for CSRF protection
    const state = Math.random().toString(36).substring(2, 15) + 
                  Math.random().toString(36).substring(2, 15)
    
    // 保存state到sessionStorage以便验证 / Save state to sessionStorage for verification
    sessionStorage.setItem('oauth_state', state)
    
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'openid email profile',
      access_type: 'offline',
      prompt: 'consent',
      state: state
    })

    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`
    window.location.href = authUrl
  }

  /**
   * 处理OAuth回调 / Handle OAuth callback
   */
  const handleOAuthCallback = async (code: string): Promise<boolean> => {
    try {
      isLoading.value = true
      error.value = ''

      const response = await api.post<LoginResponse>('/auth/google', { code })
      const { token: newToken, user: userData } = response.data

      // 保存认证信息 / Save authentication info
      token.value = newToken
      user.value = userData
      localStorage.setItem('jobcatcher_token', newToken)
      
      // 设置API默认headers / Set API default headers
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`

      ElMessage.success(`欢迎回来，${userData.name}！`)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.message || '登录失败，请重试'
      ElMessage.error(error.value)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 登出 / Logout
   */
  const logout = async () => {
    try {
      // 调用后端登出接口 / Call backend logout endpoint
      if (token.value) {
        await api.post('/auth/logout')
      }
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      // 清理本地状态 / Clear local state
      user.value = null
      token.value = ''
      localStorage.removeItem('jobcatcher_token')
      delete api.defaults.headers.common['Authorization']
      
      ElMessage.info('已安全退出')
    }
  }

  /**
   * 更新用户信息 / Update user information
   */
  const updateUserProfile = async (userData: Partial<User>) => {
    try {
      isLoading.value = true
      const response = await api.put('/auth/profile', userData)
      user.value = { ...user.value, ...response.data } as User
      ElMessage.success('个人信息更新成功')
      return true
    } catch (err: any) {
      error.value = err.response?.data?.message || '更新失败'
      ElMessage.error(error.value)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 刷新用户信息 / Refresh user information
   */
  const refreshUserData = async () => {
    if (!token.value) return
    
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (err) {
      console.error('Failed to refresh user data:', err)
    }
  }

  /**
   * 上传简历文件 / Upload resume file
   */
  const uploadResume = async (file: File): Promise<string> => {
    try {
      isLoading.value = true
      error.value = ''

      // 验证文件类型 / Validate file type
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
      if (!allowedTypes.includes(file.type)) {
        throw new Error('Only PDF and Word documents are supported')
      }

      // 验证文件大小 (最大10MB) / Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        throw new Error('File size must be less than 10MB')
      }

      // 创建FormData / Create FormData
      const formData = new FormData()
      formData.append('file', file)

      // 上传到后端 / Upload to backend
      const response = await api.post('/cv/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          // 可以在这里处理上传进度 / Can handle upload progress here
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            console.log(`Upload progress: ${percentCompleted}%`)
          }
        }
      })

      const resumeId = response.data.resume_id
      ElMessage.success('Resume uploaded successfully!')
      
      return resumeId
    } catch (err: any) {
      error.value = err.response?.data?.message || err.message || 'Failed to upload resume'
      ElMessage.error(error.value)
      throw new Error(error.value)
    } finally {
      isLoading.value = false
    }
  }

  // 初始化认证状态 / Initialize auth state
  initAuth()

  return {
    // 状态 / State
    user: readonly(user),
    token: readonly(token),
    isLoading: readonly(isLoading),
    error: readonly(error),
    
    // 计算属性 / Computed
    isAuthenticated,
    userName,
    userEmail,
    userAvatar,
    
    // 操作 / Actions
    checkAuthStatus,
    loginWithGoogle,
    handleOAuthCallback,
    logout,
    updateUserProfile,
    refreshUserData,
    uploadResume
  }
}) 