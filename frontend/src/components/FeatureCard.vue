<template>
  <div class="feature-card" :class="{ clickable }" @click="clickable && $emit('click')">
    <div class="feature-card-icon" :class="iconBgClass">
      <el-icon :size="20">
        <component :is="icon" />
      </el-icon>
    </div>
    <div class="feature-card-body">
      <h3 class="feature-card-title">{{ title }}</h3>
      <p class="feature-card-description">{{ description }}</p>
    </div>
    <el-icon v-if="clickable" class="feature-card-arrow" :size="16">
      <ArrowRight />
    </el-icon>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'

const props = defineProps<{
  title: string
  description: string
  icon: any
  variant?: 'brand' | 'purple' | 'success' | 'warning'
  clickable?: boolean
}>()

defineEmits<{
  click: []
}>()

const iconBgClass = computed(() => `icon-bg-${props.variant || 'brand'}`)
</script>

<style scoped>
.feature-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.feature-card.clickable {
  cursor: pointer;
}

.feature-card.clickable:hover {
  border-color: var(--color-brand);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.feature-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.icon-bg-brand {
  background: var(--color-brand-light);
  color: var(--color-brand);
}

.icon-bg-purple {
  background: var(--color-purple-light);
  color: var(--color-purple);
}

.icon-bg-success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.icon-bg-warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.feature-card-body {
  flex: 1;
  min-width: 0;
}

.feature-card-title {
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: 2px;
}

.feature-card-description {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-normal);
}

.feature-card-arrow {
  color: var(--color-text-weak);
  flex-shrink: 0;
  margin-top: 10px;
  transition: transform var(--transition-fast);
}

.feature-card.clickable:hover .feature-card-arrow {
  transform: translateX(3px);
  color: var(--color-brand);
}
</style>
