<template>
  <div class="heatmap-chart">
    <!-- 图表头部 / Chart Header -->
    <div class="chart-header">
      <h3 class="chart-title">
        <el-icon><TrendCharts /></el-icon>
        {{ title }}
      </h3>
      <div class="chart-controls">
        <!-- 图表类型切换 / Chart Type Toggle -->
        <el-radio-group v-model="chartType" @change="updateChart">
          <el-radio-button value="radar">Radar</el-radio-button>
          <el-radio-button value="bar">Bar Chart</el-radio-button>
          <el-radio-button value="doughnut">Doughnut</el-radio-button>
        </el-radio-group>
        
        <!-- 刷新按钮 / Refresh Button -->
        <el-button 
          size="small" 
          :icon="Refresh"
          @click="refreshChart"
          title="Refresh Chart"
        />
      </div>
    </div>

    <!-- 图表容器 / Chart Container -->
    <div class="chart-container" :class="{ loading: isLoading }">
      <div v-if="isLoading" class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>Generating chart...</span>
      </div>
      
      <canvas 
        v-show="!isLoading"
        ref="chartCanvas" 
        :width="chartWidth" 
        :height="chartHeight"
      ></canvas>
      
      <!-- 无数据提示 / No Data Message -->
      <div v-if="!isLoading && !hasData" class="no-data">
        <el-icon><DocumentRemove /></el-icon>
        <p>No skill data available</p>
        <el-text type="info" size="small">
          Upload your resume or search for jobs to see skill analysis
        </el-text>
      </div>
    </div>

    <!-- 图表说明 / Chart Legend -->
    <div v-if="hasData && !isLoading" class="chart-legend">
      <div class="legend-header">
        <h4>Skills Analysis</h4>
        <el-tag type="info" size="small">
          {{ skillData.length }} skills analyzed
        </el-tag>
      </div>
      
      <div class="legend-items">
        <div 
          v-for="(skill, index) in topSkills" 
          :key="skill.skill"
          class="legend-item"
        >
          <div 
            class="legend-color" 
            :style="{ backgroundColor: getColorForIndex(index) }"
          ></div>
          <span class="legend-skill">{{ skill.skill }}</span>
          <span class="legend-score">{{ Math.round(skill.score) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 技能热点图组件
 * Skills heatmap chart component using Chart.js
 */

import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElIcon, ElRadioGroup, ElRadioButton, ElButton, ElTag, ElText } from 'element-plus'
import { TrendCharts, Refresh, Loading, DocumentRemove } from '@element-plus/icons-vue'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title
} from 'chart.js'

// 注册Chart.js组件 / Register Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title
)

// 技能数据接口 / Skill data interface
interface SkillData {
  skill: string
  score: number // 0-100 范围 / 0-100 range
  category?: string
  demand?: 'high' | 'medium' | 'low'
}

// Props定义 / Props definition
interface Props {
  skillData?: SkillData[]
  title?: string
  width?: number
  height?: number
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  skillData: () => [],
  title: 'Skills Heatmap',
  width: 400,
  height: 300,
  isLoading: false
})

// Emits定义 / Emits definition
const emit = defineEmits<{
  refresh: []
  skillClick: [skill: SkillData]
}>()

// 响应式数据 / Reactive data
const chartCanvas = ref<HTMLCanvasElement>()
const chartInstance = ref<ChartJS | null>(null)
const chartType = ref<'radar' | 'bar' | 'doughnut'>('radar')

// 计算属性 / Computed properties
const hasData = computed(() => props.skillData.length > 0)

const chartWidth = computed(() => props.width)
const chartHeight = computed(() => props.height)

/**
 * 获取前10个技能数据
 * Get top 10 skills data
 */
const topSkills = computed(() => {
  return props.skillData
    .sort((a, b) => b.score - a.score)
    .slice(0, 10)
})

/**
 * 图表数据配置
 * Chart data configuration
 */
