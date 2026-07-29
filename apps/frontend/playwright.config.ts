import { defineConfig, devices } from "@playwright/test";

const nodeExecutable = JSON.stringify(process.execPath);

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [["line"], ["html", { open: "never" }]]
    : [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:3100",
    permissions: ["clipboard-read", "clipboard-write"],
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `${nodeExecutable} node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3100`,
    env: {
      NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:3100/api/v1",
      NEXT_PUBLIC_USE_MOCKS: "false",
    },
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    url: "http://127.0.0.1:3100",
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile-chromium",
      use: {
        ...devices["Pixel 5"],
        browserName: "chromium",
      },
    },
  ],
});
