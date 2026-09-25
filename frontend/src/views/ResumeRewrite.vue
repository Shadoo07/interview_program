<template>
  <div class="rewrite-page">
    <PageHeader
      title="简历改写"
      description="选择合适的改写模式，AI 将根据目标岗位优化简历结构与表达"
    />

    <div class="rewrite-layout">
      <!-- Left: Mode Selection -->
      <div class="rewrite-left">
        <div class="card">
          <h3 class="card-title">改写模式</h3>
          <p class="card-description">选择适合投递场景的优化方向</p>
          <div class="mode-list">
            <div
              v-for="(item, id) in modeItems"
              :key="id"
              class="mode-option"
              :class="{ active: selectedMode === id }"
              @click="selectedMode = id"
            >
              <div class="mode-option-left">
                <el-icon :size="18"><component :is="item.icon" /></el-icon>
              </div>
              <div class="mode-option-body">
                <strong>{{ item.label }}</strong>
                <p>{{ item.desc }}</p>
              </div>
              <div class="mode-radio" :class="{ checked: selectedMode === id }" />
            </div>
          </div>
        </div>
      </div>

      <!-- Center: Resume Input -->
      <div class="rewrite-center">
        <div class="card">
          <h3 class="card-title">原始简历</h3>
          <p class="card-description">粘贴或从简历分析页导入</p>
          <textarea
            v-model="resumeInput"
            class="form-textarea"
            placeholder="在此粘贴简历内容，或从简历分析页自动导入..."
            rows="14"
          ></textarea>
        </div>

        <div class="card" style="margin-top: 16px;">
          <h3 class="card-title">目标 JD（可选）</h3>
          <p class="card-description">粘贴目标岗位描述以获得更精准的改写</p>
          <textarea
            v-model="jdInput"
            class="form-textarea"
            placeholder="粘贴目标岗位描述..."
            rows="6"
          ></textarea>
        </div>

        <button
          class="btn btn-primary"
          style="width: 100%; margin-top: 12px;"
          :disabled="!resumeInput.trim() || loading"
          @click="generateRewrite"
        >
          <el-icon v-if="!loading" :size="18"><MagicStick /></el-icon>
          {{ loading ? 'AI 正在改写...' : '开始智能改写' }}
        </button>

        <div v-if="errorMessage" class="error-banner" style="margin-top: 12px;">
          <el-icon :size="16"><WarningFilled /></el-icon>
          <span>{{ errorMessage }}</span>
        </div>
      </div>

      <!-- Right: Result Preview -->
      <div class="rewrite-right">
        <!-- Empty State -->
        <div v-if="!store.rewriteResult && !loading" class="glass-card rewrite-empty">
          <div class="rewrite-empty-icon">
            <el-icon :size="36"><MagicStick /></el-icon>
          </div>
          <h3 class="rewrite-empty-title">AI 改写结果</h3>
          <p class="rewrite-empty-desc">
            选择改写模式并输入简历内容，AI 将自动重构项目亮点、优化关键词密度并生成更适合投递的版本。
          </p>
          <div class="rewrite-empty-hints">
            <span class="hint-tag">优化项目表达</span>
            <span class="hint-tag">量化成果数据</span>
            <span class="hint-tag">强化关键词</span>
            <span class="hint-tag">匹配 JD 要求</span>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading && !streamingActive" class="loading-spinner">
          <span>AI 正在生成改写版本…</span>
        </div>

        <!-- Streaming Progress -->
        <div v-if="streamingActive && progressStep" class="loading-spinner">
          <span>{{ progressStep === 'analyzing' ? '正在分析简历...' : 'AI 正在改写...' }}</span>
        </div>

        <!-- Streaming Preview -->
        <div v-if="streamingActive && streamingContent" class="card" style="margin-bottom: 12px;">
          <div class="flex-between" style="margin-bottom: 12px;">
            <h4 class="card-title" style="margin-bottom: 0;">AI 正在生成...</h4>
            <span class="streaming-cursor"></span>
          </div>
          <MarkdownViewer :content="streamingContent" />
        </div>

        <!-- Result -->
        <template v-if="store.rewriteResult">
          <div class="card" style="margin-bottom: 12px;">
            <div class="flex-between">
              <h3 class="card-title" style="margin-bottom: 0;">改写结果</h3>
              <div class="source-badge" :class="store.rewriteResult.source || 'rules'">
                {{ store.rewriteResult.source === 'ai' ? 'AI 生成' : '规则模板' }}
              </div>
            </div>
          </div>

          <!-- Rewritten Content -->
          <div class="card" style="margin-bottom: 12px;">
            <div class="flex-between" style="margin-bottom: 12px;">
              <h4 class="card-title" style="margin-bottom: 0;">优化后简历</h4>
              <button class="btn btn-ghost btn-sm" @click="copyContent(store.rewriteResult.rewritten_content || '')">
                <el-icon :size="14"><CopyDocument /></el-icon>
                一键复制
              </button>
            </div>
            <MarkdownViewer :content="store.rewriteResult.rewritten_content || ''" />
          </div>

          <!-- Analysis -->
          <ResultCard title="原始问题分析" v-if="store.rewriteResult.original_analysis">
            <p style="font-size: 14px; line-height: 1.7; color: var(--color-text-body); white-space: pre-wrap;">
              {{ store.rewriteResult.original_analysis }}
            </p>
          </ResultCard>

          <!-- Reasons -->
          <ResultCard
            v-if="store.rewriteResult.rewrite_reasons?.length"
            title="改写理由"
            variant="success"
            :badge="`${store.rewriteResult.rewrite_reasons.length} 条`"
          >
            <ul class="result-list">
              <li v-for="(reason, idx) in store.rewriteResult.rewrite_reasons" :key="idx">{{ reason }}</li>
            </ul>
          </ResultCard>

          <!-- Notes -->
          <ResultCard
            v-if="store.rewriteResult.notes?.length"
            title="注意事项"
            variant="warning"
          >
            <ul class="result-list">
              <li v-for="(note, idx) in store.rewriteResult.notes" :key="idx">{{ note }}</li>
            </ul>
          </ResultCard>

          <!-- Project Experience -->
          <div class="card" style="margin-top: 12px;" v-if="store.rewriteResult.project_experience_text">
            <div class="flex-between" style="margin-bottom: 12px;">
              <h4 class="card-title" style="margin-bottom: 0;">项目经历文本</h4>
              <button class="btn btn-ghost btn-sm" @click="copyContent(store.rewriteResult.project_experience_text || '')">
                <el-icon :size="14"><CopyDocument /></el-icon>
                复制
              </button>
            </div>
            <pre class="pre-block">{{ store.rewriteResult.project_experience_text }}</pre>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useResumeStore } from '@/stores/resume'
