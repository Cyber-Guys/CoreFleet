import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// The app calls `/report-api` on the same origin. In production nginx proxies
// it; with `npm run dev` this proxy forwards it to the report service
// (VITE_DEV_REPORT_URL, localhost by default).
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
