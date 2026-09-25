<template>
  <div class="keyword-tags">
    <span
      v-for="(tag, index) in tags"
      :key="index"
      class="keyword-tag"
      :class="`tag-${type}`"
    >
      {{ tag }}
    </span>
    <span v-if="tags.length === 0" class="keyword-empty">暂无</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  tags: string[]
  type?: 'matched' | 'missing' | 'info' | 'neutral'
}>()
</script>

<style scoped>
.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  line-height: 1.5;
}

.tag-matched {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.tag-missing {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.tag-info {
  background: var(--color-brand-soft);
  color: var(--color-brand);
}

.tag-neutral {
  background: var(--color-border-light);
  color: var(--color-text-muted);
}

.keyword-empty {
  font-size: var(--text-sm);
  color: var(--color-text-weak);
}
</style>
