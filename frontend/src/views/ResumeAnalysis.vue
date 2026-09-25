<template>
  <div class="analysis-page">
    <PageHeader
      title="简历分析"
      description="上传简历与岗位 JD，多 Agent 并行诊断并生成优化方案"
    />

    <!-- Step Indicator -->
    <StepPanel :steps="stepLabels" :current-step="currentStep" />

    <!-- Loading -->
    <div v-if="loading" class="loading-spinner">
      <span>{{ loadingText }}</span>
    </div>

    <!-- Error -->
    <div v-if="errorMessage" class="error-banner">
      <el-icon :size="16"><WarningFilled /></el-icon>
      <span>{{ errorMessage }}</span>
      <button class="btn btn-ghost btn-sm" style="margin-left: auto;" @click="errorMessage = ''">关闭</button>
    </div>

    <div class="analysis-layout">
      <!-- Main Column -->
      <div class="analysis-main">
        <!-- Step 1: Upload Resume -->
        <section v-show="currentStep >= 0" class="step-section card">
          <div class="step-section-header">
            <div>
              <h3 class="step-section-title">
                <span class="step-num">01</span>
                上传简历
              </h3>
              <p class="step-section-desc">支持 PDF、DOCX、TXT 格式，最大 10MB</p>
            </div>
            <span v-if="store.fileId" class="badge badge-success">已完成</span>
          </div>

          <div v-if="store.fileId && store.resumeFileName" class="file-uploaded">
            <div class="file-uploaded-icon">
              <el-icon :size="20"><Document /></el-icon>
            </div>
            <div class="file-uploaded-info">
              <span class="file-uploaded-name">{{ store.resumeFileName }}</span>
              <span class="file-uploaded-meta">已上传 · 待解析</span>
            </div>
            <label class="btn btn-ghost btn-sm">
              <input type="file" @change="handleFileSelect" accept=".pdf,.docx,.txt" hidden />
              重新选择
            </label>
          </div>
          <div v-else class="upload-zone-glass" :class="{ 'is-dragover': isDragover }"
            @dragover.prevent="isDragover = true"
            @dragleave.prevent="isDragover = false"
            @drop.prevent="handleDrop">
            <el-icon :size="44" class="upload-zone-icon"><UploadFilled /></el-icon>
            <p class="upload-zone-text">拖拽简历文件到此处</p>
            <label class="btn btn-primary" style="margin-top: 16px;">
              <input type="file" @change="handleFileSelect" accept=".pdf,.docx,.txt" hidden />
              <el-icon :size="16"><Upload /></el-icon>
              选择文件
            </label>
            <p class="upload-zone-hint">PDF / DOCX / TXT</p>
          </div>

          <div v-if="store.fileId && !store.resumeData" style="margin-top: 16px;">
            <button class="btn btn-primary" :disabled="parsing" @click="parseResume">
              <el-icon v-if="!parsing" :size="16"><MagicStick /></el-icon>
              {{ parsing ? '正在解析简历...' : '开始解析' }}
            </button>
          </div>
        </section>

        <!-- Step 2: Input JD -->
        <section v-if="store.resumeData" class="step-section card">
          <div class="step-section-header">
            <div>
              <h3 class="step-section-title">
                <span class="step-num">02</span>
                输入目标 JD
              </h3>
              <p class="step-section-desc">粘贴目标岗位描述，系统将提取关键技能与要求</p>
            </div>
            <span v-if="store.jdData" class="badge badge-success">已完成</span>
          </div>

          <textarea
            v-model="jdInput"
            class="form-textarea"
            placeholder="在此粘贴目标岗位描述（JD），支持从招聘网站直接复制粘贴..."
            rows="6"
          ></textarea>
          <button class="btn btn-primary" style="margin-top: 12px;"
            :disabled="!jdInput.trim() || analyzing" @click="analyzeJD">
            <el-icon v-if="!analyzing" :size="16"><Search /></el-icon>
            {{ analyzing ? '分析中...' : '分析 JD' }}
          </button>
        </section>

        <!-- Step 3: Multi-Agent Diagnosis -->
        <section v-if="store.jdData" class="step-section card">
          <div class="step-section-header">
            <div>
              <h3 class="step-section-title">
                <span class="step-num">03</span>
                多 Agent 诊断
              </h3>
              <p class="step-section-desc">HR 初筛官、技术面试官、简历编辑专家三视角并行分析</p>
            </div>
          </div>

          <div class="step-actions">
            <button class="btn btn-primary" :disabled="analyzing" @click="analyzeMatch">
              <el-icon :size="16"><Connection /></el-icon>
              开始匹配分析
            </button>
            <button class="btn btn-secondary" :disabled="analyzing || !store.resumeText || !store.jdText" @click="diagnoseResume">
              <el-icon :size="16"><ChatLineSquare /></el-icon>
              多视角诊断
            </button>
          </div>
        </section>

        <!-- Match Result -->
        <section v-if="store.matchResult" class="result-section card">
          <div class="card-header">
            <h3 class="card-title">匹配度分析结果</h3>
            <div v-if="store.matchResult.source" class="source-badge" :class="store.matchResult.source">
              {{ store.matchResult.source === 'ai' ? 'AI 生成' : '规则模板' }}
            </div>
          </div>

          <div class="match-overall">
            <div class="match-score-ring">
              <svg viewBox="0 0 100 100" class="score-ring">
                <defs>
                  <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" :stop-color="scoreGradientStart" />
                    <stop offset="100%" :stop-color="scoreGradientEnd" />
                  </linearGradient>
                </defs>
                <circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-border-light)" stroke-width="7" />
                <circle cx="50" cy="50" r="42" fill="none" stroke="url(#scoreGradient)"
                  stroke-width="7" stroke-linecap="round"
                  :stroke-dasharray="264"
                  :stroke-dashoffset="264 - (264 * (store.matchResult.overall_score || 0) / 100)"
                  transform="rotate(-90 50 50)" />
              </svg>
              <div class="match-score-content">
                <span class="match-score-num">{{ store.matchResult.overall_score || 0 }}</span>
                <span class="match-score-unit">分</span>
              </div>
            </div>
            <div class="match-level-tag">
              <span class="badge" :class="matchLevelBadge">{{ getMatchLevel(store.matchResult.overall_score) }}</span>
              <p class="match-level-desc">{{ getMatchLevelDesc(store.matchResult.overall_score) }}</p>
            </div>
          </div>

          <div class="dimension-scores" v-if="dimensionScores.length > 0">
            <ScoreCard
              v-for="item in dimensionScores"
              :key="item.label"
              :label="item.label"
              :score="item.score"
            />
          </div>

          <div class="keywords-row" v-if="store.matchResult.matched_keywords?.length || store.matchResult.missing_keywords?.length">
            <div class="keywords-group" v-if="store.matchResult.matched_keywords?.length">
              <h4 class="keywords-title">匹配关键词</h4>
              <KeywordTags :tags="store.matchResult.matched_keywords" type="matched" />
            </div>
            <div class="keywords-group" v-if="store.matchResult.missing_keywords?.length">
              <h4 class="keywords-title">技能缺口</h4>
              <KeywordTags :tags="store.matchResult.missing_keywords" type="missing" />
            </div>
          </div>

          <div v-if="store.matchResult.weak_points?.length" style="margin-top: 20px;">
            <ResultCard title="简历短板" variant="danger" :badge="`${store.matchResult.weak_points.length} 项`">
              <ul class="result-list">
                <li v-for="(point, idx) in store.matchResult.weak_points" :key="idx">{{ point }}</li>
              </ul>
            </ResultCard>
          </div>

          <div v-if="store.matchResult.suggestions?.length" style="margin-top: 12px;">
            <ResultCard title="优化建议" variant="success" :badge="`${store.matchResult.suggestions.length} 条`">
              <ul class="result-list">
                <li v-for="(sug, idx) in store.matchResult.suggestions" :key="idx">{{ sug }}</li>
              </ul>
            </ResultCard>
          </div>
        </section>

        <!-- Multi-Perspective Diagnosis -->
        <section v-if="store.diagnoseResult" class="result-section card" style="margin-top: 20px;">
          <div class="card-header">
            <h3 class="card-title">多 Agent 诊断报告</h3>
            <div class="source-badge" :class="store.diagnoseResult.source || 'rules'">
              {{ store.diagnoseResult.source === 'ai' ? 'AI 生成' : '规则模板' }}
            </div>
          </div>

          <div class="perspective-grid">
            <ResultCard title="HR 初筛官 · 诊断" variant="warning" v-if="store.diagnoseResult.strengths?.length">
              <div class="perspective-content">
                <h4>简历优势</h4>
                <ul class="result-list">
                  <li v-for="(s, idx) in store.diagnoseResult.strengths" :key="idx">
                    <strong>{{ s.point }}</strong>
                    <p>{{ s.detail }}</p>
                  </li>
                </ul>
              </div>
            </ResultCard>

            <ResultCard title="技术面试官 · 诊断" variant="danger" v-if="store.diagnoseResult.weaknesses?.length">
              <div class="perspective-content">
                <h4>待提升领域</h4>
                <ul class="result-list">
                  <li v-for="(w, idx) in store.diagnoseResult.weaknesses" :key="idx">
                    <strong>{{ w.point }}</strong>
                    <p>{{ w.detail }}</p>
                  </li>
                </ul>
              </div>
            </ResultCard>

            <ResultCard title="简历编辑专家 · 诊断" variant="success" v-if="store.diagnoseResult.improvements?.length">
              <div class="perspective-content">
                <h4>改进方案</h4>
                <ul class="result-list">
                  <li v-for="(imp, idx) in store.diagnoseResult.improvements" :key="idx">
                    <strong>{{ imp.area }}</strong>
                    <span class="badge badge-neutral" style="margin-left: 8px;">{{ imp.priority }}</span>
                    <p>{{ imp.suggestion }}</p>
                  </li>
                </ul>
              </div>
            </ResultCard>
          </div>
        </section>

        <!-- Bottom Actions -->
        <div v-if="hasData" class="bottom-actions">
          <button class="btn btn-secondary" @click="saveToHistory">
            <el-icon :size="16"><FolderAdd /></el-icon>
            保存到历史记录
          </button>
          <button class="btn btn-primary" @click="goToRewrite">
            <el-icon :size="16"><Edit /></el-icon>
            前往简历改写
          </button>
        </div>
      </div>

      <!-- Side Panel: Parse Status -->
      <aside v-if="store.fileId" class="analysis-sidebar">
        <div class="glass-card parse-status-panel">
          <h4 class="parse-status-title">解析状态</h4>
          <div class="parse-status-list">
            <div class="parse-status-item" :class="{ done: store.resumeData }">
              <el-icon :size="14">
                <CircleCheckFilled v-if="store.resumeData" />
                <Loading v-else-if="parsing" class="is-loading" />
                <Clock v-else />
              </el-icon>
              <span>识别教育经历</span>
            </div>
            <div class="parse-status-item" :class="{ done: store.resumeData }">
              <el-icon :size="14">
                <CircleCheckFilled v-if="store.resumeData" />
                <Clock v-else />
              </el-icon>
              <span>识别项目经历</span>
            </div>
            <div class="parse-status-item" :class="{ done: store.resumeData }">
              <el-icon :size="14">
                <CircleCheckFilled v-if="store.resumeData" />
                <Clock v-else />
              </el-icon>
              <span>提取技术关键词</span>
            </div>
            <div class="parse-status-item" :class="{ done: store.jdData }">
              <el-icon :size="14">
                <CircleCheckFilled v-if="store.jdData" />
                <Clock v-else />
              </el-icon>
              <span>JD 技能分析</span>
            </div>
            <div class="parse-status-item" :class="{ done: store.matchResult }">
              <el-icon :size="14">
                <CircleCheckFilled v-if="store.matchResult" />
                <Clock v-else />
              </el-icon>
              <span>匹配度计算</span>
            </div>
            <div class="parse-status-item" :class="{ done: store.diagnoseResult }">
              <el-icon :size="14">
                <CircleCheckFilled v-if="store.diagnoseResult" />
                <Clock v-else />
              </el-icon>
              <span>多 Agent 诊断</span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useResumeStore } from '@/stores/resume'
