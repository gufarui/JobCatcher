<template>
  <div class="app-main">
    <!-- 左栏：职位检索 + 展示 -->
    <!-- Left panel: Job search and display -->
    <div class="left-panel">
      <!-- 顶部搜索框组件 -->
      <!-- Top search bar component -->
      <SearchBar 
        :is-loading="isSearching"
        :total-jobs="jobs.length"
        @search="handleJobSearch"
      />
      
      <!-- 职位列表 -->
      <!-- Job list -->
      <div class="jobs-container">
        <div v-if="isSearching" class="loading-state">
          <el-icon class="loading-icon" size="48">
            <Loading />
          </el-icon>
          <p>Searching for jobs...</p>
        </div>
        
        <div v-else-if="jobs.length === 0 && hasSearched" class="empty-state">
          <el-icon size="64" color="#d0d0d0">
            <Search />
          </el-icon>
          <p>No jobs found. Try different search criteria.</p>
        </div>
        
        <div v-else-if="jobs.length === 0" class="initial-state">
          <el-icon size="64" color="#d0d0d0">
            <Suitcase />
          </el-icon>
          <p>Enter job title or skills to find opportunities</p>
        </div>
        
        <!-- 职位卡片列表 -->
        <!-- Job card list -->
        <div v-else class="jobs-list">
          <JobCard
            v-for="job in jobs"
            :key="job.id"
            :job="job"
            @click="openJobLink"
          />
        </div>
      </div>
    </div>

    <!-- 右栏：AI 聊天助手 -->
    <!-- Right panel: AI chat assistant -->
    <div class="right-panel">
      <!-- 聊天组件 -->
      <!-- Chat component -->
      <ChatBox
        :messages="chatMessages"
        :is-loading="isChatLoading"
        @send-message="handleSendMessage"
        @upload-resume="handleResumeUpload"
        @clear-chat="handleClearChat"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * JobCatcher 主应用页面
 * Main application page for JobCatcher
 * 
 * 布局：左栏职位检索展示 + 右栏AI聊天助手
 * Layout: Left panel for job search/display + Right panel for AI chat assistant
 */

import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useJobStore } from '@/stores/job'
import { useChatStore } from '@/stores/chat'
import { ElIcon, ElMessage } from 'element-plus'
import { Search, Loading, Suitcase } from '@element-plus/icons-vue'

// 导入组件 / Import components
import SearchBar from '@/components/SearchBar.vue'
import JobCard from '@/components/JobCard.vue'
import ChatBox from '@/components/ChatBox.vue'

// 类型定义 / Type definitions
interface SearchParams {
  query: string
  location: string
  salaryRange: string
  jobType: string
}

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

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// 使用stores / Use stores
const userStore = useUserStore()
const jobStore = useJobStore()
const chatStore = useChatStore()
const router = useRouter()

// 响应式数据 / Reactive data
const jobs = ref<Job[]>([])
const chatMessages = ref<ChatMessage[]>([])
const isSearching = ref(false)
const isChatLoading = ref(false)
const hasSearched = ref(false)

// 方法 / Methods
/**
 * 处理职位搜索
 * Handle job search
 */
const handleJobSearch = async (params: SearchParams) => {
  try {
    isSearching.value = true
    hasSearched.value = true
    
    // 调用API搜索职位 / Call API to search jobs
    const searchResults = await jobStore.searchJobs(params)
    jobs.value = searchResults
    
    ElMessage.success(`Found ${searchResults.length} jobs`)
  } catch (error) {
    console.error('Job search failed:', error)
    ElMessage.error('Failed to search jobs. Please try again.')
    jobs.value = []
  } finally {
    isSearching.value = false
  }
}

/**
 * 打开职位链接
 * Open job link in new tab
 */
const openJobLink = (job: Job) => {
  if (job.url) {
    window.open(job.url, '_blank')
  }
}

