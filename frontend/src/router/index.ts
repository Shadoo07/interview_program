import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/resume-analysis',
    name: 'ResumeAnalysis',
    component: () => import('@/views/ResumeAnalysis.vue')
  },
  {
    path: '/resume-rewrite',
    name: 'ResumeRewrite',
    component: () => import('@/views/ResumeRewrite.vue')
  },
  {
    path: '/interview-prep',
    name: 'InterviewPrep',
    component: () => import('@/views/InterviewPrep.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue')
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/Knowledge.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
