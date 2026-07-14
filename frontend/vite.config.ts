import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
  },
  build: {
    // Plotly is unavoidably large; it's already lazy-loaded (only the
    // chart-bearing pages import it), so isolate it into its own named
    // chunk rather than letting the warning point at an unrelated file.
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("plotly.js") || id.includes("react-plotly.js")) {
            return "plotly-vendor";
          }
        },
      },
    },
    chunkSizeWarningLimit: 1600,
  },
});
