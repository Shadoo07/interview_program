<template>
  <div class="history-page">
    <PageHeader
      title="历史记录"
      description="查看和管理所有分析记录，支持恢复继续分析"
    />

    <!-- Loading -->
    <div v-if="loading" class="loading-spinner">
      <span>加载分析记录…</span>
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="records.length === 0"
      title="暂无分析记录"
      description="完成一次简历分析后，记录将自动保存在这里"
      :icon="Clock"
      action-label="开始首次分析"
      @action="goToAnalysis"
    />

    <!-- Records Grid -->
    <div v-else class="records-grid">
      <div v-for="record in records" :key="record.id" class="record-card card card-hover" @click="viewRecord(record)">
        <!-- Header -->
        <div class="record-header">
          <div class="record-file">
            <div class="record-file-icon">
              <el-icon :size="20"><Document /></el-icon>
            </div>
            <div class="record-file-info">
              <span class="record-filename">{{ record.resume_filename || '未命名简历' }}</span>
              <span class="record-position">{{ getJdTitle(record) || '未设置目标岗位' }}</span>
            </div>
          </div>
          <div v-if="record.match_result" class="record-match">
            <span class="record-match-score">{{ record.match_result.overall_score }}</span>
            <span class="record-match-label">匹配分</span>
          </div>
        </div>

        <!-- Meta -->
        <div class="record-meta">
          <span class="record-date">
            <el-icon :size="12"><Clock /></el-icon>
            {{ formatDate(record.created_at) }}
          </span>
          <div class="record-tags">
            <span v-if="record.resume_data" class="badge badge-neutral">已解析</span>
            <span v-if="record.jd_data" class="badge badge-info">JD 已分析</span>
            <span v-if="record.rewrite_result" class="badge badge-purple">已改写</span>
            <span v-if="record.interview_questions" class="badge badge-success">面试题</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="record-actions" @click.stop>
          <button class="btn btn-secondary btn-sm" @click="restoreRecord(record)">
            <el-icon :size="14"><RefreshRight /></el-icon>
            恢复分析
          </button>
          <button class="btn btn-ghost btn-sm" style="color: var(--color-danger);" @click="confirmDelete(record)">
            <el-icon :size="14"><Delete /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetail" title="分析详情" width="520px" destroy-on-close>
      <template v-if="selectedRecord">
        <div class="detail-block">
          <h4 class="detail-title">基本信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">文件</span>
              <span class="detail-value">{{ selectedRecord.resume_filename || '未命名' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">时间</span>
              <span class="detail-value">{{ formatFullDate(selectedRecord.created_at) }}</span>
            </div>
          </div>
        </div>

        <div v-if="selectedRecord.jd_data" class="detail-block">
          <h4 class="detail-title">目标岗位</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">职位</span>
              <span class="detail-value">{{ selectedRecord.jd_data.position_title || '未知' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">类型</span>
              <span class="detail-value">{{ selectedRecord.jd_data.position_type || '未知' }}</span>
            </div>
          </div>
        </div>

        <div v-if="selectedRecord.match_result" class="detail-block">
          <h4 class="detail-title">匹配度报告</h4>
          <div class="detail-match">
            <span class="detail-match-num">{{ selectedRecord.match_result.overall_score }}</span>
            <span class="detail-match-unit">%</span>
            <span class="badge" :class="matchBadge(selectedRecord.match_result.overall_score)">
              {{ matchLevel(selectedRecord.match_result.overall_score) }}
            </span>
          </div>
        </div>
      </template>

      <template #footer>
        <button class="btn btn-secondary" @click="showDetail = false">关闭</button>
        <button class="btn btn-primary" @click="restoreRecord(selectedRecord); showDetail = false;">
          恢复此分析
        </button>
      </template>
    </el-dialog>

    <!-- Delete Confirmation -->
    <el-dialog v-model="showDeleteConfirm" title="确认删除" width="400px">
      <p style="color: var(--color-text-muted); line-height: 1.6;">
        确定要删除这条分析记录吗？此操作不可撤销。
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
import { useRouter } from 'vue-router'
import { historyApi } from '@/api'
import { Clock, Document, Delete, RefreshRight } from '@element-plus/icons-vue'
import { useResumeStore } from '@/stores/resume'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const store = useResumeStore()

const records = ref<any[]>([])
const loading = ref(true)
const showDetail = ref(false)
const selectedRecord = ref<any>(null)
const showDeleteConfirm = ref(false)
const pendingDeleteId = ref<number | null>(null)

const loadHistory = async () => {
  loading.value = true
  try {
    const resp = await historyApi.list()
    if (resp.data.code === 200) records.value = resp.data.data || []
  } catch { /* ignore */ }
  finally { loading.value = false }
}

const viewRecord = (record: any) => {
  selectedRecord.value = record
  showDetail.value = true
}

const restoreRecord = (record: any) => {
  sessionStorage.setItem('restoredRecord', JSON.stringify(record))
  store.restoreFromHistory(record)
  router.push('/resume-analysis')
}

const confirmDelete = (record: any) => {
  pendingDeleteId.value = record.id
  showDeleteConfirm.value = true
}

const doDelete = async () => {
  if (pendingDeleteId.value == null) return
  try {
    await historyApi.delete(pendingDeleteId.value)
    records.value = records.value.filter(r => r.id !== pendingDeleteId.value)
  } catch { /* ignore */ }
  finally {
    showDeleteConfirm.value = false
    pendingDeleteId.value = null
  }
}

const goToAnalysis = () => router.push('/resume-analysis')

const getJdTitle = (r: any): string => r.jd_data?.position_title || (r.jd_text || '').substring(0, 40)

const formatDate = (d: string) => {
  try { return new Date(d).toLocaleDateString('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }) }
  catch { return d }
}

const formatFullDate = (d: string) => {
  try { return new Date(d).toLocaleString('zh-CN') }
  catch { return d }
}

const matchBadge = (s: number): string => {
  if (s >= 80) return 'badge-success'
  if (s >= 60) return 'badge-info'
  if (s >= 40) return 'badge-warning'
  return 'badge-danger'
}

const matchLevel = (s: number): string => {
  if (s >= 80) return '优秀'
  if (s >= 60) return '良好'
  if (s >= 40) return '一般'
  return '需提升'
}

onMounted(() => { loadHistory() })
</script>

<style scoped>
.history-page {
  max-width: 960px;
  margin: 0 auto;
}

/* Records Grid */
.records-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-3);
}

/* Record Card */
.record-card {
  padding: var(--space-5) !important;
  cursor: pointer;
}

.record-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-4);
  gap: var(--space-4);
}

.record-file {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
  flex: 1;
}

.record-file-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-lg);
  background: var(--color-brand-light);
  color: var(--color-brand);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.record-file-info {
  min-width: 0;
}

.record-filename {
  display: block;
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-position {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.record-match {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.06) 0%, rgba(124, 58, 237, 0.04) 100%);
  border: 1px solid rgba(37, 99, 235, 0.1);
  flex-shrink: 0;
}

.record-match-score {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-brand);
  line-height: 1;
  letter-spacing: -0.02em;
}

.record-match-label {
  font-size: 10px;
  color: var(--color-text-weak);
  margin-top: 1px;
}

.record-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
  gap: var(--space-2);
}

.record-date {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--color-text-weak);
}

.record-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.record-actions {
  display: flex;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

/* Detail Dialog */
.detail-block {
  margin-bottom: var(--space-5);
}

.detail-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-brand);
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-border-light);
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.detail-item {
  display: flex;
  font-size: var(--text-sm);
}

.detail-label {
  width: 60px;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.detail-value {
  color: var(--color-text);
}

.detail-match {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.detail-match-num {
  font-size: 36px;
  font-weight: var(--weight-bold);
  color: var(--color-text);
  letter-spacing: -0.03em;
}

.detail-match-unit {
  font-size: var(--text-lg);
  color: var(--color-text-muted);
}
</style>
