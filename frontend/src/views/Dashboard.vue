<template>
  <div class="dashboard">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-grid">
        <!-- Left: Hero Text + CTA -->
        <div class="hero-left">
          <div class="hero-badge">
            <span class="badge badge-purple">
              <span class="badge-dot" />
              AI Career Agent
            </span>
          </div>
          <h1 class="hero-title">让每一份简历，<br />更接近理想 Offer</h1>
          <p class="hero-subtitle">
            上传简历与目标 JD，AI 将从<strong> HR 初筛官</strong>、<strong>技术面试官</strong>、<strong>简历编辑专家</strong>
            三个 Agent 视角生成诊断建议，一站式提升求职竞争力。
          </p>
          <div class="hero-actions">
            <button class="btn btn-primary btn-xl" @click="goToAnalysis">
              <el-icon :size="20"><Upload /></el-icon>
              开始分析简历
            </button>
            <button class="btn btn-secondary btn-lg" @click="goToHistory" v-if="hasHistory">
              <el-icon :size="18"><Clock /></el-icon>
              历史记录
            </button>
          </div>
        </div>

        <!-- Right: AI Readiness Panel -->
        <div class="hero-right">
          <div class="glass-card readiness-panel">
            <div class="readiness-header">
              <div class="readiness-title-row">
                <el-icon :size="18" class="readiness-icon"><TrendCharts /></el-icon>
                <span class="readiness-title">Offer Readiness</span>
              </div>
              <div class="readiness-score">
                <template v-if="hasAnalysisData">{{ readinessScore }}<span class="readiness-total">/100</span></template>
                <template v-else>--<span class="readiness-total">/100</span></template>
              </div>
            </div>

            <div v-if="hasAnalysisData" class="readiness-metrics">
              <div class="readiness-metric">
                <div class="metric-header">
                  <span class="metric-label">JD 匹配度</span>
                  <span class="metric-value">{{ metrics.jdMatch }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-bar-fill blue" :style="{ width: metrics.jdMatch + '%' }" />
                </div>
              </div>
              <div class="readiness-metric">
                <div class="metric-header">
                  <span class="metric-label">项目表达深度</span>
                  <span class="metric-value">{{ metrics.projectDepth }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-bar-fill purple" :style="{ width: metrics.projectDepth + '%' }" />
                </div>
              </div>
              <div class="readiness-metric">
                <div class="metric-header">
                  <span class="metric-label">技术关键词覆盖</span>
                  <span class="metric-value">{{ metrics.keywordCoverage }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-bar-fill green" :style="{ width: metrics.keywordCoverage + '%' }" />
                </div>
              </div>
              <div class="readiness-metric">
                <div class="metric-header">
                  <span class="metric-label">HR 初筛友好度</span>
                  <span class="metric-value">{{ metrics.hrFriendly }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-bar-fill blue" :style="{ width: metrics.hrFriendly + '%' }" />
                </div>
              </div>
              <div class="readiness-metric">
                <div class="metric-header">
                  <span class="metric-label">面试准备完整度</span>
                  <span class="metric-value">{{ metrics.interviewReady }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-bar-fill amber" :style="{ width: metrics.interviewReady + '%' }" />
                </div>
              </div>
            </div>

            <div v-else class="readiness-empty">
              <p class="readiness-empty-text">上传简历并完成分析后，此处将展示求职准备度评估</p>
              <button class="btn btn-primary btn-sm" @click="goToAnalysis">开始分析</button>
            </div>

            <div class="readiness-footer">
              <ModelStatusBadge :configured="llmConfigured" :mode="llmMode" />
              <span class="readiness-hint">{{ hasAnalysisData ? '基于最近一次分析' : '等待首次分析' }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- AI Agent Cards -->
    <section class="agents-section">
      <div class="section-header">
        <h2 class="section-title">AI Agent 矩阵</h2>
        <p class="section-desc">四个专业 Agent 协同工作，覆盖简历筛选全流程</p>
      </div>
      <div class="agent-grid">
        <div class="agent-card" @click="goToAnalysis">
          <div class="agent-card-icon blue">
            <el-icon :size="22"><View /></el-icon>
          </div>
          <div class="agent-card-body">
            <h3 class="agent-card-title">HR 初筛官 Agent</h3>
            <p class="agent-card-desc">模拟 HR 筛选逻辑，评估简历格式、关键词密度与初筛通过率</p>
          </div>
          <el-icon :size="16" class="agent-card-arrow"><ArrowRight /></el-icon>
        </div>

        <div class="agent-card" @click="goToAnalysis">
          <div class="agent-card-icon purple">
            <el-icon :size="22"><Monitor /></el-icon>
          </div>
          <div class="agent-card-body">
            <h3 class="agent-card-title">技术面试官 Agent</h3>
            <p class="agent-card-desc">从技术深度、项目经验、系统设计能力等维度评估技术竞争力</p>
          </div>
          <el-icon :size="16" class="agent-card-arrow"><ArrowRight /></el-icon>
        </div>

        <div class="agent-card" @click="goToAnalysis">
          <div class="agent-card-icon green">
            <el-icon :size="22"><EditPen /></el-icon>
          </div>
          <div class="agent-card-body">
            <h3 class="agent-card-title">简历编辑专家 Agent</h3>
            <p class="agent-card-desc">优化项目描述、量化成果表达、重构简历结构与排版逻辑</p>
          </div>
          <el-icon :size="16" class="agent-card-arrow"><ArrowRight /></el-icon>
        </div>

        <div class="agent-card" @click="goToAnalysis">
          <div class="agent-card-icon amber">
            <el-icon :size="22"><Connection /></el-icon>
          </div>
          <div class="agent-card-body">
            <h3 class="agent-card-title">JD 匹配分析 Agent</h3>
            <p class="agent-card-desc">深度比对 JD 要求与简历能力，输出匹配度评分与技能缺口报告</p>
          </div>
          <el-icon :size="16" class="agent-card-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </section>

    <!-- Bottom Grid: Quick Start + Recent -->
    <section class="bottom-grid">
      <!-- Quick Start Guide -->
      <div class="card guide-card">
        <h3 class="card-title">快速上手</h3>
        <p class="card-description">三步完成首次分析</p>
        <div class="guide-steps">
          <div class="guide-step">
            <span class="guide-step-num">1</span>
            <div class="guide-step-body">
              <strong>上传简历</strong>
              <p>支持 PDF / DOCX / TXT 格式，拖拽或点击上传</p>
            </div>
          </div>
          <div class="guide-step">
            <span class="guide-step-num">2</span>
            <div class="guide-step-body">
              <strong>输入目标 JD</strong>
              <p>粘贴岗位描述，AI 自动提取关键技能与要求</p>
            </div>
          </div>
          <div class="guide-step">
            <span class="guide-step-num">3</span>
            <div class="guide-step-body">
              <strong>获取诊断报告</strong>
              <p>多 Agent 并行分析，生成匹配评分与优化方案</p>
            </div>
          </div>
        </div>
      </div>

      <!-- System Status -->
      <div class="card status-card">
        <h3 class="card-title">系统状态</h3>
        <p class="card-description">当前 AI 引擎配置</p>
        <div class="status-items">
          <div class="status-item">
            <div class="status-item-icon" :class="llmConfigured ? 'online' : 'offline'">
              <el-icon :size="16"><Cpu /></el-icon>
            </div>
            <div class="status-item-body">
              <span class="status-item-label">AI 生成模式</span>
              <span class="status-item-value">{{ llmConfigured ? `${llmMode} · 大模型生成` : '规则模板生成' }}</span>
            </div>
            <button class="btn btn-ghost btn-sm" @click="goToSettings">配置</button>
          </div>
          <div class="status-item">
            <div class="status-item-icon" :class="hasRecentData ? 'online' : 'offline'">
              <el-icon :size="16"><Folder /></el-icon>
            </div>
            <div class="status-item-body">
              <span class="status-item-label">进行中的分析</span>
              <span class="status-item-value">{{ hasRecentData ? '有未完成的分析' : '暂无' }}</span>
            </div>
            <button v-if="hasRecentData" class="btn btn-ghost btn-sm" @click="goToAnalysis">继续</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Recent Records -->
    <section v-if="recentRecords.length > 0" class="recent-section">
      <div class="section-header">
        <h2 class="section-title">最近分析</h2>
        <button class="btn btn-ghost btn-sm" @click="goToHistory">
          查看全部
          <el-icon :size="14"><ArrowRight /></el-icon>
        </button>
      </div>
      <div class="recent-list">
        <div
          v-for="record in recentRecords"
          :key="record.id"
          class="recent-item card"
          @click="restoreRecord(record)"
        >
          <div class="recent-item-left">
            <div class="recent-item-icon">
              <el-icon :size="18"><Document /></el-icon>
            </div>
            <div class="recent-item-info">
              <span class="recent-name">{{ record.resume_filename || '未命名简历' }}</span>
              <span class="recent-meta">
                {{ getJdTitle(record) || '未设置 JD' }}
                <span class="meta-sep">·</span>
                {{ formatDate(record.created_at) }}
              </span>
            </div>
          </div>
          <div class="recent-item-right">
            <span v-if="record.match_result" class="badge" :class="getMatchBadge(record.match_result.overall_score)">
              匹配 {{ record.match_result.overall_score }}%
            </span>
            <el-icon :size="16" class="recent-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </section>

    <!-- Empty Prompt -->
    <div v-if="!hasRecentData && !hasHistory" class="hero-footer">
      <p class="text-muted">还没有分析记录？上传第一份简历，开启 AI 求职辅导之旅</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Upload, Clock, Document, Connection, ArrowRight,
  Cpu, Folder, View, Monitor, EditPen, TrendCharts
} from '@element-plus/icons-vue'
import { healthApi, historyApi } from '@/api'
import { useResumeStore } from '@/stores/resume'
import ModelStatusBadge from '@/components/ModelStatusBadge.vue'

const router = useRouter()
const store = useResumeStore()

const llmConfigured = ref(false)
const llmMode = ref('')
const hasRecentData = ref(false)
const hasHistory = ref(false)
const recentRecords = ref<any[]>([])

const hasAnalysisData = computed(() => {
  return !!(store.matchResult || store.diagnoseResult)
})

const metrics = computed(() => {
  const m = { jdMatch: 0, projectDepth: 0, keywordCoverage: 0, hrFriendly: 0, interviewReady: 0 }

  // JD 匹配度: directly from match result
  if (store.matchResult?.overall_score != null) {
    m.jdMatch = Math.round(store.matchResult.overall_score)
  }

  // 技术关键词覆盖: matched / (matched + missing)
  if (store.matchResult) {
    const matched = store.matchResult.matched_keywords?.length || 0
    const missing = store.matchResult.missing_keywords?.length || 0
    const total = matched + missing
    m.keywordCoverage = total > 0 ? Math.round((matched / total) * 100) : 0
  }

  // 项目表达深度: based on diagnose strengths vs weaknesses ratio
  if (store.diagnoseResult) {
    const strengths = store.diagnoseResult.strengths?.length || 0
    const weaknesses = store.diagnoseResult.weaknesses?.length || 0
    const improvements = store.diagnoseResult.improvements?.length || 0
    // More strengths relative to weaknesses = higher depth
    const total = strengths + weaknesses
    if (total > 0) {
      m.projectDepth = Math.round(50 + (strengths / total) * 40 + Math.min(improvements, 3) * 3)
      m.projectDepth = Math.min(m.projectDepth, 100)
    }
  }

  // HR 初筛友好度: based on diagnose improvements priority
  if (store.diagnoseResult) {
    const improvements = store.diagnoseResult.improvements || []
    const highPriority = improvements.filter((i: any) => i.priority === 'high').length
    const total = improvements.length || 1
    // Fewer high-priority issues = friendlier
    m.hrFriendly = Math.round(Math.max(40, 100 - (highPriority / total) * 60))
  }

  // 面试准备完整度: based on available preparation materials
  let prepScore = 0
  if (store.matchResult) prepScore += 20
  if (store.diagnoseResult) prepScore += 20
  if (store.rewriteResult?.rewritten_content) prepScore += 25
  if (store.interviewQuestions) {
    const q = store.interviewQuestions
    const hasQuestions = (q.project_deep_dive?.length || 0) + (q.tech_theory?.length || 0) > 0
    if (hasQuestions) prepScore += 20
    if (q.self_intro) prepScore += 15
  }
  m.interviewReady = Math.min(prepScore, 100)

  return m
})

const readinessScore = computed(() => {
  if (!hasAnalysisData.value) return 0
  const m = metrics.value
  // Weighted average: JD match 30%, keyword 20%, project 20%, HR 15%, interview 15%
  return Math.round(
    m.jdMatch * 0.30 +
    m.keywordCoverage * 0.20 +
    m.projectDepth * 0.20 +
    m.hrFriendly * 0.15 +
    m.interviewReady * 0.15
  )
})

const goToAnalysis = () => router.push('/resume-analysis')
const goToHistory = () => router.push('/history')
const goToSettings = () => router.push('/settings')

const getJdTitle = (record: any): string => {
  if (record.jd_data?.position_title) return record.jd_data.position_title
  if (record.jd_text) return record.jd_text.substring(0, 30)
  return ''
}

const formatDate = (dateStr: string) => {
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
    })
  } catch { return dateStr }
}

const getMatchBadge = (score: number): string => {
  if (score >= 80) return 'badge-success'
  if (score >= 60) return 'badge-info'
  if (score >= 40) return 'badge-warning'
  return 'badge-danger'
}

const restoreRecord = (record: any) => {
  sessionStorage.setItem('restoredRecord', JSON.stringify(record))
  store.restoreFromHistory(record)
  router.push('/resume-analysis')
}

onMounted(async () => {
  try {
    const resp = await healthApi.getLlmConfig()
    if (resp.data.code === 200) {
      llmConfigured.value = resp.data.data.configured
      llmMode.value = resp.data.data.preset_label || resp.data.data.preset || ''
    }
  } catch { /* ignore */ }

  store.restoreFromStorage()
  hasRecentData.value = !!(store.resumeData || store.jdText)

  try {
    const resp = await historyApi.list()
    if (resp.data.code === 200) {
      const all = resp.data.data || []
      recentRecords.value = all.slice(0, 5)
      hasHistory.value = all.length > 0
    }
  } catch { /* ignore */ }
})
</script>

<style scoped>
.dashboard {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

/* ---- Hero ---- */
.hero {
  margin-bottom: var(--space-12);
  padding-top: var(--space-4);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: var(--space-12);
  align-items: center;
}

@media (max-width: 960px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: var(--space-8);
  }
}

.hero-left {
  padding-top: var(--space-4);
}

.hero-badge {
  margin-bottom: var(--space-5);
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-purple);
  display: inline-block;
  margin-right: 2px;
  box-shadow: 0 0 8px rgba(124, 58, 237, 0.5);
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.hero-title {
  font-size: var(--text-5xl);
  font-weight: var(--weight-bold);
  color: var(--color-text);
  letter-spacing: -0.04em;
  line-height: 1.15;
  margin-bottom: var(--space-5);
}

.hero-subtitle {
  font-size: var(--text-md);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  max-width: 540px;
  margin-bottom: var(--space-8);
}

.hero-subtitle strong {
  font-weight: var(--weight-semibold);
  color: var(--color-text-body);
}

.hero-actions {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.hero-footer {
  text-align: center;
  padding: var(--space-10) 0;
  font-size: var(--text-base);
}

/* ---- Readiness Panel ---- */
.hero-right {
  display: flex;
  justify-content: center;
}

.readiness-panel {
  width: 100%;
  padding: var(--space-6);
}

.readiness-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.readiness-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.readiness-icon {
  color: var(--color-purple);
}

.readiness-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text-muted);
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.readiness-score {
  font-size: 40px;
  font-weight: var(--weight-bold);
  color: var(--color-text);
  line-height: 1;
  letter-spacing: -0.03em;
  background: var(--gradient-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.readiness-total {
  font-size: var(--text-lg);
  -webkit-text-fill-color: var(--color-text-muted);
}

.readiness-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.readiness-metric .metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.metric-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: var(--weight-medium);
}

.metric-value {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.readiness-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

.readiness-hint {
  font-size: var(--text-xs);
  color: var(--color-text-weak);
}

.readiness-empty {
  text-align: center;
  padding: var(--space-6) 0;
}

.readiness-empty-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-4);
  line-height: var(--leading-relaxed);
}

/* ---- Section Headers ---- */
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.section-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.section-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

/* ---- Agent Cards ---- */
.agents-section {
  margin-bottom: var(--space-12);
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

@media (max-width: 768px) {
  .agent-grid {
    grid-template-columns: 1fr;
  }
}

/* ---- Bottom Grid ---- */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-5);
  margin-bottom: var(--space-12);
}

@media (max-width: 768px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

/* ---- Guide ---- */
.guide-steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-top: var(--space-4);
}

.guide-step {
  display: flex;
  gap: var(--space-3);
}

.guide-step-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(124, 58, 237, 0.08) 100%);
  color: var(--color-brand);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.guide-step-body strong {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

.guide-step-body p {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 1px;
  line-height: var(--leading-normal);
}

/* ---- Status ---- */
.status-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border-radius: var(--radius-md);
}

.status-item-icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-item-icon.online {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.status-item-icon.offline {
  background: var(--color-border-light);
  color: var(--color-text-weak);
}

.status-item-body {
  flex: 1;
  min-width: 0;
}

.status-item-label {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-weak);
}

.status-item-value {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-body);
}

/* ---- Recent ---- */
.recent-section {
  margin-bottom: var(--space-12);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5) !important;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.recent-item:hover {
  border-color: var(--color-brand);
  box-shadow: var(--shadow-md);
  transform: translateX(2px);
}

.recent-item-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.recent-item-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--color-brand-light);
  color: var(--color-brand);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.recent-item-info {
  min-width: 0;
}

.recent-name {
  display: block;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.recent-meta {
  font-size: var(--text-xs);
  color: var(--color-text-weak);
}

.meta-sep {
  color: var(--color-border);
  margin: 0 3px;
}

.recent-item-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.recent-arrow {
  color: var(--color-text-weak);
  transition: all var(--transition-fast);
}

.recent-item:hover .recent-arrow {
  transform: translateX(2px);
  color: var(--color-brand);
}
</style>
