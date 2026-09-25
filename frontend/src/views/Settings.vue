<template>
  <div class="settings-page">
    <PageHeader
      title="设置"
      description="AI 模型控制台 — 管理大模型连接与生成配置"
    />

    <!-- Loading -->
    <div v-if="loading" class="loading-spinner">
      <span>加载配置…</span>
    </div>

    <template v-else>
      <div class="settings-grid">
        <!-- Model Status -->
        <div class="card settings-card">
          <div class="card-header">
            <div>
              <h3 class="card-title">模型配置</h3>
              <p class="card-description">当前 AI 引擎连接状态</p>
            </div>
            <span class="badge" :class="llmConfig.configured ? 'badge-success' : 'badge-warning'">
              <span class="badge-dot" />
              {{ llmConfig.configured ? '在线' : '离线' }}
            </span>
          </div>

          <div class="config-rows">
            <div class="config-row">
              <span class="config-row-label">API Key</span>
              <span class="config-row-value">
                <template v-if="llmConfig.api_key_preview">
                  <code class="key-masked">{{ maskApiKey(llmConfig.api_key_preview) }}</code>
                </template>
                <span v-else class="text-weak">未设置</span>
              </span>
            </div>
            <div class="config-row">
              <span class="config-row-label">模型预设</span>
              <span class="config-row-value">
                <span class="model-preset">{{ llmConfig.preset_label || llmConfig.preset || '未设置' }}</span>
              </span>
            </div>
            <div class="config-row">
              <span class="config-row-label">API 地址</span>
              <span class="config-row-value">{{ llmConfig.base_url || '未设置' }}</span>
            </div>
            <div class="config-row">
              <span class="config-row-label">模型名称</span>
              <span class="config-row-value">{{ llmConfig.model_name || '未设置' }}</span>
            </div>
            <div class="config-row">
              <span class="config-row-label">生成模式</span>
              <span class="config-row-value">
                <span class="source-badge" :class="llmConfig.configured ? 'ai' : 'rules'">
                  {{ llmConfig.configured ? '大模型生成' : '规则模板生成' }}
                </span>
              </span>
            </div>
          </div>

          <div class="config-banner" :class="llmConfig.configured ? 'success' : 'warning'">
            <el-icon :size="18">
              <CircleCheckFilled v-if="llmConfig.configured" />
              <WarningFilled v-else />
            </el-icon>
            <div>
              <p v-if="llmConfig.configured">大模型已连接，所有 AI 功能使用云端模型生成</p>
              <p v-else>大模型未连接，AI 功能将降级使用规则模板生成。配置后可获得更精准的分析结果。</p>
            </div>
          </div>

          <div class="config-actions">
            <button
              class="btn btn-secondary"
              :disabled="testing"
              @click="testLlmConnection"
            >
              {{ testing ? '测试中…' : '测试模型连接' }}
            </button>
            <p v-if="testResult" class="test-result" :class="testResult.ok ? 'success' : 'error'">
              <el-icon :size="14">
                <CircleCheckFilled v-if="testResult.ok" />
                <CircleCloseFilled v-else />
              </el-icon>
              {{ testResult.message }}
              <span v-if="testResult.latency_ms !== null"> · {{ testResult.latency_ms }}ms</span>
            </p>
          </div>
        </div>

        <!-- Configuration Guide -->
        <div class="card settings-card">
          <h3 class="card-title" style="margin-bottom: 4px;">配置说明</h3>
          <p class="card-description" style="margin-bottom: 20px;">如何在后端配置大模型 API</p>

          <div class="guide-content">
            <p>在后端项目根目录创建 <code>.env</code> 文件，添加以下配置：</p>
            <pre class="code-block">
