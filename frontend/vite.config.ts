import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy all /api/* requests to Django backend
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      // Proxy auth routes for CSRF / session cookie flow
      "/auth-backend": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/auth-backend/, "/auth"),
      },
    },
  },
});
