import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'
import { existsSync, statSync, readdirSync } from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
// In Docker: WORKDIR is /app, vite.config.ts is at /app/vite.config.ts
// When COPY . . runs, it copies the frontend/ directory contents to /app/
// So frontend/src/lib/api.ts becomes /app/src/lib/api.ts
// __dirname = /app, so path.resolve(__dirname, 'src') = /app/src
const srcPath = path.resolve(__dirname, 'src')

// Custom resolver plugin for @/ aliases to ensure proper extension resolution
// This is needed for Docker/Linux builds where path resolution may behave differently
const aliasResolver = () => {
  return {
    name: 'alias-resolver',
    enforce: 'pre' as const,
    resolveId(id: string, importer: string | undefined) {
      // Only handle @/ imports
      if (!id.startsWith('@/')) {
        return null
      }
      
      const relativePath = id.replace('@/', '').replace(/\\/g, '/')
      const extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.mts', '.json']
      
      // Try with each extension
      for (const ext of extensions) {
        const fullPath = path.resolve(srcPath, relativePath + ext)
        try {
          if (existsSync(fullPath)) {
            const stats = statSync(fullPath)
            if (stats.isFile()) {
              // Return absolute path - this prevents Vite from trying to load without extension
              return fullPath
            }
          }
        } catch (err) {
          // File doesn't exist, continue to next extension
          continue
        }
      }
      
      // Try as directory with index file
      const dirPath = path.resolve(srcPath, relativePath)
      try {
        if (existsSync(dirPath)) {
          const stats = statSync(dirPath)
          if (stats.isDirectory()) {
            for (const ext of extensions) {
              const indexPath = path.resolve(dirPath, `index${ext}`)
              if (existsSync(indexPath)) {
                return indexPath
              }
            }
          }
        }
      } catch (err) {
        // Directory doesn't exist
      }
      
      // If we get here, the file doesn't exist - try alternative locations
      // Sometimes files might be in a nested src/src/ structure
      const altSrcPath = path.resolve(__dirname, 'src', 'src')
      if (existsSync(altSrcPath)) {
        for (const ext of extensions) {
          const fullPath = path.resolve(altSrcPath, relativePath + ext)
          if (existsSync(fullPath)) {
            return fullPath
          }
        }
      }
      
      // If still not found, return null to let Vite's built-in alias resolver try
      // This allows Vite to use the resolve.alias configuration as fallback
      // Vite will handle extension resolution automatically
      return null
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [aliasResolver(), react()],
  resolve: {
    // Use alias here as fallback - Vite will handle extension resolution
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