import { resumeApi, jdApi, matchApi, agentApi, historyApi } from '@/api'
import {
  WarningFilled, Upload, UploadFilled, Document, Connection, Search,
  ChatLineSquare, FolderAdd, Edit, MagicStick,
  CircleCheckFilled, Loading, Clock
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import StepPanel from '@/components/StepPanel.vue'
import ScoreCard from '@/components/ScoreCard.vue'
import KeywordTags from '@/components/KeywordTags.vue'
import ResultCard from '@/components/ResultCard.vue'

const router = useRouter()
const store = useResumeStore()

const stepLabels = ['上传简历', '输入 JD', '多 Agent 诊断', '生成优化方案']
const currentStep = ref(0)
const loading = ref(false)
const loadingText = ref('')
const errorMessage = ref('')
const parsing = ref(false)
const analyzing = ref(false)
const isDragover = ref(false)
const jdInput = ref('')

const hasData = computed(() => store.resumeData || store.jdData)

const dimensionScores = computed(() => {
  return (store.matchResult?.dimension_scores || []).map((item: any) => ({
    label: item.dimension,
    score: item.score
  }))
})

const scoreGradientStart = computed(() => {
  const s = store.matchResult?.overall_score || 0
  if (s >= 80) return '#16A34A'
  if (s >= 60) return '#2563EB'
  if (s >= 40) return '#F59E0B'
  return '#DC2626'
})

const scoreGradientEnd = computed(() => {
  const s = store.matchResult?.overall_score || 0
  if (s >= 80) return '#22C55E'
  if (s >= 60) return '#7C3AED'
  if (s >= 40) return '#FBBF24'
  return '#EF4444'
})

const matchLevelBadge = computed(() => {
  const s = store.matchResult?.overall_score || 0
  if (s >= 80) return 'badge-success'
  if (s >= 60) return 'badge-info'
  if (s >= 40) return 'badge-warning'
  return 'badge-danger'
})

const getMatchLevel = (score?: number): string => {
  if (!score) return '未知'
  if (score >= 80) return '优秀'
  if (score >= 60) return '良好'
  if (score >= 40) return '一般'
  return '需提升'
}

const getMatchLevelDesc = (score?: number): string => {
  if (!score) return ''
  if (score >= 80) return '简历与 JD 高度匹配，可直接投递'
  if (score >= 60) return '基本匹配，建议针对性优化后投递'
  if (score >= 40) return '存在明显差距，建议重点补充相关技能'
  return '匹配度较低，建议重新评估目标岗位'
}

const updateStep = () => {
  if (store.matchResult || store.diagnoseResult) currentStep.value = 3
  else if (store.jdData) currentStep.value = 2
  else if (store.fileId && store.resumeData) currentStep.value = 2
  else if (store.fileId) currentStep.value = 1
  else currentStep.value = 0
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) await uploadFile(target.files[0])
}

