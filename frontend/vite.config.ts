import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'
import { existsSync, statSync } from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
// In Docker: WORKDIR is /src, vite.config.ts is at /src/vite.config.ts
// When COPY . . runs, it copies the frontend/ directory contents to /src/
// So frontend/src/ becomes /src/src/
// Therefore @/lib/api should resolve to /src/src/lib/api.ts
// __dirname = /src, so path.resolve(__dirname, 'src') = /src/src
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
      
      // If we get here, the file doesn't exist - throw an error with helpful message
      // This prevents Vite from trying to resolve without extension
      const triedPaths = extensions.map(ext => path.join(srcPath, relativePath + ext))
      const errorMsg = `[alias-resolver] Could not find file for '@/${relativePath}'. ` +
        `Tried paths:\n${triedPaths.map(p => `  - ${p}`).join('\n')}\n` +
        `Source directory: ${srcPath}\n` +
        `Current working directory: ${process.cwd()}`
      throw new Error(errorMsg)
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [aliasResolver(), react()],
  resolve: {
    // Don't use alias here - let our custom plugin handle @/ imports
    // This prevents Vite from trying to resolve without extensions when plugin returns null
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

