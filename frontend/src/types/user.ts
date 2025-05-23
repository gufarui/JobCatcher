/**
 * 用户相关类型定义
 * User-related type definitions
 */

// 用户信息接口 / User information interface
export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  avatar_url?: string
  created_at: string
  updated_at: string
  is_active: boolean
  last_login?: string
}

// 登录响应接口 / Login response interface
export interface LoginResponse {
  token: string
  user: User
  expires_in: number
  token_type: string
}

// OAuth回调参数接口 / OAuth callback parameters interface
export interface OAuthCallbackParams {
  code: string
  state: string
  error?: string
  error_description?: string
}

// 用户更新数据接口 / User update data interface
export interface UserUpdateData {
  name?: string
  avatar?: string
  preferences?: UserPreferences
}

// 用户偏好设置接口 / User preferences interface
export interface UserPreferences {
  language: 'en' | 'zh-CN'
  theme: 'light' | 'dark' | 'auto'
  notifications: {
    email: boolean
    push: boolean
    job_alerts: boolean
  }
  job_search: {
    default_location: string
    salary_range: string
    job_types: string[]
  }
}

// 简历信息接口 / Resume information interface
export interface Resume {
  id: string
  user_id: string
  filename: string
  file_url: string
  file_size: number
  content_text: string
  parsed_data: ResumeData
  created_at: string
  updated_at: string
}

// 解析后的简历数据接口 / Parsed resume data interface
export interface ResumeData {
  personal_info: {
    name: string
    email: string
    phone?: string
    location?: string
    linkedin?: string
    github?: string
  }
  summary?: string
  experience: WorkExperience[]
  education: Education[]
  skills: string[]
  languages?: Language[]
  certifications?: Certification[]
}

// 工作经历接口 / Work experience interface
export interface WorkExperience {
  company: string
  position: string
  start_date: string
  end_date?: string
  is_current: boolean
  description: string
  technologies?: string[]
}

// 教育经历接口 / Education interface
export interface Education {
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date?: string
  gpa?: string
  description?: string
}

// 语言技能接口 / Language skill interface
export interface Language {
  name: string
  proficiency: 'beginner' | 'intermediate' | 'advanced' | 'native'
}

// 认证证书接口 / Certification interface
export interface Certification {
  name: string
  issuer: string
  issue_date: string
  expiry_date?: string
  credential_id?: string
  credential_url?: string
} 