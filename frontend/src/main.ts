/**
 * JobCatcher 前端应用主入口
 * Main entry point for JobCatcher frontend application
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Element Plus 样式 / Element Plus styles
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

// Chart.js 必要的组件 / Chart.js necessary components
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  ArcElement
} from 'chart.js'

// 注册Chart.js组件 / Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  ArcElement
)

// 全局样式 / Global styles
import './styles/index.css'

// 创建Vue应用实例 / Create Vue app instance
const app = createApp(App)

// 使用Pinia状态管理 / Use Pinia for state management
const pinia = createPinia()
app.use(pinia)

// 使用Vue Router路由 / Use Vue Router
app.use(router)

// 挂载应用 / Mount the app
app.mount('#app')

// 控制台输出应用信息 / Console output app info
console.log(`🚀 JobCatcher v1.0.0 - ${import.meta.env.MODE} mode`)
console.log('📧 Support: support@jobcatcher.ai') 