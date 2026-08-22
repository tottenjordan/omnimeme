import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        timeout: 60000,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, res) => {
            console.warn('[vite proxy error]', err.message);
            if (res && !res.headersSent) {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ detail: 'FastAPI backend connection error. Ensure uvicorn is running.' }));
            }
          });
          proxy.on('proxyReq', (proxyReq, _req, _res) => {
            proxyReq.setHeader('Connection', 'keep-alive');
          });
        },
      },
    },
  },
})