/**
 * 处理发送聊天消息
 * Handle sending chat message
 */
const handleSendMessage = async (content: string) => {
  try {
    isChatLoading.value = true
    
    // 添加用户消息到聊天历史 / Add user message to chat history
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    chatMessages.value.push(userMessage)
    
    // 发送到后端AI助手 / Send to backend AI assistant
    const aiResponse = await chatStore.sendMessage(content)
    
    // 添加AI回复到聊天历史 / Add AI response to chat history
    const aiMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: aiResponse,
      timestamp: new Date()
    }
    chatMessages.value.push(aiMessage)
    
  } catch (error) {
    console.error('Failed to send message:', error)
    ElMessage.error('Failed to send message. Please try again.')
  } finally {
    isChatLoading.value = false
  }
}

/**
 * 处理简历上传
 * Handle resume upload
 */
const handleResumeUpload = async (file: File) => {
  try {
    isChatLoading.value = true
    
    // 上传简历文件 / Upload resume file
    const uploadResult = await userStore.uploadResume(file)
    
    // 添加系统消息 / Add system message
    const systemMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: 'Resume uploaded successfully! Please enter target job keywords to get personalized recommendations.',
      timestamp: new Date()
    }
    chatMessages.value.push(systemMessage)
    
    ElMessage.success('Resume uploaded successfully!')
    
  } catch (error) {
    console.error('Resume upload failed:', error)
    ElMessage.error('Failed to upload resume. Please try again.')
  } finally {
    isChatLoading.value = false
  }
}

/**
 * 处理清除聊天记录
 * Handle clear chat history
 */
const handleClearChat = async () => {
  try {
    await chatStore.clearChat()
    chatMessages.value = []
    ElMessage.success('Chat history cleared')
  } catch (error) {
    console.error('Failed to clear chat:', error)
    ElMessage.error('Failed to clear chat history')
  }
}

/**
 * 检查用户登录状态
 * Check user authentication status
 */
const checkAuthStatus = () => {
  if (!userStore.isAuthenticated) {
    ElMessage.warning('Please login to continue')
    router.push('/')
  }
}

// 生命周期钩子 / Lifecycle hooks
onMounted(() => {
  checkAuthStatus()
  // 加载聊天历史 / Load chat history
  chatStore.loadChatHistory().then(history => {
    chatMessages.value = history
  })
})
</script>

<style scoped>
.app-main {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

/* 左栏：职位检索展示 / Left panel: Job search and display */
.left-panel {
  flex: 1;
  min-width: 0; /* 防止flex子项收缩问题 / Prevent flex item shrinking issues */
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow: hidden;
}

/* 职位容器 / Jobs container */
.jobs-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px; /* 为滚动条留空间 / Space for scrollbar */
}

/* 职位列表 / Jobs list */
.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 状态显示 / State displays */
.loading-state,
.empty-state,
.initial-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  text-align: center;
  color: #606266;
}

.loading-state .loading-icon {
  animation: rotate 2s linear infinite;
  color: #409eff;
  margin-bottom: 16px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-state p,
.initial-state p {
  margin-top: 16px;
  font-size: 16px;
}

/* 右栏：AI聊天助手 / Right panel: AI chat assistant */
.right-panel {
  width: 400px;
  background: #ffffff;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

/* 响应式设计 / Responsive design */
@media (max-width: 1024px) {
  .app-main {
    flex-direction: column;
  }
  
  .left-panel {
    height: 50vh;
  }
  
  .right-panel {
    width: 100%;
    height: 50vh;
    border-left: none;
    border-top: 1px solid #e4e7ed;
  }
}

@media (max-width: 768px) {
  .left-panel {
    padding: 16px;
  }
  
  .right-panel {
    height: 60vh;
  }
}

/* 滚动条样式 / Scrollbar styling */
.jobs-container::-webkit-scrollbar {
  width: 6px;
}

.jobs-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.jobs-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.jobs-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 