<template>
  <div class="search-bar">
    <!-- 搜索表单 / Search Form -->
    <el-form :model="searchForm" class="search-form" @submit.prevent="handleSearch">
      <!-- 主搜索框 / Main Search Input -->
      <div class="search-input-wrapper">
        <el-input
          v-model="searchForm.query"
          placeholder="Enter job title or skills (e.g., Vue.js Developer, Python, React)..."
          class="search-input"
          size="large"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 过滤选项 / Filter Options -->
      <div class="filters-row">
        <!-- 地点过滤 / Location Filter -->
        <el-select 
          v-model="searchForm.location" 
          placeholder="Location"
          class="filter-select"
          clearable
        >
          <el-option label="Berlin" value="berlin" />
          <el-option label="Munich" value="munich" />
          <el-option label="Hamburg" value="hamburg" />
          <el-option label="Frankfurt" value="frankfurt" />
          <el-option label="Cologne" value="cologne" />
          <el-option label="Stuttgart" value="stuttgart" />
          <el-option label="Düsseldorf" value="düsseldorf" />
          <el-option label="Remote" value="remote" />
        </el-select>

        <!-- 薪资范围过滤 / Salary Range Filter -->
        <el-select 
          v-model="searchForm.salaryRange" 
          placeholder="Salary Range"
          class="filter-select"
          clearable
        >
          <el-option label="€30k-50k" value="30000-50000" />
          <el-option label="€50k-70k" value="50000-70000" />
          <el-option label="€70k-90k" value="70000-90000" />
          <el-option label="€90k-120k" value="90000-120000" />
          <el-option label="€120k+" value="120000-999999" />
        </el-select>

        <!-- 工作类型过滤 / Job Type Filter -->
        <el-select 
          v-model="searchForm.jobType" 
          placeholder="Job Type"
          class="filter-select"
          clearable
        >
          <el-option label="Full-time" value="fulltime" />
          <el-option label="Part-time" value="parttime" />
          <el-option label="Contract" value="contract" />
          <el-option label="Freelance" value="freelance" />
          <el-option label="Internship" value="internship" />
        </el-select>

        <!-- 搜索按钮 / Search Button -->
        <el-button 
          type="primary" 
          size="large"
          @click="handleSearch"
          :loading="isLoading"
          class="search-button"
        >
          <el-icon><Search /></el-icon>
          Search Jobs
        </el-button>
      </div>
    </el-form>

    <!-- 搜索结果统计 / Search Results Stats -->
    <div v-if="totalJobs > 0" class="search-stats">
      <el-text type="info">
        Found {{ totalJobs }} jobs{{ searchForm.query ? ` for "${searchForm.query}"` : '' }}
      </el-text>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 职位搜索栏组件
 * Job search bar component
 */

import { ref, reactive } from 'vue'
import { ElForm, ElInput, ElSelect, ElOption, ElButton, ElIcon, ElText } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

// 定义组件属性接口 / Define component props interface
interface SearchParams {
  query: string
  location: string
  salaryRange: string
  jobType: string
}

// Props定义 / Props definition
interface Props {
  isLoading?: boolean
  totalJobs?: number
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  totalJobs: 0
})

// Emits定义 / Emits definition
const emit = defineEmits<{
  search: [params: SearchParams]
}>()

// 响应式数据 / Reactive data
const searchForm = reactive<SearchParams>({
  query: '',
  location: '',
  salaryRange: '',
  jobType: ''
})

// 方法 / Methods
/**
 * 处理搜索提交
 * Handle search submission
 */
const handleSearch = () => {
  emit('search', { ...searchForm })
}
</script>

<style scoped>
.search-bar {
  padding: 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.search-form {
  width: 100%;
}

.search-input-wrapper {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
}

.filters-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-select {
  min-width: 140px;
  flex: 1;
}

.search-button {
  min-width: 120px;
  height: 40px;
}

.search-stats {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 响应式设计 / Responsive design */
@media (max-width: 768px) {
  .filters-row {
    flex-direction: column;
  }
  
  .filter-select {
    width: 100%;
    min-width: auto;
  }
  
  .search-button {
    width: 100%;
  }
}
</style> 