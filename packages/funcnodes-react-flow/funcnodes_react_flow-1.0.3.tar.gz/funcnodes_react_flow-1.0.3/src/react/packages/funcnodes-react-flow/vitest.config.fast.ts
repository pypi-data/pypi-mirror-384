import { defineConfig } from "vitest/config";
import path from "path";
import { loadAliasesFromTsConfig } from "./vite.config";

// Fast test configuration that avoids slow Vite config merging
export default defineConfig({
  test: {
    globals: true,
    environment: "happy-dom", // Faster than jsdom
    setupFiles: "./src/setupTests.ts",
    css: false, // Disable CSS processing for faster tests
    testTimeout: 30000,
    include: [
      "tests/**/*.{test,spec}.{js,ts,tsx}",
      "src/**/*.{test,spec}.{js,ts,tsx}",
    ],
    exclude: [
      "**/node_modules/**",
      "**/dist/**",
      "**/tests/e2e/**",
      "**/*.e2e.*",
      "**/keypress-provider*.test.tsx",
    ],
    pool: "forks", // Use forks instead of vmThreads for faster startup
    poolOptions: {
      forks: {
        isolate: false, // Disable isolation for faster tests
      },
    },
    deps: {
      optimizer: {
        web: {
          enabled: true,
        },
      },
    },
  },
  resolve: {
    alias: {
      ...loadAliasesFromTsConfig(),
    },
  },
  esbuild: {
    target: "node14", // Lower target for faster transpilation
  },
});
