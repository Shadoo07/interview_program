<template>
  <div class="empty-state">
    <el-icon class="empty-state-icon" :size="iconSize">
      <component :is="icon" />
    </el-icon>
    <h3 class="empty-state-title">{{ title }}</h3>
    <p v-if="description" class="empty-state-description">{{ description }}</p>
    <button v-if="actionLabel" class="btn btn-primary btn-sm" @click="$emit('action')">
      {{ actionLabel }}
    </button>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  actionLabel?: string
  icon?: any
  iconSize?: number
}>()

defineEmits<{
  action: []
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-6);
  text-align: center;
}

.empty-state-icon {
  color: var(--color-text-weak);
  margin-bottom: var(--space-4);
}

.empty-state-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.empty-state-description {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  max-width: 360px;
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-5);
}
</style>
