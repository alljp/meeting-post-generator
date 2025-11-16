import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface User {
  id: number
  email: string
  name?: string | null
  picture?: string | null
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (user: User, token: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => {
      // Initialize from localStorage token if present
      const token = localStorage.getItem('token')
      const isAuthenticated = !!token
      
      return {
        user: null,
        token: token,
        isAuthenticated: isAuthenticated,
        setAuth: (user, token) => {
          localStorage.setItem('token', token)
          set({ user, token, isAuthenticated: true })
        },
        clearAuth: () => {
          localStorage.removeItem('token')
          set({ user: null, token: null, isAuthenticated: false })
        },
      }
    },
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist user, not token (token is in localStorage separately)
      partialize: (state) => ({ user: state.user }),
    }
  )
)

