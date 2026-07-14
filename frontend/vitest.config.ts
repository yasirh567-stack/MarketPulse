import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./tests/setup.ts"],
      css: true,
      // Playwright specs live under e2e/ and use a different test runner
      // (`npm run test:e2e`) — excluding them here keeps `vitest run` from
      // trying (and failing) to execute Playwright's `test()` API.
      include: ["tests/**/*.{test,spec}.{ts,tsx}"],
      exclude: ["e2e/**", "node_modules/**"],
    },
  })
);
