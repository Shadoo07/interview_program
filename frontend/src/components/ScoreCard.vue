<template>
  <div class="score-card">
    <div class="score-card-header">
      <span class="score-label">{{ label }}</span>
      <span class="score-value" :class="scoreColor">{{ score }}</span>
    </div>
    <div class="score-bar">
      <div class="score-fill" :class="scoreColor" :style="{ width: clampedScore + '%' }" />
    </div>
    <div v-if="description" class="score-description">{{ description }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  score: number
  description?: string
}>()

const clampedScore = computed(() => Math.min(100, Math.max(0, props.score)))

const scoreColor = computed(() => {
  if (props.score >= 80) return 'excellent'
  if (props.score >= 60) return 'good'
  if (props.score >= 40) return 'average'
  return 'poor'
})
</script>

<style scoped>
.score-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--space-4);
}

.score-card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: var(--space-2);
}

.score-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-weight: var(--weight-medium);
}

.score-value {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  font-variant-numeric: tabular-nums;
}

.score-value.excellent { color: var(--color-success); }
.score-value.good     { color: var(--color-brand); }
.score-value.average  { color: var(--color-warning); }
.score-value.poor     { color: var(--color-danger); }

.score-bar {
  height: 6px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.score-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.score-fill.excellent { background: var(--color-success); }
.score-fill.good     { background: var(--color-brand); }
.score-fill.average  { background: var(--color-warning); }
.score-fill.poor     { background: var(--color-danger); }

.score-description {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-weak);
}
</style>
