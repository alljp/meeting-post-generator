import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, formatDistance } from 'date-fns'
import { Calendar, Video, MapPin, RefreshCw, Loader2 } from 'lucide-react'
import { useToastContext } from '../contexts/ToastContext'
import api from '@/lib/api'

interface CalendarEvent {
  id: number
  title: string
  description: string | null
  start_time: string
  end_time: string
  location: string | null
  meeting_link: string | null
  meeting_platform: string | null
  notetaker_enabled: boolean
  recall_bot_id: string | null
  google_event_id: string
}

const PlatformIcon = ({ platform }: { platform: string | null }) => {
  if (!platform) return null
  
  const icons: Record<string, { color: string; name: string }> = {
    zoom: { color: 'text-blue-600', name: 'Zoom' },
    teams: { color: 'text-blue-500', name: 'Teams' },
    meet: { color: 'text-green-600', name: 'Meet' },
  }
  
  const icon = icons[platform.toLowerCase()]
  if (!icon) return null
  
  return (
    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${icon.color} bg-gray-100`}>
      <Video className="w-3 h-3 mr-1" />
      {icon.name}
    </span>
  )
}

const EventCard = ({ event }: { event: CalendarEvent }) => {
  const queryClient = useQueryClient()
  
  const toggleMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const response = await api.patch(`/calendar/events/${event.id}/notetaker`, null, {
        params: { enabled },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
    },
  })
  
  const startTime = new Date(event.start_time)
  const endTime = new Date(event.end_time)
  const isToday = format(startTime, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')
  const isUpcoming = startTime > new Date()
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">{event.title}</h3>
            <PlatformIcon platform={event.meeting_platform} />
          </div>
          
          <div className="space-y-1 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span>
                {isToday ? 'Today' : format(startTime, 'MMM d, yyyy')} at {format(startTime, 'h:mm a')}
                {' - '}
                {format(endTime, 'h:mm a')}
              </span>
              {isUpcoming && (
                <span className="text-gray-400">
                  ({formatDistance(startTime, new Date(), { addSuffix: true })})
                </span>
              )}
            </div>
            
            {event.location && (
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                <span>{event.location}</span>
              </div>
            )}
            
            {event.meeting_link && (
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4" />
                <a
                  href={event.meeting_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Join Meeting
                </a>
              </div>
            )}
            
            {event.description && (
              <p className="text-gray-500 mt-2 line-clamp-2">{event.description}</p>
            )}
          </div>
        </div>
        
        <div className="ml-4">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={event.notetaker_enabled}
              onChange={(e) => toggleMutation.mutate(e.target.checked)}
              disabled={toggleMutation.isPending}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            <span className="ml-3 text-sm font-medium text-gray-700">
              {event.notetaker_enabled ? 'Notetaker ON' : 'Notetaker OFF'}
            </span>
          </label>
        </div>
      </div>
    </div>
  )
}

export default function CalendarEvents() {
  const queryClient = useQueryClient()
  const { success, error: showError } = useToastContext()
  
  const { data: events, isLoading, error } = useQuery<CalendarEvent[]>({
    queryKey: ['calendar-events'],
    queryFn: async () => {
      const response = await api.get('/calendar/events')
      return response.data
    },
  })
  
  const syncMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/calendar/sync')
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      success(`Synced ${data.synced} events (${data.created} created, ${data.updated} updated)`)
    },
    onError: (error: any) => {
      showError(`Sync failed: ${error.response?.data?.detail || error.message}`)
    },
  })
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load calendar events. Please try again.</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Upcoming Events</h2>
        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {syncMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Syncing...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              Sync Calendar
            </>
          )}
        </button>
      </div>
      
      {events && events.length > 0 ? (
        <div className="space-y-3">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      ) : (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">No upcoming events found</p>
          <p className="text-sm text-gray-500">
            Click "Sync Calendar" to fetch events from your Google Calendar
          </p>
        </div>
      )}
    </div>
  )
}

