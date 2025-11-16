import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import api from '../lib/api'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setAuth } = useAuthStore()
  const token = searchParams.get('token')

  useEffect(() => {
    const handleCallback = async () => {
      if (token) {
        // Store token
        localStorage.setItem('token', token)
        
        // Fetch user info
        try {
          const response = await api.get('/auth/me')
          const user = response.data
          
          // Set auth state
          setAuth(user, token)
          
          // Redirect to home
          navigate('/', { replace: true })
        } catch (error) {
          // Log error for debugging but don't show to user (they'll be redirected)
          // In production, this could be sent to error tracking service
          if (process.env.NODE_ENV === 'development') {
            console.error('Failed to get user info:', error)
          }
          // Clear token and redirect to login
          localStorage.removeItem('token')
          navigate('/login', { replace: true })
        }
      } else {
        // No token, redirect to login
        navigate('/login', { replace: true })
      }
    }

    handleCallback()
  }, [token, setAuth, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  )
}

