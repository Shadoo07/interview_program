import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface ResumeData {
  basic_info?: any
  skills?: any[]
  education?: any[]
  projects?: any[]
  internships?: any[]
  awards?: any[]
}

export interface JdData {
  position_title?: string
  position_type?: string
  required_skills?: string[]
  nice_to_have_skills?: string[]
  responsibilities?: string[]
  requirements?: string[]
  experience_requirement?: string
  education_requirement?: string
}

export interface MatchResult {
  overall_score?: number
  dimension_scores?: Array<{
    dimension: string
    score: number
    max_score?: number
    weight?: number
    matched_keywords?: string[]
    missing_keywords?: string[]
  }>
  matched_keywords?: string[]
  missing_keywords?: string[]
  weak_points?: string[]
  suggestions?: string[]
  match_level?: string
  source?: string
}

export interface DiagnoseResult {
  source?: string
  overall_assessment?: string
  strengths?: Array<{point: string, detail: string}>
  weaknesses?: Array<{point: string, detail: string}>
  improvements?: Array<{area: string, suggestion: string, priority: string}>
  career_advice?: string
  interview_tips?: string[]
}

export interface RewriteResult {
  original_analysis?: string
  rewritten_content?: string
  rewrite_reasons?: string[]
  project_experience_text?: string
  notes?: string[]
  source?: string
}

export interface InterviewQuestions {
  source?: string
  project_deep_dive?: any[]
  tech_theory?: any[]
  system_design?: any[]
  project_difficulties?: any[]
  hr_general?: any[]
  self_intro?: string
}

const STORAGE_KEY = 'resume_coach_state'

export const useResumeStore = defineStore('resume', () => {
  const resumeText = ref('')
  const resumeFileName = ref('')
  const resumeData = ref<ResumeData | null>(null)
  const jdText = ref('')
  const jdData = ref<JdData | null>(null)
  const matchResult = ref<MatchResult | null>(null)
  const diagnoseResult = ref<DiagnoseResult | null>(null)
  const rewriteResult = ref<RewriteResult | null>(null)
  const interviewQuestions = ref<InterviewQuestions | null>(null)
  const fileId = ref<string | null>(null)

  const setResumeText = (text: string) => {
    resumeText.value = text
  }

  const setResumeFileName = (name: string) => {
    resumeFileName.value = name
  }

  const setResumeData = (data: ResumeData) => {
    resumeData.value = data
  }

  const setJdText = (text: string) => {
    jdText.value = text
  }

  const setJdData = (data: JdData) => {
    jdData.value = data
  }

  const setMatchResult = (result: MatchResult) => {
    matchResult.value = result
  }

  const setDiagnoseResult = (result: DiagnoseResult) => {
    diagnoseResult.value = result
  }

  const setRewriteResult = (result: RewriteResult | null) => {
    rewriteResult.value = result
  }

  const setInterviewQuestions = (questions: InterviewQuestions | null) => {
    interviewQuestions.value = questions
  }

  const setFileId = (id: string) => {
    fileId.value = id
  }

  const clearResume = () => {
    resumeText.value = ''
    resumeFileName.value = ''
    resumeData.value = null
    fileId.value = null
  }

  const clearJd = () => {
    jdText.value = ''
    jdData.value = null
  }

  const clearAnalysis = () => {
    matchResult.value = null
    diagnoseResult.value = null
  }

  const clearAll = () => {
    resumeText.value = ''
    resumeFileName.value = ''
    resumeData.value = null
    jdText.value = ''
    jdData.value = null
    matchResult.value = null
    diagnoseResult.value = null
    rewriteResult.value = null
    interviewQuestions.value = null
    fileId.value = null
  }

  const saveToStorage = () => {
    const state = {
      resumeText: resumeText.value,
      resumeFileName: resumeFileName.value,
      resumeData: resumeData.value,
      jdText: jdText.value,
      jdData: jdData.value,
      matchResult: matchResult.value,
      diagnoseResult: diagnoseResult.value,
      rewriteResult: rewriteResult.value,
      interviewQuestions: interviewQuestions.value,
      fileId: fileId.value
    }
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch (e) {
      console.warn('Failed to save state to sessionStorage:', e)
    }
  }

  const restoreFromStorage = () => {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY)
      if (saved) {
        const state = JSON.parse(saved)
        resumeText.value = state.resumeText || ''
        resumeFileName.value = state.resumeFileName || ''
        resumeData.value = state.resumeData || null
        jdText.value = state.jdText || ''
        jdData.value = state.jdData || null
        matchResult.value = state.matchResult || null
        diagnoseResult.value = state.diagnoseResult || null
        rewriteResult.value = state.rewriteResult || null
        interviewQuestions.value = state.interviewQuestions || null
        fileId.value = state.fileId || null
        return true
      }
    } catch (e) {
      console.warn('Failed to restore state from sessionStorage:', e)
    }
    return false
  }

  const restoreFromHistory = (historyData: any) => {
    resumeText.value = historyData.raw_text || ''
    resumeFileName.value = historyData.resume_filename || ''
    resumeData.value = historyData.resume_data || null
    jdText.value = historyData.jd_text || ''
    jdData.value = historyData.jd_data || null
    matchResult.value = historyData.match_result || null
    diagnoseResult.value = historyData.diagnose_result || null
    rewriteResult.value = historyData.rewrite_result || null
    interviewQuestions.value = historyData.interview_questions || null
    saveToStorage()
  }

  watch([resumeText, resumeData, jdText, jdData, matchResult, diagnoseResult, rewriteResult, interviewQuestions], () => {
    saveToStorage()
  }, { deep: true })

  return {
    resumeText,
    resumeFileName,
    resumeData,
    jdText,
    jdData,
    matchResult,
    diagnoseResult,
    rewriteResult,
    interviewQuestions,
    fileId,
    setResumeText,
    setResumeFileName,
    setResumeData,
    setJdText,
    setJdData,
    setMatchResult,
    setDiagnoseResult,
    setRewriteResult,
    setInterviewQuestions,
    setFileId,
    clearResume,
    clearJd,
    clearAnalysis,
    clearAll,
    saveToStorage,
    restoreFromStorage,
    restoreFromHistory
  }
})
