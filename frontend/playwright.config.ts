import { defineConfig, devices } from '@playwright/test'

const localBrowserChannel = process.env.CI ? undefined : 'msedge'

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  fullyParallel: false,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry'
  },
  webServer: [
    {
      command: 'powershell -NoProfile -Command "$env:LLM_ENABLE_REMOTE=\'false\'; cd ../backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"',
      url: 'http://127.0.0.1:8001/api/health/check',
      reuseExistingServer: false,
      timeout: 30_000
    },
    {
      command: 'powershell -NoProfile -Command "$env:VITE_API_BASE_URL=\'http://127.0.0.1:8001/api\'; npm run dev -- --host 127.0.0.1 --port 5173"',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: false,
      timeout: 30_000
    }
  ],
  projects: [
    {
      name: 'edge',
      use: {
        ...devices['Desktop Chrome'],
        ...(localBrowserChannel ? { channel: localBrowserChannel } : {})
      }
    }
  ]
})
