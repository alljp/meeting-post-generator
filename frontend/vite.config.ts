import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'
import { existsSync, statSync } from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const srcPath = path.resolve(__dirname, 'src')

// Custom plugin to ensure extension resolution works with aliases
// This must run BEFORE the alias resolution, so we handle @/ imports directly
const aliasExtensionPlugin = () => {
  return {
    name: 'alias-extension-resolver',
    enforce: 'pre' as const, // Run before other resolvers
    resolveId(id: string, importer: string | undefined) {
      // Handle @/ imports directly
      if (id.startsWith('@/')) {
        const relativePath = id.replace('@/', '')
        const extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.mts', '.json']
        
        // Try with extensions
        for (const ext of extensions) {
          const fullPath = path.resolve(srcPath, relativePath + ext)
          if (existsSync(fullPath)) {
            return fullPath
          }
        }
        
        // Try as directory with index files
        const dirPath = path.resolve(srcPath, relativePath)
        if (existsSync(dirPath) && statSync(dirPath).isDirectory()) {
          for (const ext of extensions) {
            const indexPath = path.join(dirPath, `index${ext}`)
            if (existsSync(indexPath)) {
              return indexPath
            }
          }
        }
        
        // If nothing found, return the path without extension and let Vite handle it
        // This will cause an error, but at least we tried
        return path.resolve(srcPath, relativePath)
      }
      return null
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [aliasExtensionPlugin(), react()], // Plugin must run before react plugin
  resolve: {
    // Remove alias since plugin handles it
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

