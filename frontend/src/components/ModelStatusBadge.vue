<template>
  <span class="model-badge" :class="`model-badge-${status}`">
    <span class="model-badge-dot" />
    <span>{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  configured: boolean
  mode?: string
}>()

const status = computed(() => props.configured ? 'active' : 'inactive')
const label = computed(() => {
  if (props.configured && props.mode) return `AI · ${props.mode}`
  return props.configured ? 'AI 已配置' : 'AI 未配置'
})
</script>

<style scoped>
.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  white-space: nowrap;
}

.model-badge-active {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.model-badge-inactive {
  background: var(--color-border-light);
  color: var(--color-text-muted);
}

.model-badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.model-badge-active .model-badge-dot {
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
