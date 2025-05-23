<template>
  <div class="chat-box">
    <!-- 聊天头部 / Chat Header -->
    <div class="chat-header">
      <div class="header-title">
        <el-icon class="title-icon"><ChatRound /></el-icon>
        <h3>AI Job Assistant</h3>
      </div>
      <div class="header-actions">
        <el-button 
          type="danger" 
          size="small" 
          :icon="Delete"
          @click="handleClearChat"
          title="Clear Chat History"
        >
          Clear
        </el-button>
      </div>
    </div>

    <!-- 聊天消息区域 / Chat Messages Area -->
    <div class="messages-area" ref="messagesContainer">
      <div 
        v-for="message in messages" 
        :key="message.id"
        :class="['message', `message-${message.role}`]"
      >
        <!-- 消息头部 / Message Header -->
        <div class="message-header">
          <div class="message-avatar">
            <el-icon v-if="message.role === 'user'">
              <User />
            </el-icon>
            <el-icon v-else-if="message.role === 'assistant'">
              <Robot />
            </el-icon>
            <el-icon v-else>
              <Tools />
            </el-icon>
          </div>
          <div class="message-meta">
            <span class="message-role">
              {{ message.role === 'user' ? 'You' : 
                 message.role === 'assistant' ? 'AI Assistant' : 'System' }}
            </span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
        </div>

        <!-- 消息内容 / Message Content -->
        <div class="message-content">
          <div 
            v-if="message.role === 'assistant'"
            class="markdown-content" 
            v-html="renderMarkdown(message.content)"
          ></div>
          <div v-else class="text-content">
            {{ message.content }}
          </div>
          
          <!-- 下载链接 / Download Links -->
          <div v-if="message.downloadUrl" class="download-section">
            <el-button 
              type="primary" 
              size="small"
              :icon="Download"
              @click="downloadFile(message.downloadUrl, message.filename)"
            >
              Download {{ message.filename || 'File' }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 打字指示器 / Typing Indicator -->
      <div v-if="isTyping" class="typing-indicator">
        <div class="message message-assistant">
          <div class="message-header">
            <div class="message-avatar">
              <el-icon><Robot /></el-icon>
            </div>
            <div class="message-meta">
              <span class="message-role">AI Assistant</span>
            </div>
          </div>
          <div class="message-content">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 聊天输入区域 / Chat Input Area -->
    <div class="input-area">
      <!-- 文件上传区域 / File Upload Area -->
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          :before-upload="handleResumeUpload"
          accept=".pdf,.doc,.docx"
          :show-file-list="false"
          :auto-upload="false"
          class="resume-upload"
        >
          <el-button 
            type="primary" 
            size="small"
            :icon="Upload"
            :loading="isUploading"
          >
            Upload Resume
          </el-button>
        </el-upload>
        
        <el-text v-if="uploadedFileName" type="success" size="small">
          <el-icon><DocumentChecked /></el-icon>
          {{ uploadedFileName }}
        </el-text>
      </div>

      <!-- 消息输入框 / Message Input -->
      <div class="message-input-section">
        <el-input
          v-model="currentMessage"
          type="textarea"
          :rows="3"
          placeholder="Ask me anything about jobs, career advice, or upload your resume for analysis..."
          class="message-input"
          :disabled="isConnecting || isTyping"
          @keydown="handleKeyDown"
          resize="none"
        />
        
        <div class="input-actions">
          <el-button 
            type="primary"
            @click="sendMessage"
            :disabled="!currentMessage.trim() || isConnecting || isTyping"
            :loading="isSending"
            class="send-button"
          >
            <el-icon><Promotion /></el-icon>
            Send
          </el-button>
        </div>
      </div>

      <!-- 连接状态 / Connection Status -->
      <div v-if="connectionStatus !== 'connected'" class="connection-status">
        <el-alert
          :title="getConnectionStatusText()"
          :type="connectionStatus === 'connecting' ? 'info' : 'error'"
          :closable="false"
          size="small"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AI聊天框组件
 * AI chat box component with WebSocket support
 */

import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { 
  ElButton, 
  ElInput, 
  ElIcon, 
  ElUpload, 
  ElText, 
  ElAlert,
  ElMessage
} from 'element-plus'
import {
  ChatRound,
  User,
  Robot,
  Tools,
  Delete,
  Upload,
  Download,
  DocumentChecked,
  Promotion
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// 消息接口 / Message interface
interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  downloadUrl?: string
  filename?: string
}

// Props定义 / Props definition
interface Props {
  messages?: ChatMessage[]
  isConnected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  messages: () => [],
  isConnected: false
})

