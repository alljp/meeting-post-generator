import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { 
  Calendar, Users, FileText, Mail, MessageSquare, Copy, Send, 
  Loader2, ArrowLeft, Video, Check, Sparkles
} from 'lucide-react'
import { useToastContext } from '../contexts/ToastContext'
import ConfirmDialog from '../components/ConfirmDialog'
import api from '../lib/api'
import PlatformIcon from '../components/PlatformIcon'

interface Attendee {
  id: number
  name: string
  email: string | null
}

interface Meeting {
  id: number
  title: string
  start_time: string
  end_time: string
  platform: string
  transcript: string | null
  transcript_available: boolean
  recording_url: string | null
  attendees: Attendee[]
  recall_bot_id: string
}

type Tab = 'transcript' | 'email' | 'posts' | 'draft'

export default function MeetingDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const { success, error: showError } = useToastContext()
  const [activeTab, setActiveTab] = useState<Tab>('transcript')
  const [copied, setCopied] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<string>('linkedin')
  const [draftPost, setDraftPost] = useState<string | null>(null)
  const [postConfirm, setPostConfirm] = useState<{ postId: number | null; open: boolean }>({
    postId: null,
    open: false,
  })

  const { data: meeting, isLoading, error } = useQuery<Meeting>({
    queryKey: ['meeting', id],
    queryFn: async () => {
      const response = await api.get(`/meetings/${id}`)
      return response.data
    },
    enabled: !!id,
  })

  const { data: email } = useQuery({
    queryKey: ['meeting-email', id],
    queryFn: async () => {
      const response = await api.get(`/meetings/${id}/email`)
      return response.data.email
    },
    enabled: !!id && activeTab === 'email',
  })

  const { data: posts } = useQuery({
    queryKey: ['meeting-posts', id],
    queryFn: async () => {
      const response = await api.get(`/meetings/${id}/posts`)
      return response.data.posts || []
    },
    enabled: !!id && (activeTab === 'posts' || activeTab === 'draft'),
  })

  const generatePostMutation = useMutation({
    mutationFn: async (platform: string) => {
      const response = await api.post(`/meetings/${id}/generate-post?platform=${platform}`)
      return response.data
    },
    onSuccess: (data) => {
      setDraftPost(data.content)
      queryClient.invalidateQueries({ queryKey: ['meeting-posts', id] })
      success('Post generated successfully!')
    },
    onError: (error: any) => {
      showError(`Failed to generate post: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      success('Copied to clipboard!')
    } catch (err) {
      showError('Failed to copy to clipboard')
    }
  }

  const postMutation = useMutation({
    mutationFn: async (postId: number) => {
      const response = await api.post(`/social/posts/${postId}/post`)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['meeting-posts', id] })
      success(data.message || 'Post published successfully!')
      setPostConfirm({ postId: null, open: false })
    },
    onError: (error: any) => {
      showError(`Failed to post: ${error.response?.data?.detail || error.message}`)
      setPostConfirm({ postId: null, open: false })
    },
  })

  const handlePost = async (postId: number) => {
    setPostConfirm({ postId, open: true })
  }

  const confirmPost = () => {
    if (postConfirm.postId !== null) {
      postMutation.mutate(postConfirm.postId)
    }
  }

  if (isLoading) {
    return (
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </div>
    )
  }

  if (error || !meeting) {
    return (
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-800 font-medium">Failed to load meeting. Please try again.</p>
        </div>
      </div>
    )
  }

  const startTime = new Date(meeting.start_time)
  const endTime = new Date(meeting.end_time)

  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: 'transcript', label: 'Transcript', icon: FileText },
    { id: 'email', label: 'Follow-up Email', icon: Mail },
    { id: 'posts', label: 'Social Media Posts', icon: MessageSquare },
    { id: 'draft', label: 'Draft Post', icon: MessageSquare },
  ]

  return (
    <div className="px-4 py-8 sm:px-6 lg:px-8">
      <Link
        to="/meetings"
        className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Meetings
      </Link>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8 mb-6">
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-4">
              <h1 className="text-3xl font-bold text-gray-900">{meeting.title}</h1>
              <PlatformIcon platform={meeting.platform} size="md" />
            </div>

            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>
                  {format(startTime, 'MMM d, yyyy')} at {format(startTime, 'h:mm a')}
                  {' - '}
                  {format(endTime, 'h:mm a')}
                </span>
              </div>

              {meeting.attendees && meeting.attendees.length > 0 && (
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>
                    {meeting.attendees.length} attendee{meeting.attendees.length !== 1 ? 's' : ''}
                    {': '}
                    {meeting.attendees.map(a => a.name).join(', ')}
                  </span>
                </div>
              )}

              {meeting.recording_url && (
                <div className="flex items-center gap-2">
                  <Video className="w-4 h-4" />
                  <a
                    href={meeting.recording_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    View Recording
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors
                    ${isActive
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'transcript' && (
            <div>
              {meeting.transcript_available && meeting.transcript ? (
                <div>
                  <div className="flex justify-end mb-4">
                    <button
                      onClick={() => handleCopy(meeting.transcript!)}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 mr-2" />
                          Copy Transcript
                        </>
                      )}
                    </button>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
                      {meeting.transcript}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-50 rounded-xl border border-gray-200">
                  <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-gray-900 mb-2">Transcript not available yet</p>
                  <p className="text-gray-600">
                    The transcript will appear here once the meeting is processed.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'email' && (
            <div>
              {email ? (
                <div>
                  <div className="flex justify-end mb-4">
                    <button
                      onClick={() => handleCopy(email)}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 mr-2" />
                          Copy Email
                        </>
                      )}
                    </button>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-6 md:p-8">
                    <div className="prose prose-sm max-w-none">
                      {email.split('\n').map((line, index) => {
                        // Format subject line
                        if (line.startsWith('Subject:')) {
                          return (
                            <div key={index} className="mb-4">
                              <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Subject</div>
                              <div className="text-lg font-semibold text-gray-900">{line.replace('Subject:', '').trim()}</div>
                            </div>
                          )
                        }
                        // Format empty lines
                        if (line.trim() === '') {
                          return <div key={index} className="h-3" />
                        }
                        // Format paragraphs
                        return (
                          <p key={index} className="text-gray-700 leading-relaxed mb-3">
                            {line}
                          </p>
                        )
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-50 rounded-xl border border-gray-200">
                  <Mail className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-gray-900 mb-2">Follow-up email not generated yet</p>
                  <p className="text-gray-600">
                    AI-generated follow-up email will appear here.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'posts' && (
            <div>
              {posts && posts.length > 0 ? (
                <div className="space-y-4">
                  {posts.map((post: any) => (
                    <div key={post.id} className="border border-gray-200 rounded-xl p-6 bg-white hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 capitalize">
                          {post.platform}
                        </span>
                        <span className="text-xs text-gray-500">
                          {format(new Date(post.created_at), 'MMM d, yyyy')}
                        </span>
                      </div>
                      <p className="text-gray-700 mb-3">{post.content}</p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleCopy(post.content)}
                          className="inline-flex items-center px-3 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                        >
                          <Copy className="w-3 h-3 mr-1" />
                          Copy
                        </button>
                        {post.status === 'draft' && (
                          <button
                            onClick={() => handlePost(post.id)}
                            disabled={postMutation.isPending}
                            className="inline-flex items-center px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {postMutation.isPending ? (
                              <>
                                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                                Posting...
                              </>
                            ) : (
                              <>
                                <Send className="w-3 h-3 mr-1" />
                                Post
                              </>
                            )}
                          </button>
                        )}
                        {post.status === 'posted' && (
                          <span className="inline-flex items-center px-3 py-2 text-sm font-medium bg-green-100 text-green-800 rounded-lg">
                            <Check className="w-4 h-4 mr-2" />
                            Posted
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-50 rounded-xl border border-gray-200">
                  <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-gray-900 mb-2">No social media posts generated yet</p>
                  <p className="text-gray-600">
                    Generated posts will appear here.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'draft' && (
            <div>
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 md:p-8 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Draft Social Media Post</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Generate a draft post based on this meeting. You can copy it or post it directly to your connected social media accounts.
                </p>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Platform
                    </label>
                    <select
                      value={selectedPlatform}
                      onChange={(e) => setSelectedPlatform(e.target.value)}
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
                    >
                      <option value="linkedin">LinkedIn</option>
                      <option value="facebook">Facebook</option>
                    </select>
                  </div>
                  <div className="bg-white rounded-xl border border-gray-200 p-6 min-h-[200px]">
                    {draftPost ? (
                      <p className="text-gray-700 whitespace-pre-wrap text-sm">{draftPost}</p>
                    ) : (
                      <p className="text-gray-500 text-sm">
                        Draft post content will appear here after generation.
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        if (draftPost) {
                          handleCopy(draftPost)
                        }
                      }}
                      disabled={!draftPost}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4 mr-2" />
                          Copy
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => generatePostMutation.mutate(selectedPlatform)}
                      disabled={generatePostMutation.isPending || !meeting?.transcript_available}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {generatePostMutation.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 mr-2" />
                          Generate Post
                        </>
                      )}
                    </button>
                    {draftPost && posts && posts.length > 0 && (
                      <button
                        onClick={() => {
                          // Find the most recent post for the selected platform
                          const platformPost = posts
                            .filter((p: any) => p.platform === selectedPlatform)
                            .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
                          if (platformPost) {
                            handlePost(platformPost.id)
                          }
                        }}
                        disabled={postMutation.isPending}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {postMutation.isPending ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Posting...
                          </>
                        ) : (
                          <>
                            <Send className="w-4 h-4 mr-2" />
                            Post
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        isOpen={postConfirm.open}
        title="Post to Social Media"
        message="Are you sure you want to post this to social media?"
        confirmText="Post"
        cancelText="Cancel"
        onConfirm={confirmPost}
        onCancel={() => setPostConfirm({ postId: null, open: false })}
      />
    </div>
  )
}

