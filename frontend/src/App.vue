<template>
  <div id="app" class="app-container">
    <!-- 全局加载指示器 / Global loading indicator -->
    <el-loading 
      v-loading="isGlobalLoading" 
      fullscreen 
      text="加载中..."
      background="rgba(0, 0, 0, 0.7)"
    />
    
    <!-- 路由视图 / Router view -->
    <router-view v-slot="{ Component, route }">
      <transition 
        :name="route.meta.transition || 'fade'" 
        mode="out-in"
        appear
      >
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
    
    <!-- 全局消息通知容器 / Global message notification container -->
    <teleport to="body">
      <div id="message-container" />
    </teleport>
  </div>
</template>

<script setup lang="ts">
/**
 * JobCatcher 主应用组件
 * Main application component for JobCatcher
 */

import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { storeToRefs } from 'pinia'

// 使用store / Use stores
const userStore = useUserStore()
const appStore = useAppStore()
const router = useRouter()

// 获取响应式状态 / Get reactive state
const { isGlobalLoading } = storeToRefs(appStore)

// 监听路由变化，更新页面标题 / Watch route changes to update page title
watch(() => router.currentRoute.value, (to) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - JobCatcher`
  } else {
    document.title = 'JobCatcher - AI求职助手'
  }
}, { immediate: true })

// 应用初始化 / App initialization
onMounted(async () => {
  try {
    // 检查用户登录状态 / Check user authentication status
    await userStore.checkAuthStatus()
    
    // 初始化应用设置 / Initialize app settings
    await appStore.initializeApp()
  } catch (error) {
    console.error('App initialization error:', error)
  }
})
</script>

<style lang="css">
/* 全局样式 / Global styles */
.app-container {
  min-height: 100vh;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: var(--el-bg-color-page);
  color: var(--el-text-color-primary);
}

/* 路由过渡动画 / Route transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(100%);
}

.slide-left-leave-to {
  transform: translateX(-100%);
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s ease;
}

.slide-right-enter-from {
  transform: translateX(-100%);
}

.slide-right-leave-to {
  transform: translateX(100%);
}

/* 自定义滚动条 / Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--el-bg-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-darker);
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .app-container {
    font-size: 14px;
  }
}
</style> 