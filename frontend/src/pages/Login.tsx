import { useState } from 'react'
import { useToastContext } from '../contexts/ToastContext'
import api from '../lib/api'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const { error: showError } = useToastContext()

  const handleGoogleLogin = async () => {
    try {
      setLoading(true)
      // Get authorization URL from backend
      const response = await api.get('/auth/google/login')
      const { authorization_url } = response.data
      
      // Redirect to Google OAuth
      window.location.href = authorization_url
    } catch (error: any) {
      setLoading(false)
      showError('Failed to start login. Please try again.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Connect with Google to get started
          </p>
        </div>
        <div>
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Connecting...
              </>
            ) : (
              'Sign in with Google'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

