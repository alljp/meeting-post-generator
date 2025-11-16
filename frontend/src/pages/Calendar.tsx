import { Calendar as CalendarIcon } from 'lucide-react'
import CalendarEvents from '../components/CalendarEvents'

export default function Calendar() {
  return (
    <div className="px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-blue-100">
            <CalendarIcon className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Calendar Events</h1>
            <p className="text-gray-600 mt-2">
              Your upcoming meetings will appear here. Toggle the notetaker switch to enable transcription.
            </p>
          </div>
        </div>
      </div>
      <CalendarEvents />
    </div>
  )
}

