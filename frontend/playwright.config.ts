import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3011",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    channel: process.env.CI ? undefined : "msedge"
  },
  projects: [{ name: "desktop", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "python -m uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        DATABASE_URL: "sqlite:///./e2e-comment-insight.db",
        LLM_PROVIDER: "mock",
        TASK_WORKER_COUNT: "1",
        CORS_ORIGINS: '["http://127.0.0.1:3011"]'
      }
    },
    {
      command: "npm run start -- --hostname 127.0.0.1 --port 3011",
      url: "http://127.0.0.1:3011",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {}
    }
  ]
});
