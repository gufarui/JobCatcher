<template>
  <div class="not-found">
    <div class="not-found-container">
      <!-- 404图标和动画 / 404 icon and animation -->
      <div class="error-visual">
        <div class="error-code">404</div>
        <div class="error-animation">
          <div class="magnifier">
            <el-icon size="40">
              <Search />
            </el-icon>
          </div>
        </div>
      </div>
      
      <!-- 错误信息 / Error message -->
      <div class="error-content">
        <h1>Page Not Found</h1>
        <p>The page you are looking for doesn't exist or has been moved.</p>
        
        <!-- 建议链接 / Suggested links -->
        <div class="suggestions">
          <h3>Maybe you were looking for:</h3>
          <div class="suggestion-buttons">
            <el-button 
              type="primary" 
              size="large"
              @click="goHome"
            >
              <el-icon><House /></el-icon>
              Go Home
            </el-button>
            
            <el-button 
              v-if="userStore.isAuthenticated"
              type="default" 
              size="large"
              @click="goToApp"
            >
              <el-icon><Suitcase /></el-icon>
              Job Search
            </el-button>
            
            <el-button 
              type="default" 
              size="large"
              @click="goBack"
            >
              <el-icon><ArrowLeft /></el-icon>
              Go Back
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 装饰性背景 / Decorative background -->
    <div class="background-decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 404错误页面
 * 404 Not Found page
 */

import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElButton, ElIcon } from 'element-plus'
import { Search, House, Suitcase, ArrowLeft } from '@element-plus/icons-vue'

// 使用组合式API / Use Composition API
const router = useRouter()
const userStore = useUserStore()

/**
 * 返回首页
 * Go to home page
 */
const goHome = () => {
  router.push('/')
}

/**
 * 前往应用主页
 * Go to main application
 */
const goToApp = () => {
  router.push('/app')
}

/**
 * 返回上一页
 * Go back to previous page
 */
const goBack = () => {
  // 检查是否有历史记录 / Check if there's history
  if (window.history.length > 1) {
    router.back()
  } else {
    // 如果没有历史记录，返回首页 / If no history, go to home
    goHome()
  }
}
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.not-found-container {
  background: white;
  border-radius: 20px;
  padding: 60px 40px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  width: 100%;
  position: relative;
  z-index: 2;
}

/* 404视觉效果 / 404 visual effects */
.error-visual {
  position: relative;
  margin-bottom: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: 900;
  color: #e6e8eb;
  line-height: 1;
  margin-bottom: 20px;
  position: relative;
}

.error-animation {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.magnifier {
  width: 80px;
  height: 80px;
  border: 3px solid #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

/* 错误内容 / Error content */
.error-content h1 {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 16px 0;
}

.error-content p {
  font-size: 18px;
  color: #606266;
  margin: 0 0 40px 0;
  line-height: 1.6;
}

/* 建议部分 / Suggestions section */
.suggestions h3 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 24px 0;
}

.suggestion-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.suggestion-buttons .el-button {
  padding: 16px 24px;
  font-size: 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 装饰性背景 / Decorative background */
.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(64, 158, 255, 0.1), rgba(103, 194, 58, 0.1));
  animation: floatRandom 8s ease-in-out infinite;
}

.shape-1 {
  width: 100px;
  height: 100px;
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.shape-3 {
  width: 80px;
  height: 80px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

@keyframes floatRandom {
  0%, 100% { 
    transform: translateY(0px) rotate(0deg); 
    opacity: 0.3;
  }
  33% { 
    transform: translateY(-20px) rotate(120deg); 
    opacity: 0.6;
  }
  66% { 
    transform: translateY(10px) rotate(240deg); 
    opacity: 0.4;
  }
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .not-found-container {
    padding: 40px 20px;
    margin: 20px;
  }
  
  .error-code {
    font-size: 80px;
  }
  
  .magnifier {
    width: 60px;
    height: 60px;
  }
  
  .error-content h1 {
    font-size: 24px;
  }
  
  .error-content p {
    font-size: 16px;
  }
  
  .suggestions h3 {
    font-size: 18px;
  }
  
  .suggestion-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .suggestion-buttons .el-button {
    width: 100%;
    max-width: 200px;
  }
}

@media (max-width: 480px) {
  .error-code {
    font-size: 60px;
  }
  
  .error-content h1 {
    font-size: 20px;
  }
  
  .error-content p {
    font-size: 14px;
  }
}
</style> 