import { streamPost } from '@/api'
import {
  MagicStick, WarningFilled, CopyDocument,
  Cpu, DataAnalysis, TrendCharts, Star, Files
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ResultCard from '@/components/ResultCard.vue'
import MarkdownViewer from '@/components/MarkdownViewer.vue'

const store = useResumeStore()

const selectedMode = ref('big_company_intern')
const resumeInput = ref('')
const jdInput = ref('')
const loading = ref(false)
const errorMessage = ref('')
const streamingContent = ref('')
const streamingActive = ref(false)
const progressStep = ref('')

const modeItems: Record<string, { label: string; desc: string; icon: any }> = {
  big_company_intern: {
    label: '大厂实习投递版',
    desc: '突出项目亮点与技术深度，适配大厂实习岗筛选标准',
    icon: TrendCharts
  },
  backend_developer: {
    label: '后端开发岗位版',
    desc: '强化后端技术栈与系统设计经验，匹配后端岗位 JD',
    icon: Cpu
  },
  ai_developer: {
    label: 'AI 应用开发岗位版',
    desc: '强调 AI/ML 项目实践与模型应用能力',
    icon: MagicStick
  },
  project_enhance: {
    label: '项目经历强化版',
    desc: '深度展开项目背景、技术方案与量化成果',
    icon: DataAnalysis
  },
  hr_friendly: {
    label: 'HR 初筛友好版',
    desc: '优化排版与关键词密度，提高 HR 初筛通过率',
    icon: Star
  },
  one_page: {
    label: '简洁一页版',
    desc: '精简至一页，保留最核心的竞争力信息',
    icon: Files
  }
}

const generateRewrite = async () => {
  if (!resumeInput.value.trim()) return
  loading.value = true
  errorMessage.value = ''
  streamingContent.value = ''
  streamingActive.value = true
  progressStep.value = ''
  store.setRewriteResult(null)

  const payload = {
    resume_data: parseResumeContent(resumeInput.value),
    jd_data: jdInput.value.trim() ? parseJdContent(jdInput.value) : {},
    raw_text: resumeInput.value,
    rewrite_mode: selectedMode.value
  }

  try {
    await streamPost(
      '/resume/rewrite/stream',
      payload,
      (chunk) => { streamingContent.value += chunk },
      (step) => { progressStep.value = step },
      (result) => {
        store.setRewriteResult(result)
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
    errorMessage.value = error.message || '生成失败，请重试'
    streamingActive.value = false
    loading.value = false
  }
}

const parseResumeContent = (content: string): object => ({
  basic_info: { name: '求职者' },
  skills: [{ category: '技能', items: extractSkills(content) }],
  projects: extractProjects(content),
  education: [{ school: 'XX大学', degree: '本科' }],
  internships: []
})

const parseJdContent = (content: string): object => ({
  position_title: extractPositionTitle(content),
  position_type: '后端开发',
  required_skills: extractSkills(content),
  responsibilities: extractResponsibilities(content),
  experience_requirement: '3年',
  education_requirement: '本科'
})

const extractSkills = (content: string): string[] => {
  const keywords = ['Python', 'Java', 'JavaScript', 'Vue', 'React', 'Django', 'Flask', 'MySQL', 'Redis', 'Docker']
  return keywords.filter(kw => content.includes(kw))
}

const extractProjects = (content: string): object[] => {
  const lines = content.split('\n')
  const projects: object[] = []
  let current: string[] = []
  for (const line of lines) {
    if (line.includes('项目') || line.includes('Project')) {
      if (current.length > 0) projects.push({ name: current.join(' '), description: current.join(' ') })
      current = [line]
    } else if (current.length > 0) {
      current.push(line)
    }
  }
  if (current.length > 0) projects.push({ name: current.join(' ').slice(0, 30), description: current.join(' ') })
  return projects.length > 0 ? projects : [{ name: '个人项目', description: '项目描述' }]
}

const extractPositionTitle = (content: string): string => {
  for (const line of content.split('\n')) {
    if (line.includes('招聘') || line.includes('岗位') || line.includes('工程师')) return line.trim()
  }
  return '软件开发工程师'
}

const extractResponsibilities = (content: string): string[] =>
  content.split('\n').filter(l => l.includes('负责') || l.includes('开发')).slice(0, 5)

const copyContent = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch { /* ignore */ }
}

onMounted(() => {
  store.restoreFromStorage()
  resumeInput.value = store.resumeText
  jdInput.value = store.jdText
})
</script>

<style scoped>
.rewrite-page {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

.rewrite-layout {
  display: grid;
  grid-template-columns: 280px 1fr 1fr;
  gap: var(--space-6);
  align-items: start;
}

@media (max-width: 1200px) {
  .rewrite-layout {
    grid-template-columns: 1fr 1fr;
  }
  .rewrite-left {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .rewrite-layout {
    grid-template-columns: 1fr;
  }
}

/* Mode Options */
.mode-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.mode-option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-option:hover {
  border-color: var(--color-brand);
  background: var(--color-brand-light);
}

.mode-option.active {
  border-color: var(--color-brand);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.06) 0%, rgba(124, 58, 237, 0.04) 100%);
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.15);
}

.mode-option-left {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.mode-option.active .mode-option-left {
  background: var(--color-brand-light);
  color: var(--color-brand);
}

.mode-option-body {
  flex: 1;
  min-width: 0;
}

.mode-option-body strong {
  display: block;
  font-size: var(--text-sm);
  color: var(--color-text);
  font-weight: var(--weight-semibold);
}

.mode-option-body p {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 1px;
  line-height: var(--leading-normal);
}

.mode-radio {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.mode-radio.checked {
  border-color: var(--color-brand);
  border-width: 5px;
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.3);
}

/* Empty State */
.rewrite-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-12) var(--space-8);
  min-height: 360px;
  justify-content: center;
}

.rewrite-empty-icon {
  width: 72px;
  height: 72px;
  border-radius: var(--radius-2xl);
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(124, 58, 237, 0.06) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-purple);
  margin-bottom: var(--space-5);
}

.rewrite-empty-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-3);
}

.rewrite-empty-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: var(--leading-relaxed);
  max-width: 320px;
  margin-bottom: var(--space-5);
}

.rewrite-empty-hints {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
}

.hint-tag {
  padding: 4px 10px;
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-brand);
  background: var(--color-brand-light);
  border-radius: var(--radius-full);
  border: 1px solid rgba(37, 99, 235, 0.1);
}

/* Result */
.result-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.result-list li {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-text-body);
}

.pre-block {
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text-body);
  white-space: pre-wrap;
  font-family: var(--font-family);
}

.streaming-cursor {
  display: inline-block;
  width: 8px;
  height: 18px;
  background: var(--color-brand);
  border-radius: 2px;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
