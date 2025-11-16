import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Save, Loader2, Clock, Link2, X, Mail, Settings as SettingsIcon } from 'lucide-react'
import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useToastContext } from '../contexts/ToastContext'
import api from '../lib/api'
import AutomationList from '../components/AutomationList'

const settingsSchema = z.object({
  bot_join_minutes_before: z.number().min(0).max(60),
})

type SettingsForm = z.infer<typeof settingsSchema>

interface Settings {
  bot_join_minutes_before: number
}

interface SocialAccount {
  id: number
  platform: string
  account_name: string | null
  is_active: boolean
  created_at: string | null
}

interface GoogleAccount {
  id: number
  google_email: string
  is_active: boolean
  created_at: string | null
}

export default function Settings() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToastContext()
  const [searchParams, setSearchParams] = useSearchParams()

  // Check for OAuth callback success
  useEffect(() => {
    const connected = searchParams.get('connected')
    if (connected) {
      if (connected === 'google') {
        queryClient.invalidateQueries({ queryKey: ['google-accounts'] })
        success('Google account connected successfully!')
      } else {
        queryClient.invalidateQueries({ queryKey: ['social-accounts'] })
        success(`${connected === 'linkedin' ? 'LinkedIn' : 'Facebook'} account connected successfully!`)
      }
      setSearchParams({})
    }
  }, [searchParams, queryClient, setSearchParams, success])

  const { data: settings, isLoading } = useQuery<Settings>({
    queryKey: ['settings'],
    queryFn: async () => {
      const response = await api.get('/settings')
      return response.data
    },
  })

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SettingsForm>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      bot_join_minutes_before: 5,
    },
    values: settings ? { bot_join_minutes_before: settings.bot_join_minutes_before } : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: async (data: SettingsForm) => {
      const response = await api.patch('/settings', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      success('Settings saved successfully!')
    },
    onError: (error: any) => {
      showError(`Failed to save settings: ${error.response?.data?.detail || error.message}`)
    },
  })

  const onSubmit = (data: SettingsForm) => {
    updateMutation.mutate(data)
  }

  // Google accounts
  const { data: googleAccounts, isLoading: googleAccountsLoading } = useQuery<GoogleAccount[]>({
    queryKey: ['google-accounts'],
    queryFn: async () => {
      const response = await api.get('/auth/google/accounts')
      return response.data
    },
  })

  // Social accounts
  const { data: socialAccounts, isLoading: accountsLoading } = useQuery<SocialAccount[]>({
    queryKey: ['social-accounts'],
    queryFn: async () => {
      const response = await api.get('/social/accounts')
      return response.data
    },
  })

  const connectGoogleMutation = useMutation({
    mutationFn: async () => {
      const response = await api.get('/auth/google/connect')
      return response.data
    },
    onSuccess: (data) => {
      // Redirect to OAuth URL
      window.location.href = data.authorization_url
    },
    onError: (error: any) => {
      alert(`Failed to connect Google account: ${error.response?.data?.detail || error.message}`)
    },
  })

  const disconnectGoogleMutation = useMutation({
    mutationFn: async (accountId: number) => {
      await api.delete(`/auth/google/accounts/${accountId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['google-accounts'] })
      alert('Google account disconnected successfully!')
    },
    onError: (error: any) => {
      alert(`Failed to disconnect Google account: ${error.response?.data?.detail || error.message}`)
    },
  })

  const connectLinkedInMutation = useMutation({
    mutationFn: async () => {
      const response = await api.get('/social/linkedin/connect')
      return response.data
    },
    onSuccess: (data) => {
      // Redirect to OAuth URL
      window.location.href = data.authorization_url
    },
    onError: (error: any) => {
      alert(`Failed to connect LinkedIn: ${error.response?.data?.detail || error.message}`)
    },
  })

  const connectFacebookMutation = useMutation({
    mutationFn: async () => {
      const response = await api.get('/social/facebook/connect')
      return response.data
    },
    onSuccess: (data) => {
      // Redirect to OAuth URL
      window.location.href = data.authorization_url
    },
    onError: (error: any) => {
      alert(`Failed to connect Facebook: ${error.response?.data?.detail || error.message}`)
    },
  })

  const disconnectMutation = useMutation({
    mutationFn: async (accountId: number) => {
      await api.delete(`/social/accounts/${accountId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-accounts'] })
      alert('Account disconnected successfully!')
    },
    onError: (error: any) => {
      alert(`Failed to disconnect: ${error.response?.data?.detail || error.message}`)
    },
  })

  const getLinkedInAccount = () => socialAccounts?.find(acc => acc.platform === 'linkedin' && acc.is_active)
  const getFacebookAccount = () => socialAccounts?.find(acc => acc.platform === 'facebook' && acc.is_active)

  if (isLoading) {
    return (
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gray-100">
              <SettingsIcon className="h-6 w-6 text-gray-600" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Settings</h1>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gray-100">
            <SettingsIcon className="h-6 w-6 text-gray-600" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-600 mt-2">
              Manage your account connections and preferences
            </p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-100">
            <Clock className="h-5 w-5 text-blue-600" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900">Bot Configuration</h2>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div>
            <label htmlFor="bot_join_minutes_before" className="block text-sm font-medium text-gray-700 mb-2">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Bot Join Time (minutes before meeting)</span>
              </div>
            </label>
            <p className="text-sm text-gray-500 mb-3">
              Configure how many minutes before a meeting starts that the Recall.ai bot should join.
              This ensures the bot is ready when the meeting begins.
            </p>
            <input
              type="number"
              id="bot_join_minutes_before"
              {...register('bot_join_minutes_before', { valueAsNumber: true })}
              min="0"
              max="60"
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-4 py-2.5 border transition-colors"
              placeholder="5"
            />
            {errors.bot_join_minutes_before && (
              <p className="mt-1 text-sm text-red-600">
                {errors.bot_join_minutes_before.message}
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Valid range: 0-60 minutes
            </p>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting || updateMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting || updateMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-100">
            <Mail className="h-5 w-5 text-blue-600" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900">Google Calendar Accounts</h2>
        </div>
        <p className="text-gray-500 mb-4">Connect multiple Google accounts to sync calendar events from all of them.</p>
        <div className="space-y-3 mb-4">
          {googleAccountsLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            </div>
          ) : googleAccounts && googleAccounts.length > 0 ? (
            googleAccounts
              .filter(acc => acc.is_active)
              .map((account) => (
                <div key={account.id} className="flex items-center justify-between p-5 border border-gray-200 rounded-xl hover:border-blue-200 hover:shadow-sm transition-all">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-gray-500" />
                      <h3 className="font-medium text-gray-900">{account.google_email}</h3>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Connected {account.created_at ? new Date(account.created_at).toLocaleDateString() : ''}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm(`Are you sure you want to disconnect ${account.google_email}?`)) {
                        disconnectGoogleMutation.mutate(account.id)
                      }
                    }}
                    disabled={disconnectGoogleMutation.isPending}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50 transition-colors"
                  >
                    <X className="w-4 h-4 mr-1" />
                    Disconnect
                  </button>
                </div>
              ))
          ) : (
            <p className="text-sm text-gray-500 py-4">No Google accounts connected</p>
          )}
        </div>
        <button
          onClick={() => connectGoogleMutation.mutate()}
          disabled={connectGoogleMutation.isPending}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 border border-blue-600 rounded-lg transition-colors"
        >
          {connectGoogleMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Connecting...
            </>
          ) : (
            <>
              <Link2 className="w-4 h-4 mr-2" />
              Connect Google Account
            </>
          )}
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-green-100">
            <Link2 className="h-5 w-5 text-green-600" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900">Social Media Connections</h2>
        </div>
        <p className="text-gray-500 mb-4">Connect your social media accounts to post generated content.</p>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-5 border border-gray-200 rounded-xl hover:border-blue-200 hover:shadow-sm transition-all">
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">LinkedIn</h3>
              {getLinkedInAccount() ? (
                <p className="text-sm text-gray-600">
                  Connected as {getLinkedInAccount()?.account_name || 'LinkedIn account'}
                </p>
              ) : (
                <p className="text-sm text-gray-500">Not connected</p>
              )}
            </div>
            {getLinkedInAccount() ? (
              <button
                onClick={() => disconnectMutation.mutate(getLinkedInAccount()!.id)}
                disabled={disconnectMutation.isPending}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50 transition-colors"
              >
                <X className="w-4 h-4 mr-1" />
                Disconnect
              </button>
            ) : (
              <button
                onClick={() => connectLinkedInMutation.mutate()}
                disabled={connectLinkedInMutation.isPending}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 transition-colors"
              >
                {connectLinkedInMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Link2 className="w-4 h-4 mr-1" />
                    Connect
                  </>
                )}
              </button>
            )}
          </div>
          <div className="flex items-center justify-between p-5 border border-gray-200 rounded-xl hover:border-blue-200 hover:shadow-sm transition-all">
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">Facebook</h3>
              {getFacebookAccount() ? (
                <p className="text-sm text-gray-600">
                  Connected as {getFacebookAccount()?.account_name || 'Facebook account'}
                </p>
              ) : (
                <p className="text-sm text-gray-500">Not connected</p>
              )}
            </div>
            {getFacebookAccount() ? (
              <button
                onClick={() => disconnectMutation.mutate(getFacebookAccount()!.id)}
                disabled={disconnectMutation.isPending}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50 transition-colors"
              >
                <X className="w-4 h-4 mr-1" />
                Disconnect
              </button>
            ) : (
              <button
                onClick={() => connectFacebookMutation.mutate()}
                disabled={connectFacebookMutation.isPending}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 transition-colors"
              >
                {connectFacebookMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Link2 className="w-4 h-4 mr-1" />
                    Connect
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
        <AutomationList />
      </div>
    </div>
  )
}

