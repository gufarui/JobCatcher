/**
 * 应用全局状态管理
 * Global application state management store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AppTheme {
  mode: 'light' | 'dark' | 'auto'
  primaryColor: string
}

export interface AppSettings {
  language: 'zh-CN' | 'en-US'
  theme: AppTheme
  sidebarCollapsed: boolean
  showNotifications: boolean
  autoSave: boolean
}

export const useAppStore = defineStore('app', () => {
  // 状态 / State
  const isGlobalLoading = ref(false)
  const isSidebarCollapsed = ref(false)
  const currentTheme = ref<'light' | 'dark' | 'auto'>('auto')
  const language = ref<'zh-CN' | 'en-US'>('zh-CN')
  const settings = ref<AppSettings>({
    language: 'zh-CN',
    theme: {
      mode: 'auto',
      primaryColor: '#409eff'
    },
    sidebarCollapsed: false,
    showNotifications: true,
    autoSave: true
  })

  // 网络状态 / Network status
  const isOnline = ref(navigator.onLine)
  const lastSyncTime = ref<Date | null>(null)

  // 计算属性 / Computed
  const isDarkMode = computed(() => {
    if (settings.value.theme.mode === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return settings.value.theme.mode === 'dark'
  })

  const isDesktop = computed(() => window.innerWidth >= 1024)
  const isMobile = computed(() => window.innerWidth < 768)
  const isTablet = computed(() => window.innerWidth >= 768 && window.innerWidth < 1024)

  // 操作 / Actions

  /**
   * 初始化应用设置 / Initialize app settings
   */
  const initializeApp = async () => {
    try {
      isGlobalLoading.value = true

      // 从localStorage加载设置 / Load settings from localStorage
      const savedSettings = localStorage.getItem('jobcatcher_settings')
      if (savedSettings) {
        settings.value = { ...settings.value, ...JSON.parse(savedSettings) }
      }

      // 应用主题 / Apply theme
      applyTheme()

      // 监听系统主题变化 / Listen for system theme changes
      if (settings.value.theme.mode === 'auto') {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme)
      }

      // 监听网络状态 / Listen for network status
      window.addEventListener('online', () => {
        isOnline.value = true
        ElMessage.success('网络连接已恢复')
      })

      window.addEventListener('offline', () => {
        isOnline.value = false
        ElMessage.warning('网络连接已断开')
      })

      // 更新最后同步时间 / Update last sync time
      lastSyncTime.value = new Date()

    } catch (error) {
      console.error('App initialization failed:', error)
      ElMessage.error('应用初始化失败')
    } finally {
      isGlobalLoading.value = false
    }
  }

  /**
   * 应用主题 / Apply theme
   */
  const applyTheme = () => {
    const html = document.documentElement
    
    if (isDarkMode.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }

    // 设置主题色 / Set primary color
    html.style.setProperty('--el-color-primary', settings.value.theme.primaryColor)
  }

  /**
   * 切换主题模式 / Toggle theme mode
   */
  const toggleTheme = (mode?: 'light' | 'dark' | 'auto') => {
    if (mode) {
      settings.value.theme.mode = mode
    } else {
      const modes: Array<'light' | 'dark' | 'auto'> = ['light', 'dark', 'auto']
      const currentIndex = modes.indexOf(settings.value.theme.mode)
      const nextIndex = (currentIndex + 1) % modes.length
      settings.value.theme.mode = modes[nextIndex]
    }
    
    applyTheme()
    saveSettings()
  }

  /**
   * 设置主题色 / Set primary color
   */
  const setPrimaryColor = (color: string) => {
    settings.value.theme.primaryColor = color
    applyTheme()
    saveSettings()
  }

  /**
   * 切换侧边栏状态 / Toggle sidebar state
   */
  const toggleSidebar = () => {
    settings.value.sidebarCollapsed = !settings.value.sidebarCollapsed
    isSidebarCollapsed.value = settings.value.sidebarCollapsed
    saveSettings()
  }

  /**
   * 设置语言 / Set language
   */
  const setLanguage = (lang: 'zh-CN' | 'en-US') => {
    settings.value.language = lang
    language.value = lang
    saveSettings()
  }

  /**
   * 显示全局加载状态 / Show global loading
   */
  const showGlobalLoading = (show = true) => {
    isGlobalLoading.value = show
  }

  /**
   * 保存设置到localStorage / Save settings to localStorage
   */
  const saveSettings = () => {
    try {
      localStorage.setItem('jobcatcher_settings', JSON.stringify(settings.value))
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
  }

  /**
   * 重置设置 / Reset settings
   */
  const resetSettings = () => {
    settings.value = {
      language: 'zh-CN',
      theme: {
        mode: 'auto',
        primaryColor: '#409eff'
      },
      sidebarCollapsed: false,
      showNotifications: true,
      autoSave: true
    }
    
    applyTheme()
    saveSettings()
    ElMessage.success('设置已重置')
  }

  /**
   * 更新最后同步时间 / Update last sync time
   */
  const updateSyncTime = () => {
    lastSyncTime.value = new Date()
  }

  /**
   * 检查更新 / Check for updates
   */
  const checkForUpdates = async () => {
    try {
      // 这里可以实现版本检查逻辑 / Version check logic can be implemented here
      console.log('Checking for updates...')
      
      // 模拟检查更新 / Simulate update check
      const hasUpdate = false // 实际应该从API获取 / Should fetch from API
      
      if (hasUpdate) {
        ElMessage.info('发现新版本，请刷新页面更新')
      }
      
      return hasUpdate
    } catch (error) {
      console.error('Update check failed:', error)
      return false
    }
  }

  return {
    // 状态 / State
    isGlobalLoading: readonly(isGlobalLoading),
    isSidebarCollapsed: readonly(isSidebarCollapsed),
    currentTheme: readonly(currentTheme),
    language: readonly(language),
    settings: readonly(settings),
    isOnline: readonly(isOnline),
    lastSyncTime: readonly(lastSyncTime),

    // 计算属性 / Computed
    isDarkMode,
    isDesktop,
    isMobile,
    isTablet,

    // 操作 / Actions
    initializeApp,
    toggleTheme,
    setPrimaryColor,
    toggleSidebar,
    setLanguage,
    showGlobalLoading,
    saveSettings,
    resetSettings,
    updateSyncTime,
    checkForUpdates
  }
}) 