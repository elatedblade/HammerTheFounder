import { defineConfig } from "@playwright/test";

// Anonymous, isolated public UX checks. No real Clerk sessions or provider calls.
// Authenticated persistence/authorization is covered by the backend API suite;
// a live Clerk + WhatsApp acceptance test remains explicitly separate.
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 60000,
  expect: { timeout: 15000 },
  retries: 0,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:3100", trace: "off" },
  webServer: {
    command: "npm run dev -- --webpack --hostname 127.0.0.1 --port 3100",
    url: "http://127.0.0.1:3100",
    reuseExistingServer: false,
    timeout: 120000,
    env: {
      NEXT_TELEMETRY_DISABLED: "1",
      NEXT_PUBLIC_AUTH_MODE: "unconfigured",
      NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: "",
      CLERK_SECRET_KEY: "",
      NEXT_PUBLIC_SENTRY_DSN: "",
    },
  },
});
