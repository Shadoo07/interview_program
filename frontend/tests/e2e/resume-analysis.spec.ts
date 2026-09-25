import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const testDir = path.dirname(fileURLToPath(import.meta.url))

test('resume upload, JD analysis, and match analysis flow works', async ({ page }) => {
  await page.goto('/resume-analysis')

  const resumePath = path.resolve(testDir, 'fixtures', 'sample-resume.txt')
  await page.locator('input[type="file"]').setInputFiles(resumePath)

  const sections = page.locator('.step-section')
  await expect(sections.nth(0).locator('button.btn-primary')).toBeVisible()
  await sections.nth(0).locator('button.btn-primary').click()

  await expect(page.locator('textarea.form-textarea')).toBeVisible()
  await page.locator('textarea.form-textarea').fill(`Backend Development Intern
Responsibilities: Build FastAPI backend APIs and maintain MySQL and Redis data flows.
Requirements: Python, FastAPI, SQL, Redis, and AI application project experience.`)

  await sections.nth(1).locator('button.btn-primary').click()
  await expect(page.locator('.step-actions .btn-primary')).toBeVisible()

  await page.locator('.step-actions .btn-primary').click()
  await expect(page.locator('.result-section').first()).toBeVisible()
  await expect(page.locator('.match-score-num')).toBeVisible()
  await expect(page.locator('.keywords-group').first()).toBeVisible()
})
