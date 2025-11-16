import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'
import { existsSync, statSync } from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const srcPath = path.resolve(__dirname, 'src')

// Custom plugin to ensure extension resolution works with aliases
const aliasExtensionPlugin = () => {
  return {
    name: 'alias-extension-resolver',
    resolveId(id: string, importer: string | undefined) {
      if (id.startsWith('@/')) {
        const relativePath = id.replace('@/', '')
        const extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.mts', '.json']
        
        for (const ext of extensions) {
          const fullPath = path.resolve(srcPath, relativePath + ext)
          if (existsSync(fullPath)) {
            return fullPath
          }
        }
        
        // Try without extension (for index files)
        const dirPath = path.resolve(srcPath, relativePath)
        if (existsSync(dirPath) && statSync(dirPath).isDirectory()) {
          for (const ext of extensions) {
            const indexPath = path.join(dirPath, `index${ext}`)
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
  plugins: [react(), aliasExtensionPlugin()],
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

