<template>
  <div class="home-container">
    <!-- 动态背景 / Dynamic Background -->
    <div class="background-animation">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
      </div>
    </div>

    <!-- 主要内容 / Main Content -->
    <div class="main-content">
      <!-- Logo和项目简介 / Logo and Project Introduction -->
      <div class="hero-section">
        <div class="logo-container">
          <h1 class="artistic-logo">🎯 JobCatcher</h1>
          <div class="logo-subtitle">AI-Powered Career Assistant</div>
        </div>
        
        <div class="project-intro">
          <p class="intro-text">
            Discover your perfect career match with our intelligent job search platform. 
            Upload your resume, get personalized job recommendations, and optimize your 
            career path with AI-driven insights.
          </p>
          
          <div class="feature-highlights">
            <div class="feature-item">
              <el-icon class="feature-icon"><Search /></el-icon>
              <span>Smart Job Search</span>
            </div>
            <div class="feature-item">
              <el-icon class="feature-icon"><Document /></el-icon>
              <span>Resume Analysis</span>
            </div>
            <div class="feature-item">
              <el-icon class="feature-icon"><TrendCharts /></el-icon>
              <span>Skills Visualization</span>
            </div>
            <div class="feature-item">
              <el-icon class="feature-icon"><Star /></el-icon>
              <span>AI Recommendations</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Google OAuth登录按钮 / Google OAuth Login Button -->
      <div class="auth-section">
        <el-button 
          v-if="!isAuthenticated"
          type="primary" 
          size="large"
          class="google-auth-button"
          @click="handleGoogleAuth"
          :loading="isLoading"
        >
          <el-icon class="auth-icon">
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </el-icon>
          Continue with Google
        </el-button>

        <el-button 
          v-else
          type="success" 
          size="large"
          class="continue-button"
          @click="navigateToApp"
        >
          <el-icon><ArrowRight /></el-icon>
          Continue to JobCatcher
        </el-button>

        <div class="auth-info">
          <el-text type="info" size="small">
            Sign in to access personalized job recommendations and resume analysis
          </el-text>
        </div>
      </div>
    </div>

    <!-- 页脚信息 / Footer Info -->
    <footer class="footer">
      <div class="footer-content">
        <el-text type="info" size="small">
          © 2025 JobCatcher - AI-Powered Career Assistant
        </el-text>
        <div class="footer-links">
          <el-text type="info" size="small">Privacy Policy</el-text>
          <el-text type="info" size="small">Terms of Service</el-text>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
/**
 * JobCatcher 首页组件
 * JobCatcher home page component with Google OAuth
 */

import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElButton, ElIcon, ElText, ElMessage } from 'element-plus'
import { 
  Search, 
  Document, 
  TrendCharts, 
  Star, 
  ArrowRight 
} from '@element-plus/icons-vue'

// 使用stores / Use stores
const userStore = useUserStore()
const router = useRouter()

// 响应式数据 / Reactive data
const isLoading = ref(false)

// 计算属性 / Computed properties
const isAuthenticated = computed(() => userStore.isAuthenticated)

// 方法 / Methods
/**
 * 处理Google OAuth登录
 * Handle Google OAuth login
 */
const handleGoogleAuth = async () => {
  isLoading.value = true
  
  try {
    // 使用userStore的loginWithGoogle方法 / Use userStore's loginWithGoogle method
    userStore.loginWithGoogle()
  } catch (error) {
    console.error('Google OAuth error:', error)
    ElMessage.error('Failed to initiate Google login. Please try again.')
    isLoading.value = false
  }
}

/**
 * 导航到主应用页面
 * Navigate to main application page
 */
const navigateToApp = () => {
  router.push('/app')
}

// 组件挂载时检查认证状态 / Check authentication status on mount
onMounted(() => {
  // 如果已经登录，提示用户 / If already logged in, prompt user
  if (isAuthenticated.value) {
    ElMessage.info('You are already logged in. Continue to the application.')
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 动态背景动画 / Dynamic background animation */
.background-animation {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;
}

.floating-shapes {
  position: relative;
  width: 100%;
  height: 100%;
}

.shape {
  position: absolute;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 60%;
  right: 15%;
  animation-delay: 1s;
}

.shape-3 {
  width: 60px;
  height: 60px;
  top: 30%;
  right: 25%;
  animation-delay: 2s;
}

.shape-4 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation-delay: 3s;
}

.shape-5 {
  width: 140px;
  height: 140px;
  top: 10%;
  left: 50%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.5;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.8;
  }
}

/* 主要内容 / Main content */
.main-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 800px;
  padding: 40px 20px;
  color: white;
}

.hero-section {
  margin-bottom: 40px;
}

.logo-container {
  margin-bottom: 32px;
}

.artistic-logo {
  font-size: 4rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(45deg, #fff, #f0f9ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: -2px;
}

.logo-subtitle {
  font-size: 1.2rem;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 8px;
  letter-spacing: 1px;
}

.project-intro {
  margin-bottom: 32px;
}

.intro-text {
  font-size: 1.1rem;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 24px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.feature-highlights {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-top: 32px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.feature-icon {
  font-size: 24px;
  color: #fff;
}

.feature-item span {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

/* 认证区域 / Authentication section */
.auth-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.google-auth-button,
.continue-button {
  height: 56px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 28px;
  padding: 0 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  border: none;
}

.google-auth-button {
  background: #fff;
  color: #333;
}

.google-auth-button:hover {
  background: #f8f9fa;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.continue-button {
  background: #67c23a;
  color: white;
}

.continue-button:hover {
  background: #5daf34;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(103, 194, 58, 0.4);
}

.auth-icon {
  margin-right: 8px;
}

.auth-info {
  max-width: 400px;
  text-align: center;
}

.auth-info .el-text {
  color: rgba(255, 255, 255, 0.8) !important;
}

/* 页脚 / Footer */
.footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1;
  padding: 20px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.footer-links {
  display: flex;
  gap: 16px;
}

.footer .el-text {
  color: rgba(255, 255, 255, 0.7) !important;
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .artistic-logo {
    font-size: 3rem;
  }
  
  .logo-subtitle {
    font-size: 1rem;
  }
  
  .intro-text {
    font-size: 1rem;
    padding: 0 16px;
  }
  
  .feature-highlights {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .main-content {
    padding: 20px 16px;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
  
  .footer-links {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .artistic-logo {
    font-size: 2.5rem;
  }
  
  .feature-highlights {
    grid-template-columns: 1fr;
  }
  
  .google-auth-button,
  .continue-button {
    width: 100%;
    max-width: 300px;
  }
}
</style> 