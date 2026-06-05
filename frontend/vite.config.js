import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/health":    "http://127.0.0.1:8000",
      "/map-data":  "http://127.0.0.1:8000",
      "/jobs":      "http://127.0.0.1:8000",
      "/trending":  "http://127.0.0.1:8000",
      "/salary":    "http://127.0.0.1:8000",
      "/insights":  "http://127.0.0.1:8000",
      "/skill-gap": "http://127.0.0.1:8000",
    },
  },
  optimizeDeps: {
    // Explicitly declare everything to pre-bundle so Vite skips scanning
    include: ["react", "react-dom", "react-dom/client", "react-router-dom"],
    noDiscovery: true,
  },
})
