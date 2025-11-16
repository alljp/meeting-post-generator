import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'
import { existsSync } from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const srcPath = path.resolve(__dirname, './src')

// Custom resolver plugin for @/ aliases to ensure proper extension resolution
// This is needed for Docker/Linux builds where path resolution may behave differently
const aliasResolver = () => {
  return {
    name: 'alias-resolver',
    enforce: 'pre' as const,
    resolveId(id: string, importer: string | undefined) {
      if (id.startsWith('@/')) {
        const relativePath = id.replace('@/', '').replace(/\\/g, '/')
        const extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.mts', '.json']
        
        // Try with each extension
        for (const ext of extensions) {
          const fullPath = path.resolve(srcPath, relativePath + ext)
          if (existsSync(fullPath)) {
            // Return absolute path - Vite will handle it correctly
            return fullPath
          }
        }
        
        // Try as directory with index file
        const dirPath = path.resolve(srcPath, relativePath)
        if (existsSync(dirPath)) {
          for (const ext of extensions) {
            const indexPath = path.resolve(dirPath, `index${ext}`)
            if (existsSync(indexPath)) {
              return indexPath
            }
          }
        }
      }
      return null
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [aliasResolver(), react()],
  resolve: {
    alias: {
      '@': srcPath,
    },
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

