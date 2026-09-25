<template>
  <div class="markdown-viewer">
    <div v-if="!content" class="markdown-empty">
      <el-icon :size="20"><Document /></el-icon>
      <span>暂无内容</span>
    </div>
    <div v-else class="markdown-body" v-html="renderedContent" />
    <div v-if="showCopy && content" class="markdown-toolbar">
      <button class="btn btn-ghost btn-sm" @click="handleCopy">
        <el-icon :size="14"><component :is="copied ? Check : CopyDocument" /></el-icon>
        {{ copied ? '已复制' : '复制' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Document, CopyDocument, Check } from '@element-plus/icons-vue'

const props = defineProps<{
  content: string
  showCopy?: boolean
}>()

const copied = ref(false)

const renderedContent = computed(() => {
  if (!props.content) return ''
  let html = props.content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/^(\d+)\. (.*$)/gim, '<li>$2</li>')
    .replace(/\n\n/gim, '<br><br>')
    .replace(/\n/gim, '<br>')
  return html
})

const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
  }
}
</script>

<style scoped>
.markdown-viewer {
  position: relative;
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  min-height: 60px;
}

.markdown-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  color: var(--color-text-weak);
  font-size: var(--text-sm);
  padding: var(--space-6) 0;
}

.markdown-body {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-text-body);
}

.markdown-body :deep(h1) {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  margin-bottom: var(--space-4);
}

.markdown-body :deep(h2) {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin: var(--space-5) 0 var(--space-3);
}

.markdown-body :deep(h3) {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin: var(--space-4) 0 var(--space-2);
}

.markdown-body :deep(strong) {
  color: var(--color-text);
  font-weight: var(--weight-semibold);
}

.markdown-body :deep(li) {
  margin-left: var(--space-5);
  margin-bottom: var(--space-1);
}

.markdown-toolbar {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
}
</style>
