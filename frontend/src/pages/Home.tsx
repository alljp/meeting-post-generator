import { Link } from 'react-router-dom'
import { Calendar, MessageSquare, Sparkles, Zap, ArrowRight, CheckCircle2 } from 'lucide-react'

export default function Home() {
  return (
    <div className="px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero Section */}
      <div className="mb-12">
        <div className="max-w-3xl">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Transform Your Meetings Into
            <span className="text-blue-600"> Social Content</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Automatically generate and post engaging social media content from your meeting transcripts. 
            Let AI handle the heavy lifting while you focus on what matters.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              to="/calendar"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              View Calendar
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link
              to="/meetings"
              className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              View Meetings
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-blue-100 mb-4">
            <Calendar className="h-6 w-6 text-blue-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Calendar Sync</h2>
          <p className="text-gray-600 mb-4">
            Connect multiple Google accounts and automatically track all your meetings. 
            Never miss an opportunity to create content.
          </p>
          <ul className="space-y-2">
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              Multiple account support
            </li>
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              Automatic event detection
            </li>
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              Real-time sync
            </li>
          </ul>
        </div>

        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-purple-100 mb-4">
            <Zap className="h-6 w-6 text-purple-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">AI Transcription</h2>
          <p className="text-gray-600 mb-4">
            Recall.ai bots automatically attend your meetings and generate accurate transcripts. 
            No manual note-taking required.
          </p>
          <ul className="space-y-2">
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              Automated bot attendance
            </li>
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              Full meeting transcripts
            </li>
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              Configurable join time
            </li>
          </ul>
        </div>

        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-green-100 mb-4">
            <Sparkles className="h-6 w-6 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Social Media</h2>
          <p className="text-gray-600 mb-4">
            AI-powered content generation for LinkedIn and Facebook. 
            Create engaging posts with a single click.
          </p>
          <ul className="space-y-2">
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              AI-generated content
            </li>
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              One-click posting
            </li>
            <li className="flex items-center text-sm text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
              Custom automations
            </li>
          </ul>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 md:p-12">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-2 text-center">How It Works</h2>
          <p className="text-gray-600 text-center mb-8">
            Get started in three simple steps
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-blue-600 text-white text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Connect Calendar</h3>
              <p className="text-gray-600">
                Link your Google Calendar accounts to automatically detect meetings
              </p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-blue-600 text-white text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Attend Meetings</h3>
              <p className="text-gray-600">
                AI bots join your meetings and generate transcripts automatically
              </p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-blue-600 text-white text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Post Content</h3>
              <p className="text-gray-600">
                Review AI-generated posts and publish to your social media accounts
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

