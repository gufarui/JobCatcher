/**
 * Vue Router 配置
 * Vue Router configuration for JobCatcher
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 路由元信息类型定义 / Route meta type definition
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    hideInMenu?: boolean
    transition?: string
  }
}

// 路由配置 / Route configuration
const routes: RouteRecordRaw[] = [
  // 首页 / Home page
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: {
      title: '首页',
      transition: 'fade'
    }
  },
  
  // OAuth回调页面 / OAuth callback page
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('@/views/AuthCallback.vue'),
    meta: {
      title: '登录验证',
      hideInMenu: true
    }
  },
  
  // 主应用页面 / Main application page
  {
    path: '/app',
    name: 'App',
    component: () => import('@/views/AppMain.vue'),
    meta: {
      title: '求职助手',
      requiresAuth: true,
      transition: 'slide-left'
    }
  },
  
  // 404错误页面 / 404 error page
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面未找到',
      hideInMenu: true
    }
  }
]

// 创建路由实例 / Create router instance
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  // 滚动行为 / Scroll behavior
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局前置守卫 / Global before guard
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 检查是否需要身份验证 / Check if authentication is required
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    // 未登录用户重定向到首页 / Redirect unauthenticated users to home
    ElMessage.warning('请先登录')
    next({ name: 'Home' })
    return
  }
  
  // 已登录用户访问首页时重定向到应用 / Redirect authenticated users from home to app
  if (to.name === 'Home' && userStore.isAuthenticated) {
    next({ name: 'App' })
    return
  }
  
  next()
})

// 全局后置钩子 / Global after hook
router.afterEach((to) => {
  // 页面加载完成后的逻辑 / Logic after page load
  console.log(`Navigated to: ${to.path}`)
})

export default router 