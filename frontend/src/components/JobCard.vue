<template>
  <div class="job-card-wrapper">
    <el-card 
      class="job-card" 
      :class="{ 'highlighted': job.isRecommended }"
      shadow="hover"
      @click="handleCardClick"
    >
      <!-- 卡片头部 / Card Header -->
      <div class="job-header">
        <div class="job-title-section">
          <h3 class="job-title">{{ job.title }}</h3>
          <el-tag 
            v-if="job.isRecommended" 
            type="success" 
            size="small"
            class="recommended-tag"
          >
            <el-icon><Star /></el-icon>
            Recommended
          </el-tag>
        </div>
        <div class="job-source">
          <el-tag 
            :type="getSourceTagType(job.source)" 
            size="small"
          >
            {{ formatJobSource(job.source) }}
          </el-tag>
        </div>
      </div>

      <!-- 公司和基本信息 / Company and Basic Info -->
      <div class="job-info">
        <div class="job-info-item">
          <el-icon class="info-icon"><OfficeBuilding /></el-icon>
          <span class="company-name">{{ job.company }}</span>
        </div>
        
        <div class="job-info-item">
          <el-icon class="info-icon"><Location /></el-icon>
          <span>{{ job.location }}</span>
        </div>
        
        <div v-if="job.salary" class="job-info-item">
          <el-icon class="info-icon"><Money /></el-icon>
          <span class="salary">{{ job.salary }}</span>
        </div>

        <div v-if="job.jobType" class="job-info-item">
          <el-icon class="info-icon"><Clock /></el-icon>
          <span>{{ job.jobType }}</span>
        </div>
      </div>

      <!-- 职位匹配度 / Job Match Score -->
      <div v-if="job.matchScore !== undefined" class="match-score">
        <div class="match-label">Match Score:</div>
        <el-progress 
          :percentage="Math.round(job.matchScore * 100)" 
          :color="getScoreColor(job.matchScore)"
          :stroke-width="8"
          class="score-progress"
        />
      </div>

      <!-- 折叠式工作描述 / Collapsible Job Description -->
      <div class="job-description">
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="Job Description" name="description">
            <div 
              class="description-content" 
              v-html="formatDescription(job.description)"
            ></div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 卡片操作 / Card Actions -->
      <div class="job-actions">
        <el-button 
          type="primary" 
          size="small"
          @click.stop="openJobLink"
          :icon="Link"
        >
          View Original
        </el-button>
        <el-button 
          v-if="job.isRecommended"
          type="success" 
          size="small"
          @click.stop="$emit('analyze', job)"
          :icon="TrendCharts"
        >
          Analyze Match
        </el-button>
      </div>

      <!-- 过期标识 / Expired Indicator -->
      <div v-if="job.expired" class="expired-overlay">
        <el-tag type="danger" size="large">
          <el-icon><Warning /></el-icon>
          Expired
        </el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
/**
 * 职位卡片组件
 * Job card component for displaying job information
 */

import { ref, computed } from 'vue'
import { 
  ElCard, 
  ElTag, 
  ElIcon, 
  ElButton, 
  ElCollapse, 
  ElCollapseItem, 
  ElProgress 
} from 'element-plus'
import {
  Star,
  OfficeBuilding,
  Location,
  Money,
  Clock,
  Link,
  TrendCharts,
  Warning
} from '@element-plus/icons-vue'

// 职位数据接口 / Job data interface
interface JobData {
  id: string
  title: string
  company: string
  location: string
  salary?: string
  jobType?: string
  source: 'stepstone' | 'google' | 'jobspikr' | 'coresignal'
  url: string
  description: string
  expired?: boolean
  isRecommended?: boolean
  matchScore?: number // 0-1 范围 / 0-1 range
}

// Props定义 / Props definition
interface Props {
  job: JobData
}

const props = defineProps<Props>()

// Emits定义 / Emits definition
const emit = defineEmits<{
  click: [job: JobData]
  analyze: [job: JobData]
}>()

// 响应式数据 / Reactive data
const activeCollapse = ref<string[]>([])

// 计算属性 / Computed properties
/**
 * 根据来源获取标签类型
 * Get tag type based on job source
 */
const getSourceTagType = (source: string) => {
  const typeMap: Record<string, string> = {
    stepstone: 'primary',
    google: 'success',
    jobspikr: 'warning',
    coresignal: 'info'
  }
  return typeMap[source] || 'info'
}

/**
 * 格式化职位来源显示
 * Format job source display
 */
const formatJobSource = (source: string) => {
  const sourceMap: Record<string, string> = {
    stepstone: 'StepStone',
    google: 'Google Jobs',
    jobspikr: 'JobsPikr',
    coresignal: 'CoreSignal'
  }
  return sourceMap[source] || source.toUpperCase()
}

/**
 * 根据匹配度获取进度条颜色
 * Get progress bar color based on match score
 */
const getScoreColor = (score: number) => {
  if (score >= 0.8) return '#67c23a' // 绿色 / Green
  if (score >= 0.6) return '#e6a23c' // 橙色 / Orange
  if (score >= 0.4) return '#f56c6c' // 红色 / Red
  return '#909399' // 灰色 / Gray
}

/**
 * 格式化工作描述
 * Format job description with basic HTML support
 */
const formatDescription = (description: string) => {
  if (!description) return 'No description available.'
  
  // 基本的Markdown到HTML转换 / Basic Markdown to HTML conversion
  return description
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^\*\s+(.*$)/gim, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}

// 方法 / Methods
/**
 * 处理卡片点击
 * Handle card click
 */
const handleCardClick = () => {
  emit('click', props.job)
}

/**
 * 打开职位原始链接
 * Open original job link
 */
const openJobLink = () => {
  if (props.job.url) {
    window.open(props.job.url, '_blank', 'noopener,noreferrer')
  }
}
</script>

<style scoped>
.job-card-wrapper {
  margin-bottom: 16px;
}

.job-card {
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: visible;
}

.job-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.job-card.highlighted {
  border: 2px solid #67c23a;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfccb 100%);
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.job-title-section {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.job-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.recommended-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.job-source {
  flex-shrink: 0;
}

.job-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.job-info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.info-icon {
  color: #909399;
  font-size: 16px;
}

.company-name {
  font-weight: 500;
  color: #409eff;
}

.salary {
  font-weight: 600;
  color: #67c23a;
}

.match-score {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.match-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

.score-progress {
  width: 100%;
}

.job-description {
  margin-bottom: 16px;
}

.description-content {
  max-height: 200px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

.description-content :deep(p) {
  margin: 8px 0;
}

.description-content :deep(ul) {
  margin: 8px 0;
  padding-left: 20px;
}

.description-content :deep(li) {
  margin: 4px 0;
}

.job-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-start;
}

.expired-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .job-header {
    flex-direction: column;
    gap: 8px;
  }
  
  .job-title {
    font-size: 16px;
  }
  
  .job-actions {
    flex-direction: column;
  }
  
  .job-actions .el-button {
    width: 100%;
  }
}
</style> 