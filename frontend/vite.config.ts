import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const frontendPort = parseInt(env.FRONTEND_PORT || process.env.FRONTEND_PORT || '5180', 10)
  const apiPort = parseInt(env.API_PORT || process.env.API_PORT || '8010', 10)
  const apiHost = env.API_HOST || process.env.API_HOST || '127.0.0.1'

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      strictPort: true,
      proxy: {
        '/api': {
          target: `http://${apiHost}:${apiPort}`,
          changeOrigin: true,
        },
        '/media': {
          target: `http://${apiHost}:${apiPort}`,
          changeOrigin: true,
        }
      }
    }
  }
})

