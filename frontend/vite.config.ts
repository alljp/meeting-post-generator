import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'
import { existsSync } from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
// Resolve src path - works whether vite.config.ts is at root or in a subdirectory
let srcPath = path.resolve(__dirname, 'src')
// Fallback: if src doesn't exist at __dirname/src, try current working directory
if (!existsSync(srcPath)) {
  srcPath = path.resolve(process.cwd(), 'src')
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      {
        find: /^@\/(.*)$/,
        replacement: path.resolve(srcPath, '$1'),
      },
    ],
    extensions: ['.mjs', '.js', '.mts', '.ts', '.jsx', '.tsx', '.json'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})

