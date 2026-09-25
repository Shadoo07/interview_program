<template>
  <div class="interview-page">
    <PageHeader
      title="面试准备"
      description="基于简历与 JD 智能生成结构化面试题库，按类型分组训练"
    />

    <!-- Input Section -->
    <div class="card input-card">
      <h3 class="card-title">输入信息</h3>
      <p class="card-description">填写简历和 JD 后生成针对性面试题</p>
      <div class="input-grid">
        <div>
          <label class="form-label">简历内容</label>
          <textarea v-model="resumeInput" class="form-textarea" placeholder="粘贴简历内容…" rows="5" />
        </div>
        <div>
          <label class="form-label">目标岗位 JD</label>
          <textarea v-model="jdInput" class="form-textarea" placeholder="粘贴目标岗位描述…" rows="5" />
        </div>
      </div>
      <button class="btn btn-primary" style="margin-top: 16px;" :disabled="!resumeInput.trim() || !jdInput.trim() || loading" @click="generateQuestions">
        <el-icon v-if="!loading" :size="18"><MagicStick /></el-icon>
        {{ loading ? (progressStep === 'generating_questions' ? 'AI 正在生成面试题…' : 'AI 正在生成自我介绍…') : '生成面试题库' }}
      </button>
      <div v-if="errorMessage" class="error-banner" style="margin-top: 12px;">
        <el-icon :size="16"><WarningFilled /></el-icon>
        {{ errorMessage }}
      </div>
    </div>

    <!-- Streaming Progress -->
    <div v-if="streamingActive && !store.interviewQuestions" class="card" style="margin-bottom: 16px;">
      <div class="loading-spinner">
        <span>{{ progressStep === 'generating_questions' ? 'AI 正在生成面试题...' : progressStep === 'generating_self_intro' ? 'AI 正在生成自我介绍...' : '准备中...' }}</span>
      </div>
    </div>

    <!-- Streaming Self Intro Preview (while questions are being prepared) -->
    <div v-if="streamingActive && streamingIntro && !store.interviewQuestions" class="card" style="margin-bottom: 16px;">
      <div class="flex-between" style="margin-bottom: 16px;">
        <h4 class="card-title" style="margin-bottom: 0;">
          自我介绍
          <span class="streaming-cursor"></span>
        </h4>
      </div>
      <MarkdownViewer :content="streamingIntro" />
    </div>

    <!-- Results -->
    <template v-if="store.interviewQuestions">
      <div class="card" style="margin-bottom: 16px;">
        <div class="flex-between">
          <div>
            <h3 class="card-title" style="margin-bottom: 2px;">面试题库</h3>
            <p class="card-description">{{ totalQuestionCount }} 道题目 · 按类型分组</p>
          </div>
          <div class="source-badge" :class="store.interviewQuestions.source || 'rules'">
            {{ store.interviewQuestions.source === 'ai' ? 'AI 生成' : '规则模板' }}
          </div>
        </div>
      </div>

      <!-- Category Tabs -->
      <div class="category-tabs">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          class="category-tab"
          :class="{ active: activeCategory === tab.key }"
          @click="activeCategory = tab.key"
        >
          <el-icon :size="15"><component :is="tab.icon" /></el-icon>
          <span>{{ tab.label }}</span>
          <span v-if="getCategoryCount(tab.key)" class="category-count">{{ getCategoryCount(tab.key) }}</span>
        </button>
      </div>

      <!-- Self Intro -->
      <div v-if="activeCategory === 'self_intro'" class="card">
        <div class="flex-between" style="margin-bottom: 16px;">
          <h4 class="card-title" style="margin-bottom: 0;">
            自我介绍
            <span v-if="streamingActive && streamingIntro" class="streaming-cursor"></span>
          </h4>
          <button
            v-if="!streamingActive"
            class="btn btn-ghost btn-sm"
            @click="copyContent(store.interviewQuestions?.self_intro || '')"
          >
            <el-icon :size="14"><CopyDocument /></el-icon>
            复制
          </button>
        </div>
        <MarkdownViewer
          :content="streamingActive ? streamingIntro : (store.interviewQuestions?.self_intro || '')"
          :show-copy="true"
        />
      </div>

      <!-- Question Cards -->
      <div v-else class="questions-list">
        <EmptyState
          v-if="currentQuestions.length === 0"
          title="暂无此类问题"
          description="该类别下暂未生成题目"
          :icon="ChatDotRound"
        />
        <div v-for="(q, idx) in currentQuestions" :key="idx" class="question-card card">
          <div class="question-top">
            <span class="question-number">Q{{ idx + 1 }}</span>
            <span class="badge" :class="difficultyBadge(q.difficulty)">
              {{ q.difficulty }}
            </span>
            <span class="question-focus">
              <el-icon :size="14"><Aim /></el-icon>
              {{ q.focus_point }}
            </span>
          </div>
          <h4 class="question-text">{{ q.question }}</h4>

          <div class="question-sections">
            <div class="question-section">
              <span class="section-label">
                <el-icon :size="14"><ChatLineSquare /></el-icon>
                回答思路
              </span>
              <div class="section-content">{{ q.answer_guide }}</div>
            </div>
            <div class="question-section warning">
              <span class="section-label">
                <el-icon :size="14"><Warning /></el-icon>
                注意事项
              </span>
              <div class="section-content warning-text">{{ q.notes }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Empty -->
    <EmptyState
      v-if="!store.interviewQuestions && !loading"
      title="还没有面试题库"
      description="在上方输入简历和岗位 JD，AI 将自动生成结构化面试题库，包含项目深挖、技术基础、系统设计等多种题型"
      :icon="ChatDotRound"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useResumeStore } from '@/stores/resume'
