<template>
  <div class="result-card" :class="variant">
    <div class="result-card-header" @click="toggle">
      <div class="result-card-header-left">
        <el-icon v-if="iconComponent" :size="18" class="result-card-icon">
          <component :is="iconComponent" />
        </el-icon>
        <h4 class="result-card-title">{{ title }}</h4>
        <span v-if="badge" class="result-card-badge">{{ badge }}</span>
      </div>
      <el-icon class="result-card-chevron" :class="{ expanded: isExpanded }" :size="18">
        <ArrowDown />
      </el-icon>
    </div>
    <div v-show="isExpanded" class="result-card-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps<{
  title: string
  variant?: 'default' | 'success' | 'warning' | 'danger'
  icon?: any
  badge?: string
}>()

const isExpanded = ref(true)

const iconComponent = computed(() => props.icon || null)

const toggle = () => {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped>
.result-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.result-card.warning {
  border-left: 3px solid var(--color-warning);
}

.result-card.danger {
  border-left: 3px solid var(--color-danger);
}

.result-card.success {
  border-left: 3px solid var(--color-success);
}

.result-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
}

.result-card-header:hover {
  background: var(--color-bg);
}

.result-card-header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.result-card-icon {
  color: var(--color-text-muted);
}

.result-card-title {
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

.result-card-badge {
  padding: 2px 8px;
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  background: var(--color-brand-light);
  color: var(--color-brand);
  border-radius: var(--radius-full);
}

.result-card-chevron {
  color: var(--color-text-weak);
  transition: transform var(--transition-fast);
}

.result-card-chevron.expanded {
  transform: rotate(180deg);
}

.result-card-body {
  padding: 0 var(--space-5) var(--space-5);
}
</style>
