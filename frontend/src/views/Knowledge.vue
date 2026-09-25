<template>
  <div class="knowledge-page">
    <PageHeader
      title="知识库"
      description="上传行业文档构建私有知识库，支持全文语义检索"
    />

    <div class="knowledge-layout">
      <!-- Left: Upload & Documents -->
      <div class="knowledge-sidebar">
        <!-- Upload -->
        <div class="card">
          <h3 class="card-title">上传文档</h3>
          <p class="card-description">支持 TXT、PDF、DOCX，最大 20MB</p>

          <div
            class="upload-zone-glass"
            :class="{ 'is-dragover': isDragover }"
            @dragover.prevent="isDragover = true"
            @dragleave.prevent="isDragover = false"
            @drop.prevent="handleDrop"
          >
            <el-icon :size="36" class="upload-zone-icon"><UploadFilled /></el-icon>
            <p class="upload-zone-text">拖拽文件到此处</p>
            <label class="btn btn-primary btn-sm" style="margin-top: 12px;">
              <input type="file" @change="handleFileSelect" accept=".txt,.pdf,.docx" hidden />
              <el-icon :size="14"><Upload /></el-icon>
              选择文件
            </label>
          </div>

          <div v-if="selectedFile" class="selected-file">
            <div class="selected-file-icon">
              <el-icon :size="16"><Document /></el-icon>
            </div>
            <span class="selected-file-name">{{ selectedFile.name }}</span>
            <button class="btn btn-primary btn-sm" :disabled="uploading" @click="uploadFile">
              {{ uploading ? '上传中…' : '确认上传' }}
            </button>
          </div>

          <div v-if="errorMessage" class="error-banner" style="margin-top: 12px;">
            <el-icon :size="16"><WarningFilled /></el-icon>
            <span>{{ errorMessage }}</span>
            <button class="btn btn-ghost btn-sm" style="margin-left: auto;" @click="errorMessage = ''">关闭</button>
          </div>
        </div>

        <!-- Document List -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">文档列表</h3>
            <span v-if="documents.length > 0" class="badge badge-neutral">{{ documents.length }} 个文档</span>
          </div>

          <div v-if="loadingDocs" class="loading-spinner" style="padding: 32px 0;">
            <span>加载中…</span>
          </div>

          <EmptyState
            v-else-if="documents.length === 0"
            title="暂无文档"
            description="上传面试、技术、行业文档以构建私有知识库"
            :icon="Folder"
            :icon-size="28"
          />

          <div v-else class="doc-list">
            <div v-for="doc in documents" :key="doc.id" class="doc-item">
              <div class="doc-item-main">
                <div class="doc-item-icon" :class="fileIconClass(doc.file_type)">
                  <el-icon :size="16"><Document /></el-icon>
                </div>
                <div class="doc-item-info">
                  <span class="doc-item-name">{{ doc.filename }}</span>
                  <span class="doc-item-meta">
                    <span class="doc-type-badge">{{ doc.file_type?.toUpperCase() }}</span>
                    · {{ doc.total_chunks }} 片段
                    · {{ formatDate(doc.created_at) }}
                  </span>
                </div>
              </div>
              <button class="btn btn-ghost btn-sm" style="color: var(--color-danger);" @click="confirmDelete(doc)">
                <el-icon :size="14"><Delete /></el-icon>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Search -->
      <div class="knowledge-main">
        <div class="card">
          <h3 class="card-title">知识检索</h3>
          <p class="card-description">语义搜索已上传文档，发现相关内容</p>

          <div class="search-box">
            <div class="search-input-wrapper">
              <el-icon :size="16" class="search-input-icon"><Search /></el-icon>
              <input
                v-model="searchKeyword"
                class="search-input-clean"
                type="text"
                placeholder="输入关键词，AI 语义检索…"
                @keyup.enter="searchKnowledge"
              />
            </div>
            <button
              class="btn btn-primary"
              :disabled="!searchKeyword.trim() || searching"
              @click="searchKnowledge"
            >
              {{ searching ? '检索中…' : '搜索' }}
            </button>
          </div>

          <!-- Initial State -->
          <EmptyState
            v-if="!hasSearched && searchResults.length === 0"
            title="开始检索"
            description="在上方输入关键词，AI 将在知识库中进行语义搜索"
            :icon="Search"
            :icon-size="28"
          />

          <!-- No Results -->
          <EmptyState
            v-else-if="hasSearched && searchResults.length === 0"
            title="未找到相关内容"
            description="尝试使用其他关键词，或上传更多相关文档"
            :icon="Search"
            :icon-size="28"
          />

          <!-- Results -->
          <div v-else-if="searchResults.length > 0" class="search-results">
            <div class="search-summary">
              <el-icon :size="16"><CircleCheckFilled /></el-icon>
              找到 <strong>{{ searchResults.length }}</strong> 条相关结果
            </div>
            <div class="result-list">
              <div v-for="result in searchResults" :key="result.chunk_id" class="result-item">
                <div class="result-header">
                  <div class="result-doc">
                    <el-icon :size="14"><Document /></el-icon>
                    <span>{{ result.document_name }}</span>
                  </div>
                  <span class="result-score">
                    相关度 {{ (result.score * 100).toFixed(0) }}%
                  </span>
                </div>
                <p class="result-snippet">{{ result.content }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <el-dialog v-model="showDeleteConfirm" title="确认删除" width="400px">
      <p style="color: var(--color-text-muted); line-height: 1.6;">
        确定要删除文档「{{ pendingDeleteDoc?.filename }}」吗？删除后知识库中的相关内容也将被移除。
      </p>
      <template #footer>
        <button class="btn btn-secondary" @click="showDeleteConfirm = false">取消</button>
        <button class="btn btn-danger" @click="doDelete">确认删除</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { knowledgeApi } from '@/api'
import {
  UploadFilled, Upload, Document, WarningFilled, Folder,
  Search, Delete, CircleCheckFilled
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'

const isDragover = ref(false)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const searching = ref(false)
const loadingDocs = ref(false)
const errorMessage = ref('')
const searchKeyword = ref('')
const hasSearched = ref(false)
const documents = ref<any[]>([])
const searchResults = ref<any[]>([])
const showDeleteConfirm = ref(false)
const pendingDeleteDoc = ref<any>(null)

const fileIconClass = (type: string): string => {
  const t = type?.toLowerCase() || ''
  if (t === 'pdf') return 'pdf'
  if (t === 'docx' || t === 'doc') return 'doc'
  return 'txt'
}

const loadDocuments = async () => {
  loadingDocs.value = true
  try {
    const response = await knowledgeApi.list()
    if (response.data.code === 200) {
      documents.value = response.data.data || []
    }
  } catch {
    // silently fail
  } finally {
    loadingDocs.value = false
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files?.length) {
    selectedFile.value = target.files[0]
    errorMessage.value = ''
  }
}

const handleDrop = (event: DragEvent) => {
  isDragover.value = false
  if (event.dataTransfer?.files.length) {
    selectedFile.value = event.dataTransfer.files[0]
    errorMessage.value = ''
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  errorMessage.value = ''
  try {
    const response = await knowledgeApi.upload(selectedFile.value)
    if (response.data.code === 200) {
      selectedFile.value = null
      await loadDocuments()
    } else {
      errorMessage.value = response.data.message || '上传失败'
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

const confirmDelete = (doc: any) => {
  pendingDeleteDoc.value = doc
  showDeleteConfirm.value = true
}

const doDelete = async () => {
  if (!pendingDeleteDoc.value) return
  try {
    await knowledgeApi.delete(pendingDeleteDoc.value.id)
    documents.value = documents.value.filter(d => d.id !== pendingDeleteDoc.value.id)
  } catch {
    // silently fail
  } finally {
    showDeleteConfirm.value = false
    pendingDeleteDoc.value = null
  }
}

const searchKnowledge = async () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return
  searching.value = true
  hasSearched.value = true
  errorMessage.value = ''
  try {
    const response = await knowledgeApi.search(keyword)
    if (response.data.code === 200) {
      searchResults.value = response.data.data || []
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '搜索失败'
  } finally {
    searching.value = false
  }
}

const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.knowledge-page {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

.knowledge-layout {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: var(--space-6);
  align-items: start;
}

@media (max-width: 900px) {
  .knowledge-layout {
    grid-template-columns: 1fr;
  }
}

/* Sidebar */
.knowledge-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* Selected File */
.selected-file {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.selected-file-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--color-brand-light);
  color: var(--color-brand);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.selected-file-name {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--color-text-body);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Document List */
.doc-list {
  display: flex;
  flex-direction: column;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
  transition: background var(--transition-fast);
}

.doc-item:last-child {
  border-bottom: none;
}

.doc-item:hover {
  background: var(--color-bg);
}

.doc-item-main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.doc-item-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.doc-item-icon.pdf {
  background: #FEF2F2;
  color: #DC2626;
}

.doc-item-icon.doc {
  background: #EFF6FF;
  color: #2563EB;
}

.doc-item-icon.txt {
  background: var(--color-border-light);
  color: var(--color-text-muted);
}

.doc-item-info {
  min-width: 0;
}

.doc-item-name {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-item-meta {
  font-size: var(--text-xs);
  color: var(--color-text-weak);
  display: flex;
  align-items: center;
  gap: 4px;
}

.doc-type-badge {
  font-weight: var(--weight-semibold);
  color: var(--color-brand);
}

/* Search */
.knowledge-main .card {
  min-height: 360px;
}

.search-box {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.search-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-input-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-weak);
  pointer-events: none;
}

.search-input-clean {
  width: 100%;
  padding: 10px 14px 10px 36px;
  font-size: var(--text-base);
  font-family: var(--font-family);
  color: var(--color-text);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.search-input-clean:focus {
  outline: none;
  border-color: var(--color-brand);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
  background: var(--color-surface);
}

.search-input-clean::placeholder {
  color: var(--color-text-weak);
}

/* Search Results */
.search-summary {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: var(--space-4) 0 var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border-light);
}

.search-summary strong {
  color: var(--color-brand);
}

.search-results {
  margin-top: var(--space-2);
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.result-item {
  padding: var(--space-4);
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-fast);
}

.result-item:hover {
  border-color: var(--color-brand);
  box-shadow: var(--shadow-sm);
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.result-doc {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

.result-score {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-brand);
  background: var(--color-brand-light);
  padding: 3px 10px;
  border-radius: var(--radius-full);
}

.result-snippet {
  font-size: var(--text-sm);
  color: var(--color-text-body);
  line-height: var(--leading-relaxed);
}
</style>
