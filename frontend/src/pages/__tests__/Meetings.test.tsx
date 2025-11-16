/**
 * Tests for Meetings page component.
 * Tests meeting list rendering, loading states, error handling, and navigation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import Meetings from '../Meetings'
import api from '../../lib/api'

// Mock the API
vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}))

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    Link: ({ children, to, ...props }: any) => <a href={to} {...props}>{children}</a>,
  }
})

describe('Meetings Page', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    })
    vi.clearAllMocks()
  })

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          {component}
        </QueryClientProvider>
      </BrowserRouter>
    )
  }

  it('should render loading state', async () => {
    ;(api.get as any).mockImplementation(() => new Promise(() => {})) // Never resolves

    renderWithProviders(<Meetings />)

    expect(screen.getByText(/past meetings/i)).toBeInTheDocument()
    const loader = document.querySelector('.animate-spin')
    expect(loader).toBeTruthy()
  })

  it('should render meetings list', async () => {
    const mockMeetings = [
      {
        id: 1,
        title: 'Team Meeting',
        start_time: new Date(Date.now() - 86400000).toISOString(),
        end_time: new Date(Date.now() - 82800000).toISOString(),
        platform: 'zoom',
        transcript_available: true,
        attendees: [
          { id: 1, name: 'John Doe', email: 'john@example.com' },
          { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
        ],
      },
      {
        id: 2,
        title: 'Product Review',
        start_time: new Date(Date.now() - 172800000).toISOString(),
        end_time: new Date(Date.now() - 169200000).toISOString(),
        platform: 'meet',
        transcript_available: false,
        attendees: [{ id: 3, name: 'Bob Wilson', email: null }],
      },
    ]

    ;(api.get as any).mockResolvedValue({ data: mockMeetings })

    renderWithProviders(<Meetings />)

    await waitFor(() => {
      expect(screen.getByText('Team Meeting')).toBeInTheDocument()
      expect(screen.getByText('Product Review')).toBeInTheDocument()
    })

    // Check for platform icons (Zoom should be visible)
    expect(screen.getByText(/zoom/i) || screen.getByText(/meet/i)).toBeTruthy()
    
    // Check for transcript status
    expect(screen.getByText(/transcript available/i) || screen.getByText(/transcript pending/i)).toBeTruthy()
  })

  it('should render empty state when no meetings', async () => {
    ;(api.get as any).mockResolvedValue({ data: [] })

    renderWithProviders(<Meetings />)

    await waitFor(() => {
      expect(screen.getByText(/no past meetings found/i)).toBeInTheDocument()
    })
  })

  it('should display attendee information', async () => {
    const mockMeetings = [
      {
        id: 1,
        title: 'Team Meeting',
        start_time: new Date(Date.now() - 86400000).toISOString(),
        end_time: new Date(Date.now() - 82800000).toISOString(),
        platform: 'zoom',
        transcript_available: true,
        attendees: [
          { id: 1, name: 'John Doe', email: 'john@example.com' },
        ],
      },
    ]

    ;(api.get as any).mockResolvedValue({ data: mockMeetings })

    renderWithProviders(<Meetings />)

    await waitFor(() => {
      expect(screen.getByText(/1 attendee/i)).toBeInTheDocument()
      expect(screen.getByText(/John Doe/i)).toBeInTheDocument()
    })
  })

  it('should handle error state', async () => {
    ;(api.get as any).mockRejectedValue(new Error('Network error'))

    renderWithProviders(<Meetings />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load meetings/i)).toBeInTheDocument()
    })
  })

  it('should render meeting links', async () => {
    const mockMeetings = [
      {
        id: 1,
        title: 'Team Meeting',
        start_time: new Date(Date.now() - 86400000).toISOString(),
        end_time: new Date(Date.now() - 82800000).toISOString(),
        platform: 'zoom',
        transcript_available: true,
        attendees: [],
      },
    ]

    ;(api.get as any).mockResolvedValue({ data: mockMeetings })

    renderWithProviders(<Meetings />)

    await waitFor(() => {
      const link = screen.getByText('Team Meeting').closest('a')
      expect(link).toHaveAttribute('href', '/meetings/1')
    })
  })

  it('should format dates correctly', async () => {
    const testDate = new Date('2024-01-15T14:00:00Z')
    const mockMeetings = [
      {
        id: 1,
        title: 'Team Meeting',
        start_time: testDate.toISOString(),
        end_time: new Date(testDate.getTime() + 3600000).toISOString(),
        platform: 'zoom',
        transcript_available: true,
        attendees: [],
      },
    ]

    ;(api.get as any).mockResolvedValue({ data: mockMeetings })

    renderWithProviders(<Meetings />)

    await waitFor(() => {
      // Check that date is formatted (should contain month name)
      const dateText = screen.getByText(/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/i)
      expect(dateText).toBeInTheDocument()
    })
  })
})

