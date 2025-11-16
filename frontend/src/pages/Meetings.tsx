import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Calendar, Users, FileText, Loader2, MessageSquare } from 'lucide-react'
import api from '@/lib'
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
  transcript_available: boolean
  attendees: Attendee[]
}

export default function Meetings() {
  const { data: meetings, isLoading, error } = useQuery<Meeting[]>({
    queryKey: ['meetings'],
    queryFn: async () => {
      const response = await api.get('/meetings')
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-purple-100">
              <MessageSquare className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Past Meetings</h1>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-purple-100">
              <MessageSquare className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Past Meetings</h1>
            </div>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-800 font-medium">Failed to load meetings. Please try again.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-purple-100">
            <MessageSquare className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Past Meetings</h1>
            <p className="text-gray-600 mt-2">
              View your past meetings and generated content.
            </p>
          </div>
        </div>
      </div>

      {meetings && meetings.length > 0 ? (
        <div className="space-y-4">
          {meetings.map((meeting) => {
            const startTime = new Date(meeting.start_time)
            const endTime = new Date(meeting.end_time)
            
            return (
              <Link
                key={meeting.id}
                to={`/meetings/${meeting.id}`}
                className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-200 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-semibold text-gray-900">{meeting.title}</h3>
                      <PlatformIcon platform={meeting.platform} size="sm" />
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
                            {meeting.attendees.length <= 3 && (
                              <span className="ml-1 text-gray-500">
                                ({meeting.attendees.map(a => a.name).join(', ')})
                              </span>
                            )}
                          </span>
                        </div>
                      )}

                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        <span className={meeting.transcript_available ? 'text-green-600' : 'text-gray-400'}>
                          {meeting.transcript_available ? 'Transcript available' : 'Transcript pending'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="ml-4">
                    <MessageSquare className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      ) : (
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-12 text-center border border-gray-200">
          <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">No past meetings found</p>
          <p className="text-gray-600">
            Meetings will appear here after they are completed and transcripts are available.
          </p>
        </div>
      )}
    </div>
  )
}

