import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    // In development the API runs separately. In production the server serves
    // this build itself, so the client never needs to know a host name -- which
    // is what lets the same build run on anybody's server.
    proxy: { '/api': 'http://127.0.0.1:5173' },
    port: 5174,
  },
  build: { outDir: 'dist', emptyOutDir: true },
})
