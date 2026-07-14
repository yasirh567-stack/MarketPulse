import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // Assumes `make dev` (or the backend + frontend dev servers) are already
  // running — this project targets DEMO_MODE=true so the smoke test never
  // depends on real network/API keys. See docs/deployment.md for CI wiring.
});
