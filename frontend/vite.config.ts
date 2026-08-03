import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ mode }) => {
  // By default `npm run dev` proxies to local backend at 8080.
  // For production (API resides on Render), the client should use absolute URL set via
  // `VITE_API_BASE` environment variable. If unset, fallback path `/v1` is proxied by
  // Vercel rewrites to the hosted backend variable embedded in `vercel.json`.
  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    server: {
      proxy: mode === "development" ? {
        "/v1": {
          target: "http://localhost:8080",
          changeOrigin: true,
        },
      } : undefined,
    },
  };
});
