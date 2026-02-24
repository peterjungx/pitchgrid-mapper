import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

const backendPort = process.env.BACKEND_PORT || '8080'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    port: process.env.FRONTEND_PORT ? parseInt(process.env.FRONTEND_PORT) : 5173,
    proxy: {
      '/api': {
        target: `http://localhost:${backendPort}`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://localhost:${backendPort}`,
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
