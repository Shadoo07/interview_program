<template>
  <div class="step-panel">
    <div class="step-list">
      <div
        v-for="(step, index) in steps"
        :key="index"
        class="step-item"
        :class="getStepClass(index)"
      >
        <div class="step-indicator">
          <el-icon v-if="index < currentStep" :size="14"><Check /></el-icon>
          <span v-else class="step-number">{{ index + 1 }}</span>
        </div>
        <span class="step-label">{{ step }}</span>
        <div v-if="index < steps.length - 1" class="step-connector" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check } from '@element-plus/icons-vue'

const props = defineProps<{
  steps: string[]
  currentStep: number
}>()

const getStepClass = (index: number): string => {
  if (index < props.currentStep) return 'completed'
  if (index === props.currentStep) return 'active'
  return 'pending'
}
</script>

<style scoped>
.step-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  margin-bottom: var(--space-6);
}

.step-list {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.step-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  position: relative;
  flex: 1;
  min-width: 0;
}

.step-connector {
  position: absolute;
  left: calc(100% + 4px);
  top: 50%;
  right: 0;
  height: 2px;
  background: var(--color-border);
  transform: translateY(-50%);
  min-width: 16px;
}

.step-item:last-child .step-connector {
  display: none;
}

.step-item.completed .step-connector {
  background: var(--color-success);
}

.step-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  transition: all var(--transition-fast);
}

.step-item.pending .step-indicator {
  background: var(--color-border-light);
  color: var(--color-text-weak);
}

.step-item.active .step-indicator {
  background: var(--color-brand);
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}

.step-item.completed .step-indicator {
  background: var(--color-success);
  color: #FFFFFF;
}

.step-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  white-space: nowrap;
}

.step-item.pending .step-label {
  color: var(--color-text-weak);
}

.step-item.active .step-label {
  color: var(--color-brand);
}

.step-item.completed .step-label {
  color: var(--color-text-body);
}

@media (max-width: 768px) {
  .step-label {
    display: none;
  }
}
</style>