// Emits定义 / Emits definition
const emit = defineEmits<{
  sendMessage: [content: string]
  uploadResume: [file: File]
  clearChat: []
  connect: []
  disconnect: []
}>()

// 响应式数据 / Reactive data
const currentMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const uploadRef = ref()
const uploadedFileName = ref('')
const isUploading = ref(false)
const isSending = ref(false)
const isTyping = ref(false)
const connectionStatus = ref<'connected' | 'connecting' | 'disconnected'>('disconnected')

// Markdown渲染器 / Markdown renderer
const md = new MarkdownIt({
  highlight: function (str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  }
})

// 方法 / Methods
/**
 * 渲染Markdown内容
 * Render Markdown content to HTML
 */
const renderMarkdown = (content: string): string => {
  return md.render(content)
}

/**
 * 格式化时间显示
 * Format time display
 */
const formatTime = (timestamp: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(timestamp)
}

/**
 * 发送消息
 * Send message
 */
const sendMessage = async () => {
  if (!currentMessage.value.trim()) return
  
  isSending.value = true
  try {
    emit('sendMessage', currentMessage.value)
    currentMessage.value = ''
    await scrollToBottom()
  } finally {
    isSending.value = false
  }
}

/**
 * 处理键盘事件
 * Handle keyboard events
 */
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    sendMessage()
  }
}

/**
 * 处理简历上传
 * Handle resume upload
 */
const handleResumeUpload = (file: File): boolean => {
  // 验证文件类型 / Validate file type
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]
  
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('Please upload PDF, DOC, or DOCX files only.')
    return false
  }

  // 验证文件大小 (最大10MB) / Validate file size (max 10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('File size must be less than 10MB.')
    return false
  }

  isUploading.value = true
  uploadedFileName.value = file.name
  
  try {
    emit('uploadResume', file)
    ElMessage.success(`Resume "${file.name}" uploaded successfully!`)
  } catch (error) {
    ElMessage.error('Failed to upload resume. Please try again.')
    uploadedFileName.value = ''
  } finally {
    isUploading.value = false
  }

  return false // 阻止自动上传 / Prevent auto upload
}

/**
 * 清除聊天记录
 * Clear chat history
 */
const handleClearChat = () => {
  emit('clearChat')
  uploadedFileName.value = ''
  ElMessage.success('Chat history cleared.')
}

/**
 * 下载文件
 * Download file
 */
const downloadFile = (url: string, filename?: string) => {
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'download'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * 滚动到底部
 * Scroll to bottom
 */
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

/**
 * 获取连接状态文本
 * Get connection status text
 */
const getConnectionStatusText = (): string => {
  switch (connectionStatus.value) {
    case 'connecting':
      return 'Connecting to AI assistant...'
    case 'disconnected':
      return 'Disconnected from AI assistant. Trying to reconnect...'
    default:
      return 'Connected'
  }
}

// 监听消息变化并滚动到底部 / Watch messages and scroll to bottom
watch(() => props.messages, () => {
  scrollToBottom()
}, { deep: true })

// 组件挂载时连接WebSocket / Connect WebSocket on mount
onMounted(() => {
  emit('connect')
  connectionStatus.value = 'connecting'
})

// 组件卸载时断开连接 / Disconnect on unmount
onUnmounted(() => {
  emit('disconnect')
})
</script>

<style scoped>
.chat-box {
  display: flex;
  flex-direction: column;
  height: 600px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
}

.header-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8f9fa;
}

.message {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.message-user .message-avatar {
  background: #409eff;
  color: white;
}

.message-assistant .message-avatar {
  background: #67c23a;
  color: white;
}

.message-system .message-avatar {
  background: #909399;
  color: white;
}

.message-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.message-role {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.message-content {
  margin-left: 40px;
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message-user .message-content {
  background: #409eff;
  color: white;
  margin-left: 40px;
  margin-right: 0;
}

.text-content {
  line-height: 1.6;
  white-space: pre-wrap;
}

.markdown-content {
  line-height: 1.6;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
}

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content :deep(code) {
  background: #f1f2f6;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
}

.markdown-content :deep(pre) {
  background: #f1f2f6;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.download-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.typing-indicator {
  margin-bottom: 16px;
}

.typing-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  animation: typing 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.input-area {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #f0f0f0;
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.message-input-section {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
}

.input-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.send-button {
  height: 76px;
  min-width: 80px;
}

.connection-status {
  margin-top: 8px;
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .chat-box {
    height: 500px;
  }
  
  .message-content {
    margin-left: 0;
    margin-top: 8px;
  }
  
  .message-input-section {
    flex-direction: column;
  }
  
  .send-button {
    height: 40px;
    width: 100%;
  }
}
</style> 