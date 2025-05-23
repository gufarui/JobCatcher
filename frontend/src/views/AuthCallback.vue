<template>
  <div class="auth-callback">
    <div class="callback-container">
      <!-- 加载状态 / Loading state -->
      <div v-if="isProcessing" class="loading-section">
        <el-icon class="loading-icon" size="64">
          <Loading />
        </el-icon>
        <h2>Processing login...</h2>
        <p>Please wait while we complete your authentication.</p>
      </div>
      
      <!-- 错误状态 / Error state -->
      <div v-else-if="error" class="error-section">
        <el-icon size="64" color="#f56c6c">
          <WarningFilled />
        </el-icon>
        <h2>Authentication Failed</h2>
        <p>{{ error }}</p>
        <el-button type="primary" @click="goHome">
          Return to Home
        </el-button>
      </div>
      
      <!-- 成功状态 / Success state -->
      <div v-else class="success-section">
        <el-icon size="64" color="#67c23a">
          <SuccessFilled />
        </el-icon>
        <h2>Login Successful!</h2>
        <p>Redirecting to your dashboard...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * OAuth认证回调页面
 * OAuth authentication callback page
 */

import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElIcon, ElButton, ElMessage } from 'element-plus'
import { Loading, WarningFilled, SuccessFilled } from '@element-plus/icons-vue'

// 使用组合式API / Use Composition API
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 响应式状态 / Reactive state
const isProcessing = ref(true)
const error = ref('')

/**
 * 处理OAuth回调
 * Handle OAuth callback
 */
const handleAuthCallback = async () => {
  try {
    const code = route.query.code as string
    const state = route.query.state as string
    const errorParam = route.query.error as string

    // 检查是否有错误参数 / Check for error parameter
    if (errorParam) {
      throw new Error(`OAuth error: ${errorParam}`)
    }

    // 检查是否有授权码 / Check for authorization code
    if (!code) {
      throw new Error('Authorization code not found')
    }

    // 验证state参数 (CSRF保护) / Validate state parameter (CSRF protection)
    const savedState = sessionStorage.getItem('oauth_state')
    if (state !== savedState) {
      throw new Error('Invalid state parameter - possible CSRF attack')
    }

    // 调用store处理OAuth回调 / Call store to handle OAuth callback
    const success = await userStore.handleOAuthCallback(code)
    
    if (success) {
      // 登录成功，等待2秒后跳转 / Login successful, redirect after 2 seconds
      setTimeout(() => {
        router.replace('/app')
      }, 2000)
    } else {
      throw new Error('Login failed - please try again')
    }

  } catch (err: any) {
    console.error('OAuth callback error:', err)
    error.value = err.message || 'Authentication failed'
    ElMessage.error(error.value)
  } finally {
    isProcessing.value = false
    // 清理sessionStorage / Clean up sessionStorage
    sessionStorage.removeItem('oauth_state')
  }
}

/**
 * 返回首页
 * Return to home page
 */
const goHome = () => {
  router.replace('/')
}

// 组件挂载时处理回调 / Handle callback on component mount
onMounted(() => {
  handleAuthCallback()
})
</script>

<style scoped>
.auth-callback {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.callback-container {
  background: white;
  border-radius: 16px;
  padding: 60px 40px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 100%;
}

.loading-section,
.error-section,
.success-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.loading-icon {
  animation: rotate 2s linear infinite;
  color: #409eff;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

p {
  margin: 0;
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
}

.error-section .el-button {
  margin-top: 10px;
  padding: 12px 30px;
  font-size: 16px;
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .callback-container {
    padding: 40px 20px;
    margin: 20px;
  }
  
  h2 {
    font-size: 24px;
  }
  
  p {
    font-size: 14px;
  }
}
</style> 