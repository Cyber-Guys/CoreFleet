import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// The app talks to the same-origin `/report-api` path. In production nginx proxies
// it; in `npm run dev` this dev-server proxy forwards it to the report service
// (VITE_DEV_REPORT_URL, default localhost for a local backend).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const devReport = env.VITE_DEV_REPORT_URL || 'http://localhost:9080'
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        '/report-api': {
          target: devReport,
          changeOrigin: true,
          rewrite: (p) => p.replace(/^\/report-api/, ''),
        },
      },
    },
  }
})
