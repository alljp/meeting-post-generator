import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import api from '../lib/api'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, user, setAuth, clearAuth } = useAuthStore()

  useEffect(() => {
    // If we have a token but no user, fetch user info
    const token = localStorage.getItem('token')
    if (token && !user) {
      api.get('/auth/me')
        .then((response) => {
          setAuth(response.data, token)
        })
        .catch(() => {
          // Token invalid, clear auth
          clearAuth()
        })
    }
  }, [user, setAuth, clearAuth])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

