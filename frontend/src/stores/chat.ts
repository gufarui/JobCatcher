/**
 * 聊天管理状态存储
 * Chat management state store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// 类型定义 / Type definitions
interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    type?: 'text' | 'file' | 'recommendation' | 'heatmap'
    file_url?: string
    file_name?: string
    recommendations?: any[]
    heatmap_data?: any
  }
}

interface WebSocketMessage {
  type: 'message' | 'error' | 'status'
  role?: 'user' | 'assistant' | 'system'
  content?: string
  metadata?: any
  error?: string
  status?: string
}

export const useChatStore = defineStore('chat', () => {
  // 状态 / State
  const messages = ref<ChatMessage[]>([])
  const isConnected = ref(false)
  const isLoading = ref(false)
  const currentSessionId = ref<string | null>(null)
  const websocket = ref<WebSocket | null>(null)
  const connectionRetries = ref(0)
  const maxRetries = 3

  // 计算属性 / Computed properties
  const messageCount = computed(() => messages.value.length)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])
  const hasMessages = computed(() => messages.value.length > 0)

  // WebSocket连接管理 / WebSocket connection management
  const connectWebSocket = () => {
    try {
      // 构建WebSocket URL / Build WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/api/chat/ws`
      
      websocket.value = new WebSocket(wsUrl)
      
      websocket.value.onopen = () => {
        console.log('WebSocket connected')
        isConnected.value = true
        connectionRetries.value = 0
      }
      
      websocket.value.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      websocket.value.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        isConnected.value = false
        
        // 自动重连 / Auto reconnect
        if (connectionRetries.value < maxRetries) {
          connectionRetries.value++
          setTimeout(() => {
            console.log(`Attempting to reconnect... (${connectionRetries.value}/${maxRetries})`)
            connectWebSocket()
          }, 2000 * connectionRetries.value)
        }
      }
      
      websocket.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        isConnected.value = false
      }
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  }

  // 处理WebSocket消息 / Handle WebSocket message
  const handleWebSocketMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case 'message':
        if (data.role && data.content) {
          addMessage({
            id: Date.now().toString(),
            role: data.role,
            content: data.content,
            timestamp: new Date(),
            metadata: data.metadata
          })
        }
        break
      case 'error':
        console.error('WebSocket error message:', data.error)
        // 可以添加错误消息到聊天历史 / Can add error message to chat history
        addMessage({
          id: Date.now().toString(),
          role: 'system',
          content: `Error: ${data.error}`,
          timestamp: new Date()
        })
        break
      case 'status':
        console.log('WebSocket status:', data.status)
        break
    }
  }

  // 发送消息 / Send message
  const sendMessage = async (content: string): Promise<string> => {
    if (!content.trim()) {
      throw new Error('Message content cannot be empty')
    }

    try {
      isLoading.value = true
      
      // 添加用户消息到本地历史 / Add user message to local history
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date()
      }
      addMessage(userMessage)
      
      // 通过WebSocket发送消息 / Send message via WebSocket
      if (websocket.value && isConnected.value) {
        const wsMessage: WebSocketMessage = {
          type: 'message',
          role: 'user',
          content: content.trim()
        }
        websocket.value.send(JSON.stringify(wsMessage))
        
        // WebSocket会处理AI回复 / WebSocket will handle AI response
        return 'Message sent via WebSocket'
      } else {
        // 回退到HTTP API / Fallback to HTTP API
        const response = await axios.post('/api/chat/message', {
          content: content.trim(),
          session_id: currentSessionId.value
        })
        
        const aiResponse = response.data.content || 'No response received'
        
        // 添加AI回复到历史 / Add AI response to history
        addMessage({
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: aiResponse,
          timestamp: new Date(),
          metadata: response.data.metadata
        })
        
        return aiResponse
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      throw new Error('Failed to send message. Please try again.')
    } finally {
      isLoading.value = false
    }
  }

  // 添加消息到历史 / Add message to history
  const addMessage = (message: ChatMessage) => {
    messages.value.push(message)
    // 自动保存到本地存储 / Auto save to local storage
    saveMessagesToStorage()
  }

  // 清除聊天记录 / Clear chat history
  const clearChat = async () => {
    try {
      // 调用后端API清除服务器端聊天历史 / Call backend API to clear server-side chat history
      await axios.delete('/api/chat/clear')
      
      // 清除本地聊天历史 / Clear local chat history
      messages.value = []
      currentSessionId.value = null
      
      // 清除本地存储 / Clear local storage
      localStorage.removeItem('chat_messages')
      localStorage.removeItem('chat_session_id')
      
    } catch (error) {
      console.error('Failed to clear chat:', error)
      throw new Error('Failed to clear chat history')
    }
  }

  // 加载聊天历史 / Load chat history
  const loadChatHistory = async (): Promise<ChatMessage[]> => {
    try {
      // 首先尝试从服务器加载 / First try to load from server
      const response = await axios.get('/api/chat/history')
      const serverMessages = response.data.messages || []
      
      if (serverMessages.length > 0) {
        messages.value = serverMessages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
        currentSessionId.value = response.data.session_id
      } else {
        // 从本地存储加载 / Load from local storage
        loadMessagesFromStorage()
      }
      
      return messages.value
    } catch (error) {
      console.error('Failed to load chat history from server:', error)
      // 回退到本地存储 / Fallback to local storage
      loadMessagesFromStorage()
      return messages.value
    }
  }

  // 保存消息到本地存储 / Save messages to local storage
  const saveMessagesToStorage = () => {
    try {
      localStorage.setItem('chat_messages', JSON.stringify(messages.value))
      if (currentSessionId.value) {
        localStorage.setItem('chat_session_id', currentSessionId.value)
      }
    } catch (error) {
      console.error('Failed to save messages to storage:', error)
    }
  }

  // 从本地存储加载消息 / Load messages from local storage
  const loadMessagesFromStorage = () => {
    try {
      const saved = localStorage.getItem('chat_messages')
      if (saved) {
        const parsedMessages = JSON.parse(saved)
        messages.value = parsedMessages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }
      
      const savedSessionId = localStorage.getItem('chat_session_id')
      if (savedSessionId) {
        currentSessionId.value = savedSessionId
      }
    } catch (error) {
      console.error('Failed to load messages from storage:', error)
      messages.value = []
    }
  }

  // 断开WebSocket连接 / Disconnect WebSocket
  const disconnectWebSocket = () => {
    if (websocket.value) {
      websocket.value.close()
      websocket.value = null
    }
    isConnected.value = false
  }

  // 重连WebSocket / Reconnect WebSocket
  const reconnectWebSocket = () => {
    disconnectWebSocket()
    connectionRetries.value = 0
    connectWebSocket()
  }

  // 发送系统消息 / Send system message
  const addSystemMessage = (content: string, metadata?: any) => {
    addMessage({
      id: Date.now().toString(),
      role: 'system',
      content,
      timestamp: new Date(),
      metadata
    })
  }

  // 删除特定消息 / Delete specific message
  const deleteMessage = (messageId: string) => {
    const index = messages.value.findIndex(msg => msg.id === messageId)
    if (index !== -1) {
      messages.value.splice(index, 1)
      saveMessagesToStorage()
    }
  }

  // 重置状态 / Reset state
  const reset = () => {
    messages.value = []
    isConnected.value = false
    isLoading.value = false
    currentSessionId.value = null
    connectionRetries.value = 0
    disconnectWebSocket()
  }

  // 初始化store / Initialize store
  const initialize = () => {
    loadMessagesFromStorage()
    connectWebSocket()
  }

  // 销毁store / Destroy store
  const destroy = () => {
    disconnectWebSocket()
    reset()
  }

  return {
    // 状态 / State
    messages,
    isConnected,
    isLoading,
    currentSessionId,
    connectionRetries,
    
    // 计算属性 / Computed properties
    messageCount,
    lastMessage,
    hasMessages,
    
    // 行为 / Actions
    sendMessage,
    addMessage,
    clearChat,
    loadChatHistory,
    connectWebSocket,
    disconnectWebSocket,
    reconnectWebSocket,
    addSystemMessage,
    deleteMessage,
    reset,
    initialize,
    destroy
  }
}) 