const chartData = computed(() => {
  const skills = topSkills.value
  const labels = skills.map(item => item.skill)
  const data = skills.map(item => item.score)
  const colors = skills.map((_, index) => getColorForIndex(index))

  if (chartType.value === 'radar') {
    return {
      labels,
      datasets: [{
        label: 'Skill Demand (%)',
        data,
        backgroundColor: 'rgba(64, 158, 255, 0.2)',
        borderColor: 'rgba(64, 158, 255, 1)',
        pointBackgroundColor: 'rgba(64, 158, 255, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(64, 158, 255, 1)',
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    }
  } else if (chartType.value === 'bar') {
    return {
      labels,
      datasets: [{
        label: 'Skill Demand (%)',
        data,
        backgroundColor: colors.map(color => color + '80'), // 添加透明度 / Add transparency
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false
      }]
    }
  } else { // doughnut
    return {
      labels,
      datasets: [{
        label: 'Skill Demand (%)',
        data,
        backgroundColor: colors.map(color => color + '80'),
        borderColor: colors,
        borderWidth: 2,
        hoverOffset: 4
      }]
    }
  }
})

/**
 * 图表配置选项
 * Chart configuration options
 */
const chartOptions = computed(() => {
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: false
      },
      legend: {
        display: chartType.value === 'doughnut',
        position: 'bottom' as const,
        labels: {
          padding: 20,
          usePointStyle: true
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const skill = topSkills.value[context.dataIndex]
            return `${skill.skill}: ${skill.score}% demand`
          }
        }
      }
    },
    onClick: (event: any, elements: any[]) => {
      if (elements.length > 0) {
        const index = elements[0].index
        const skill = topSkills.value[index]
        emit('skillClick', skill)
      }
    }
  }

  if (chartType.value === 'radar') {
    return {
      ...baseOptions,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
            callback: function(value: any) {
              return value + '%'
            }
          },
          pointLabels: {
            font: {
              size: 12
            }
          }
        }
      }
    }
  } else if (chartType.value === 'bar') {
    return {
      ...baseOptions,
      indexAxis: 'y' as const,
      scales: {
        x: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value: any) {
              return value + '%'
            }
          }
        },
        y: {
          ticks: {
            font: {
              size: 11
            }
          }
        }
      }
    }
  } else {
    return baseOptions
  }
})

// 方法 / Methods
/**
 * 根据索引获取颜色
 * Get color based on index
 */
const getColorForIndex = (index: number): string => {
  const colors = [
    '#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399',
    '#c71585', '#ff6347', '#32cd32', '#00ced1', '#ff1493'
  ]
  return colors[index % colors.length]
}

/**
 * 初始化图表
 * Initialize chart
 */
const initChart = async () => {
  await nextTick()
  if (!chartCanvas.value || !hasData.value) return

  destroyChart()

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  try {
    chartInstance.value = new ChartJS(ctx, {
      type: chartType.value,
      data: chartData.value,
      options: chartOptions.value
    })
  } catch (error) {
    console.error('Failed to create chart:', error)
  }
}

/**
 * 更新图表
 * Update chart
 */
const updateChart = async () => {
  await nextTick()
  if (chartInstance.value) {
    chartInstance.value.destroy()
  }
  await initChart()
}

/**
 * 销毁图表
 * Destroy chart
 */
const destroyChart = () => {
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }
}

/**
 * 刷新图表
 * Refresh chart
 */
const refreshChart = () => {
  emit('refresh')
}

/**
 * 重置图表大小
 * Resize chart
 */
const resizeChart = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 监听数据变化 / Watch data changes
watch(() => props.skillData, async () => {
  if (hasData.value) {
    await updateChart()
  } else {
    destroyChart()
  }
}, { deep: true })

watch(() => props.isLoading, (newVal) => {
  if (!newVal && hasData.value) {
    initChart()
  }
})

// 组件挂载 / Component mounted
onMounted(() => {
  if (hasData.value && !props.isLoading) {
    initChart()
  }
  
  // 监听窗口大小变化 / Listen to window resize
  window.addEventListener('resize', resizeChart)
})

// 组件卸载 / Component unmounted
onUnmounted(() => {
  destroyChart()
  window.removeEventListener('resize', resizeChart)
})
</script>

<style scoped>
.heatmap-chart {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.chart-title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-container {
  position: relative;
  padding: 20px;
  min-height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container.loading {
  background: #f8f9fa;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #909399;
}

.loading-icon {
  font-size: 32px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #909399;
  text-align: center;
}

.no-data .el-icon {
  font-size: 48px;
  color: #dcdfe6;
}

.no-data p {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.chart-legend {
  padding: 16px 20px;
  background: #f8f9fa;
  border-top: 1px solid #f0f0f0;
}

.legend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.legend-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.legend-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.legend-item:hover {
  background: rgba(64, 158, 255, 0.1);
  cursor: pointer;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-skill {
  flex: 1;
  font-size: 12px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legend-score {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  flex-shrink: 0;
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .chart-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .chart-container {
    min-height: 300px;
    padding: 16px;
  }
  
  .legend-items {
    grid-template-columns: 1fr;
  }
}
</style> 