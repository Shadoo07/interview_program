<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-brand" @click="goHome">
        <div class="brand-icon">
          <el-icon :size="20"><Document /></el-icon>
        </div>
        <div class="brand-text">
          <span class="brand-name">简历教练</span>
          <span class="brand-subtitle">AI Career Agent</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
        >
          <el-icon :size="18">
            <component :is="item.icon" />
          </el-icon>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="currentPath === item.path" class="nav-active-dot" />
        </router-link>
      </nav>

      <!-- AI Status Capsule -->
      <div class="sidebar-status">
        <div class="status-capsule" :class="{ online: llmConfigured }">
          <span class="status-dot" />
          <div class="status-text">
            <span class="status-model">{{ llmConfigured ? llmModelLabel : 'AI 待配置' }}</span>
            <span class="status-state">{{ llmConfigured ? 'Agent Ready' : '规则模板模式' }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  HomeFilled, Document, Edit, ChatDotRound,
  Collection, Clock, Setting
} from '@element-plus/icons-vue'
import { healthApi } from '@/api'

const router = useRouter()
const route = useRoute()

const currentPath = computed(() => route.path)
const llmConfigured = ref(false)
const llmModelLabel = ref('DeepSeek V4 Pro')

const navItems = [
  { path: '/',              label: '首页',     icon: HomeFilled },
  { path: '/resume-analysis', label: '简历分析', icon: Document },
  { path: '/resume-rewrite',  label: '简历改写', icon: Edit },
  { path: '/interview-prep',  label: '面试准备', icon: ChatDotRound },
  { path: '/knowledge',       label: '知识库',   icon: Collection },
  { path: '/history',         label: '历史记录', icon: Clock },
  { path: '/settings',        label: '设置',     icon: Setting },
]

const goHome = () => router.push('/')

const checkLlmConfig = async () => {
  try {
    const response = await healthApi.getLlmConfig()
    if (response.data.code === 200) {
      llmConfigured.value = response.data.data.configured
      if (response.data.data.preset_label) {
        llmModelLabel.value = response.data.data.preset_label
      } else if (response.data.data.preset) {
        llmModelLabel.value = response.data.data.preset
      }
    }
  } catch {
    // silently fail
  }
}

onMounted(() => {
  checkLlmConfig()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

/* ---- Sidebar ---- */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(226, 232, 240, 0.6);
  display: flex;
  flex-direction: column;
  z-index: 50;
  padding: var(--space-5);
}

/* ---- Brand ---- */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-2);
  margin-bottom: var(--space-6);
  cursor: pointer;
  user-select: none;
}

.brand-icon {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-brand);
  color: #FFFFFF;
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.30);
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.brand-subtitle {
  font-size: 11px;
  font-weight: var(--weight-medium);
  color: var(--color-text-weak);
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

/* ---- Navigation ---- */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 10px var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text-muted);
  text-decoration: none;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.nav-item:hover {
  background: var(--color-brand-light);
  color: var(--color-brand);
}

.nav-item:hover :deep(.el-icon) {
  transform: translateX(2px);
  transition: transform var(--transition-fast);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(124, 58, 237, 0.06) 100%);
  color: var(--color-brand);
  font-weight: var(--weight-semibold);
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.12);
}

.nav-item.active :deep(.el-icon) {
  color: var(--color-brand);
}

.nav-active-dot {
  position: absolute;
  right: var(--space-3);
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-brand);
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.5);
}

.nav-label {
  white-space: nowrap;
}

/* ---- Status Capsule ---- */
.sidebar-status {
  padding: var(--space-3) 0 0;
  border-top: 1px solid var(--color-border-light);
}

.status-capsule {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-fast);
}

.status-capsule.online {
  background: linear-gradient(135deg, rgba(240, 253, 244, 0.8) 0%, rgba(220, 252, 231, 0.6) 100%);
  border-color: rgba(22, 163, 74, 0.15);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-weak);
  flex-shrink: 0;
}

.status-capsule.online .status-dot {
  background: var(--color-success);
  box-shadow: 0 0 10px rgba(22, 163, 74, 0.5);
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.status-model {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  line-height: 1.3;
}

.status-state {
  font-size: 10px;
  color: var(--color-text-weak);
  letter-spacing: 0.02em;
}

.status-capsule.online .status-state {
  color: var(--color-success);
}

/* ---- Main Content ---- */
.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: var(--space-8);
  min-height: 100vh;
  max-width: calc(100vw - var(--sidebar-width));
  position: relative;
}
</style>