import { streamPost } from '@/api'
import {
  MagicStick, WarningFilled, ChatDotRound, Aim,
  Document, Monitor, Connection, Warning, Avatar, CopyDocument,
  ChatLineSquare
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import MarkdownViewer from '@/components/MarkdownViewer.vue'

const store = useResumeStore()

const activeCategory = ref('project_deep_dive')
const resumeInput = ref('')
const jdInput = ref('')
const loading = ref(false)
const errorMessage = ref('')
const streamingIntro = ref('')
const streamingActive = ref(false)
const progressStep = ref('')

type QC = 'project_deep_dive' | 'tech_theory' | 'system_design' | 'project_difficulties' | 'hr_general' | 'self_intro'
type QCL = Exclude<QC, 'self_intro'>

const categoryTabs: Array<{ key: QC; label: string; icon: any }> = [
  { key: 'project_deep_dive',    label: '项目深挖',     icon: Document },
  { key: 'tech_theory',          label: '技术基础',     icon: Monitor },
  { key: 'system_design',        label: '系统设计',     icon: Connection },
  { key: 'project_difficulties', label: '项目难点',     icon: Warning },
  { key: 'hr_general',           label: '行为面试',     icon: Avatar },
  { key: 'self_intro',           label: '自我介绍',     icon: ChatDotRound },
]

const currentQuestions = computed(() => {
  if (!store.interviewQuestions) return []
  if (activeCategory.value === 'self_intro') return []
  const cat = activeCategory.value as QCL
  return store.interviewQuestions[cat] || []
})

const totalQuestionCount = computed(() => {
  if (!store.interviewQuestions) return 0
  const cats: QCL[] = ['project_deep_dive', 'tech_theory', 'system_design', 'project_difficulties', 'hr_general']
  return cats.reduce((sum, cat) => sum + (store.interviewQuestions?.[cat]?.length || 0), 0)
})

const getCategoryCount = (key: QC): number => {
  if (key === 'self_intro') return 0
  return (store.interviewQuestions?.[key as QCL] || []).length
}

const difficultyBadge = (d: string): string => {
  if (d === '简单' || d === 'Easy') return 'badge-success'
  if (d === '困难' || d === 'Hard') return 'badge-danger'
  return 'badge-warning'
}

const copyContent = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch { /* ignore */ }
}