const handleDrop = async (event: DragEvent) => {
  isDragover.value = false
  if (event.dataTransfer?.files[0]) await uploadFile(event.dataTransfer.files[0])
}

const uploadFile = async (file: File) => {
  loading.value = true; loadingText.value = '上传中...'; errorMessage.value = ''
  try {
    const response = await resumeApi.upload(file)
    if (response.data.code === 200) {
      store.setFileId(response.data.data.file_id)
      store.setResumeFileName(file.name)
      updateStep()
    } else {
      errorMessage.value = response.data.message
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '上传失败'
  } finally { loading.value = false }
}

const parseResume = async () => {
  if (!store.fileId) return
  parsing.value = true; errorMessage.value = ''
  try {
    const parseResp = await resumeApi.parse(store.fileId)
    if (parseResp.data.code === 200) {
      const rawText = parseResp.data.data?.raw_text || ''
      const structResp = await resumeApi.structure(rawText)
      if (structResp.data.code === 200) {
        store.setResumeText(rawText)
        store.setResumeData(structResp.data.data)
        updateStep()
      } else {
        errorMessage.value = structResp.data.message
      }
    } else {
      errorMessage.value = parseResp.data.message
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '解析失败'
  } finally { parsing.value = false }
}

const analyzeJD = async () => {
  if (!jdInput.value.trim()) return
  analyzing.value = true; errorMessage.value = ''
  try {
    const response = await jdApi.analyze(jdInput.value)
    if (response.data.code === 200) {
      store.setJdText(jdInput.value)
      store.setJdData(response.data.data)
      updateStep()
    } else {
      errorMessage.value = response.data.message
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '分析失败'
  } finally { analyzing.value = false }
}

const analyzeMatch = async () => {
  if (!store.resumeData || !store.jdData) return
  analyzing.value = true; errorMessage.value = ''
  try {
    const response = await matchApi.analyze(store.resumeData, store.jdData)
    if (response.data.code === 200) {
      store.setMatchResult(response.data.data)
      updateStep()
    } else {
      errorMessage.value = response.data.message
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '匹配分析失败'
  } finally { analyzing.value = false }
}

const diagnoseResume = async () => {
  if (!store.resumeText || !store.jdText) return
  analyzing.value = true; errorMessage.value = ''
  try {
    const response = await agentApi.diagnose(store.resumeText, store.jdText)
    if (response.data.code === 200) {
      store.setDiagnoseResult(response.data.data)
      updateStep()
    } else {
      errorMessage.value = response.data.message
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '诊断失败'
  } finally { analyzing.value = false }
}

const saveToHistory = async () => {
  try {
    await historyApi.save({
      resume_filename: store.resumeFileName,
      raw_text: store.resumeText,
      resume_data: store.resumeData,
      jd_text: store.jdText,
      jd_data: store.jdData,
      match_result: store.matchResult,
      diagnose_result: store.diagnoseResult
    })
    ElMessage.success('已保存到历史记录')
  } catch { /* ignore */ }
}

const goToRewrite = () => router.push('/resume-rewrite')

onMounted(() => {
  store.restoreFromStorage()
  updateStep()
  jdInput.value = store.jdText
})
</script>

<style scoped>
.analysis-page {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

.analysis-layout {
  display: grid;
  grid-template-columns: 1fr 240px;
  gap: var(--space-6);
  align-items: start;
}

@media (max-width: 1024px) {
  .analysis-layout {
    grid-template-columns: 1fr;
  }
  .analysis-sidebar {
    display: none;
  }
}

.analysis-main {
  min-width: 0;
}

/* Step Section */
.step-section {
  margin-bottom: var(--space-5);
}

.step-section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.step-section-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(124, 58, 237, 0.08) 100%);
  color: var(--color-brand);
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.step-section-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-top: 2px;
}

/* File Uploaded */
.file-uploaded {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}

.file-uploaded-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  background: var(--color-brand-light);
  color: var(--color-brand);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-uploaded-info {
  flex: 1;
  min-width: 0;
}

.file-uploaded-name {
  display: block;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.file-uploaded-meta {
  font-size: var(--text-xs);
  color: var(--color-text-weak);
}

/* Step Actions */
.step-actions {
  display: flex;
  gap: var(--space-3);
}

.result-section {
  margin-bottom: var(--space-5);
}

/* Match Overall */
.match-overall {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-6) 0;
  justify-content: center;
}

.match-score-ring {
  position: relative;
  width: 110px;
  height: 110px;
  flex-shrink: 0;
}

.score-ring {
  width: 100%;
  height: 100%;
}

.match-score-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.match-score-num {
  font-size: 32px;
  font-weight: var(--weight-bold);
  color: var(--color-text);
  line-height: 1;
  letter-spacing: -0.03em;
}

.match-score-unit {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.match-level-tag {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.match-level-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  max-width: 180px;
  line-height: var(--leading-normal);
}

/* Dimension Scores */
.dimension-scores {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

/* Keywords */
.keywords-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.keywords-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
}

/* Perspective Grid */
.perspective-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.perspective-content {
  font-size: var(--text-base);
}

.perspective-content h4 {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-3);
}

.result-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.result-list li {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-text-body);
}

.result-list li strong {
  display: block;
  color: var(--color-text);
  font-weight: var(--weight-semibold);
  margin-bottom: 2px;
}

.result-list li p {
  color: var(--color-text-muted);
  margin-top: 2px;
}

.bottom-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  padding: var(--space-8) 0;
}

/* Parse Status Sidebar */
.analysis-sidebar {
  position: sticky;
  top: var(--space-8);
}

.parse-status-panel {
  padding: var(--space-5);
}

.parse-status-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-4);
  letter-spacing: -0.01em;
}

.parse-status-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.parse-status-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.parse-status-item.done {
  color: var(--color-success);
}

.is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