LLM_MODEL_PRESET=deepseek-v4-pro
DEEPSEEK_API_KEY=your_deepseek_api_key</pre>
            <p style="margin-top: 12px;">
              切换模型时修改 <code>LLM_MODEL_PRESET</code> 即可，支持的预设：
            </p>
            <div class="model-tags">
              <code>deepseek-v4-pro</code>
              <code>deepseek-v4-flash</code>
              <code>gemini-3.0-pro</code>
              <code>gpt-5.5</code>
              <code>qwen3.6-plus</code>
              <code>glm-5.1</code>
            </div>

            <h4 style="margin-top: 24px;">支持的 API</h4>
            <ul>
              <li>DeepSeek API</li>
              <li>Gemini OpenAI-compatible API</li>
              <li>OpenAI API</li>
              <li>Qwen / DashScope</li>
              <li>GLM / 智谱兼容接口</li>
            </ul>

            <h4 style="margin-top: 20px;">功能覆盖</h4>
            <p>配置大模型后，以下功能将使用 AI 生成：</p>
            <ul>
              <li>简历诊断分析 — HR / 技术官 / 编辑 三视角 Agent</li>
              <li>简历智能改写 — 6 种模式适配不同投递场景</li>
              <li>面试问题生成 — 项目深挖 / 技术基础 / 系统设计</li>
            </ul>
            <p style="margin-top: 8px;">未配置或调用失败时，系统自动降级使用规则模板。</p>
          </div>
        </div>

        <!-- System Info -->
        <div class="card settings-card">
          <h3 class="card-title" style="margin-bottom: 4px;">系统信息</h3>
          <p class="card-description" style="margin-bottom: 16px;">当前服务与版本</p>
          <div class="config-rows">
            <div class="config-row">
              <span class="config-row-label">版本</span>
              <span class="config-row-value">v1.0.0</span>
            </div>
            <div class="config-row">
              <span class="config-row-label">服务状态</span>
              <span class="config-row-value" style="color: var(--color-success); font-weight: var(--weight-semibold);">
                <span class="status-dot-live" />
                运行中
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { CircleCheckFilled, WarningFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { healthApi } from '@/api'
import PageHeader from '@/components/PageHeader.vue'

const loading = ref(true)
const testing = ref(false)
const llmConfig = ref({
  configured: false,
  preset: '',
  preset_label: '',
  model_name: '',
  base_url: '',
  api_key_source: '',
  api_key_preview: null as string | null
})
const testResult = ref<{
  ok: boolean
  message: string
  latency_ms: number | null
} | null>(null)

const maskApiKey = (key: string): string => {
  if (!key) return '未设置'
  if (key.length <= 8) return '****'
  return key.substring(0, 4) + '••••••••' + key.substring(key.length - 4)
}

const fetchLlmConfig = async () => {
  loading.value = true
  try {
    const response = await healthApi.getLlmConfig()
    if (response.data.code === 200) {
      llmConfig.value = response.data.data
    }
  } catch {
    // silently fail
  } finally {
    loading.value = false
  }
}

const testLlmConnection = async () => {
  testing.value = true
  testResult.value = null
  try {
    const response = await healthApi.testLlm()
    if (response.data.code === 200) {
      testResult.value = response.data.data.test
      llmConfig.value = response.data.data
    }
  } catch (error: any) {
    testResult.value = {
      ok: false,
      message: error.response?.data?.message || '连接失败',
      latency_ms: null
    }
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  fetchLlmConfig()
})
</script>

<style scoped>
.settings-page {
  max-width: 760px;
  margin: 0 auto;
}

.settings-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
}

/* Config Rows */
.config-rows {
  display: flex;
  flex-direction: column;
}

.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border-light);
}

.config-row:last-child {
  border-bottom: none;
}

.config-row-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.config-row-value {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-body);
  text-align: right;
}

.key-masked {
  background: var(--color-bg);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  letter-spacing: 0.05em;
}

.model-preset {
  color: var(--color-purple);
  font-weight: var(--weight-semibold);
}

/* Banner */
.config-banner {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  margin-top: var(--space-4);
}

.config-banner.success {
  background: linear-gradient(135deg, rgba(240, 253, 244, 0.9) 0%, rgba(220, 252, 231, 0.6) 100%);
  color: var(--color-success);
  border: 1px solid rgba(22, 163, 74, 0.12);
}

.config-banner.warning {
  background: linear-gradient(135deg, rgba(255, 251, 235, 0.9) 0%, rgba(254, 243, 199, 0.6) 100%);
  color: #92400E;
  border: 1px solid rgba(245, 158, 11, 0.12);
}

.config-actions {
  margin-top: var(--space-4);
}

.test-result {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-3);
  font-size: var(--text-sm);
}

.test-result.success {
  color: var(--color-success);
}

.test-result.error {
  color: var(--color-danger);
}

/* Status Dot */
.status-dot-live {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-success);
  margin-right: 4px;
  box-shadow: 0 0 8px rgba(22, 163, 74, 0.5);
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Guide */
.guide-content {
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--color-text-body);
}

.guide-content h4 {
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}

.guide-content ul {
  padding-left: 20px;
}

.guide-content li {
  margin-bottom: 4px;
}

.guide-content p {
  margin-bottom: 8px;
}

.model-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.model-tags code {
  background: var(--color-brand-light);
  color: var(--color-brand);
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.code-block {
  background: #1E293B;
  color: #E2E8F0;
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  overflow-x: auto;
  margin: var(--space-3) 0;
}

:deep(code):not(.code-block code):not(.model-tags code):not(.key-masked) {
  background: var(--color-brand-soft);
  color: var(--color-brand);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}
</style>