const generateQuestions = async () => {
  if (!resumeInput.value.trim() || !jdInput.value.trim()) return
  loading.value = true
  errorMessage.value = ''
  streamingIntro.value = ''
  streamingActive.value = true
  progressStep.value = ''
  store.setInterviewQuestions(null)

  const payload = {
    resume_data: parseResume(resumeInput.value),
    jd_data: parseJd(jdInput.value),
    raw_text: resumeInput.value
  }

  try {
    await streamPost(
      '/interview/questions/stream',
      payload,
      (chunk) => { streamingIntro.value += chunk },
      (step) => { progressStep.value = step },
      (result) => {
        store.setInterviewQuestions(result)
        streamingActive.value = false
        loading.value = false
      },
      (error) => {
        errorMessage.value = error
        streamingActive.value = false
        loading.value = false
      }
    )
  } catch (error: any) {
    errorMessage.value = error.message || '生成失败'
    streamingActive.value = false
    loading.value = false
  }
}

const parseResume = (c: string): object => ({
  basic_info: { name: '求职者' },
  skills: [{ category: '技能', items: extractSkills(c) }],
  projects: extractProjects(c),
  education: [{ school: 'XX大学', degree: '本科' }],
  internships: []
})

const parseJd = (c: string): object => ({
  position_title: extractTitle(c),
  position_type: '后端开发',
  required_skills: extractSkills(c),
  responsibilities: extractResp(c),
  experience_requirement: '3年',
  education_requirement: '本科'
})

const extractSkills = (c: string): string[] =>
  ['Python','Java','JavaScript','Vue','React','Django','Flask','MySQL','Redis','Docker','Git','Linux'].filter(k => c.includes(k))

const extractProjects = (_content: string): object[] =>
  [{ name: '个人项目', description: '负责开发', technologies: [] }]

const extractTitle = (c: string): string => {
  for (const l of c.split('\n')) if (l.includes('招聘')||l.includes('岗位')||l.includes('工程师')) return l.trim()
  return '软件开发工程师'
}

const extractResp = (c: string): string[] => c.split('\n').filter(l => l.includes('负责')||l.includes('开发')).slice(0, 5)

onMounted(() => {
  store.restoreFromStorage()
  resumeInput.value = store.resumeText
  jdInput.value = store.jdText
})
</script>

<style scoped>
.interview-page {
  max-width: 900px;
  margin: 0 auto;
}

.input-card {
  margin-bottom: var(--space-5);
}

.input-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-top: var(--space-4);
}

@media (max-width: 640px) {
  .input-grid { grid-template-columns: 1fr; }
}

/* Category Tabs */
.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
}

.category-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.category-tab:hover {
  border-color: var(--color-brand);
  color: var(--color-brand);
  background: var(--color-brand-light);
}

.category-tab.active {
  background: var(--gradient-brand);
  border-color: transparent;
  color: #FFFFFF;
  box-shadow: 0 2px 12px rgba(37, 99, 235, 0.30);
}

.category-count {
  font-size: 11px;
  background: rgba(255,255,255,0.25);
  padding: 1px 7px;
  border-radius: var(--radius-full);
  font-weight: var(--weight-semibold);
}

/* Question Cards */
.questions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.question-card {
  padding: var(--space-5);
}

.question-top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
  flex-wrap: wrap;
}

.question-number {
  font-size: var(--text-xs);
  font-weight: var(--weight-bold);
  color: var(--color-brand);
  background: var(--color-brand-light);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
}

.question-focus {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--color-purple);
  font-weight: var(--weight-medium);
  background: var(--color-purple-light);
  padding: 3px 10px;
  border-radius: var(--radius-full);
}

.question-text {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  line-height: var(--leading-normal);
  margin-bottom: var(--space-4);
}

.question-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.question-section {
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
}

.question-section.warning {
  background: var(--color-warning-light);
  border: 1px solid var(--color-warning-soft);
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.question-section.warning .section-label {
  color: #92400E;
}

.section-content {
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text-body);
  white-space: pre-wrap;
}

.warning-text {
  color: #92400E;
}

.streaming-cursor {
  display: inline-block;
  width: 8px;
  height: 18px;
  background: var(--color-brand);
  border-radius: 2px;
  animation: blink 0.8s infinite;
  vertical-align: middle;
  margin-left: 6px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
