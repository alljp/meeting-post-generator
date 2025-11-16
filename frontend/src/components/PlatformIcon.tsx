import { Video } from 'lucide-react'

interface PlatformIconProps {
  platform: string
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const platformConfig: Record<string, { color: string; bgColor: string; label: string }> = {
  zoom: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    label: 'Zoom',
  },
  teams: {
    color: 'text-blue-500',
    bgColor: 'bg-blue-50',
    label: 'Teams',
  },
  meet: {
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    label: 'Meet',
  },
}

export default function PlatformIcon({ platform, size = 'md', showLabel = true }: PlatformIconProps) {
  const config = platformConfig[platform.toLowerCase()] || {
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    label: platform,
  }

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  }

  return (
    <div className={`inline-flex items-center gap-2 ${config.bgColor} px-2 py-1 rounded`}>
      <Video className={`${sizeClasses[size]} ${config.color}`} />
      {showLabel && (
        <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
      )}
    </div>
  )
}

