import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL,
  timeout: 300000
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const healthApi = {
  check: () => api.get('/health/check'),
  getLlmConfig: () => api.get('/health/llm-config'),
  testLlm: () => api.get('/health/llm-test'),
  getLlmModels: () => api.get('/health/llm-models')
}

export const resumeApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/resume/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  parse: (fileId: string) => api.post('/resume/parse', { file_id: fileId }),
  structure: (rawText: string) => api.post('/resume/structure', { raw_text: rawText }),
  rewrite: (data: { resume_data: object; jd_data: object; raw_text: string; rewrite_mode: string; match_result?: object; diagnose_result?: object }) =>
    api.post('/resume/rewrite', data),
  getRewriteModes: () => api.get('/resume/modes')
}

export const jdApi = {
  analyze: (jdContent: string) => api.post('/jd/analyze', { jd_content: jdContent })
}

export const matchApi = {
  analyze: (resumeData: object, jdData: object) =>
    api.post('/match/analyze', { resume_data: resumeData, jd_data: jdData })
}

export const agentApi = {
  diagnose: (resumeText: string, jdContent: string) =>
    api.post('/agent/diagnose', { resume_text: resumeText, jd_content: jdContent })
}

export const interviewApi = {
  questions: (data: { resume_data: object; jd_data: object; raw_text?: string; rewrite_result?: object; question_types?: string[] }) =>
    api.post('/interview/questions', data),
  getTypes: () => api.get('/interview/types')
}

export const historyApi = {
  list: () => api.get('/history/list'),
  get: (id: number) => api.get(`/history/${id}`),
  delete: (id: number) => api.delete(`/history/${id}`),
  save: (data: {
    resume_filename?: string
    raw_text?: string
    resume_data?: object | null
    jd_text?: string
    jd_data?: object | null
    match_result?: object | null
    diagnose_result?: object | null
    rewrite_result?: object | null
    interview_questions?: object | null
  }) =>
    api.post('/history/save', data)
}

export const knowledgeApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  list: () => api.get('/knowledge/list'),
  delete: (id: number) => api.delete(`/knowledge/${id}`),
  search: (keyword: string, top_k: number = 5) =>
    api.post('/knowledge/search', { keyword, top_k })
}

export default api

export async function streamPost(
  url: string,
  data: object,
  onChunk: (chunk: string) => void,
  onProgress?: (step: string) => void,
  onDone?: (result: any) => void,
  onError?: (error: string) => void
): Promise<void> {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  const response = await fetch(`${baseURL}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    onError?.(`HTTP ${response.status}: ${response.statusText}`)
    return
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith('data: ')) continue
      try {
        const event = JSON.parse(trimmed.slice(6))
        if (event.type === 'chunk') onChunk(event.data.content)
        else if (event.type === 'progress') onProgress?.(event.data.step)
        else if (event.type === 'done') onDone?.(event.data.result)
        else if (event.type === 'error') onError?.(event.data.message)
      } catch { /* skip malformed lines */ }
    }
  }
}
