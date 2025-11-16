/**
 * Tests for CalendarEvents component.
 * Tests event rendering, loading states, error handling, and interactions.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import CalendarEvents from '../CalendarEvents'
import api from '../../lib/api'

// Mock the API
vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('CalendarEvents Component', () => {
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
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  it('should render loading state', async () => {
    ;(api.get as any).mockImplementation(() => new Promise(() => {})) // Never resolves

    renderWithProviders(<CalendarEvents />)

    // Check for loading spinner (Loader2 component renders)
    const loader = screen.queryByRole('status') || document.querySelector('.animate-spin')
    expect(loader).toBeTruthy()
  })

  it('should render events list', async () => {
    const mockEvents = [
      {
        id: 1,
        title: 'Team Meeting',
        description: 'Weekly sync',
        start_time: new Date(Date.now() + 3600000).toISOString(),
        end_time: new Date(Date.now() + 7200000).toISOString(),
        location: 'Conference Room A',
        meeting_link: 'https://zoom.us/j/123',
        meeting_platform: 'zoom',
        notetaker_enabled: false,
        recall_bot_id: null,
        google_event_id: 'event_123',
      },
      {
        id: 2,
        title: 'Product Review',
        description: null,
        start_time: new Date(Date.now() + 86400000).toISOString(),
        end_time: new Date(Date.now() + 90000000).toISOString(),
        location: null,
        meeting_link: 'https://meet.google.com/abc-def',
        meeting_platform: 'meet',
        notetaker_enabled: true,
        recall_bot_id: 'bot_123',
        google_event_id: 'event_456',
      },
    ]

    ;(api.get as any).mockResolvedValue({ data: mockEvents })

    renderWithProviders(<CalendarEvents />)

    await waitFor(() => {
      expect(screen.getByText('Team Meeting')).toBeInTheDocument()
      expect(screen.getByText('Product Review')).toBeInTheDocument()
    })
  })

  it('should render empty state when no events', async () => {
    ;(api.get as any).mockResolvedValue({ data: [] })

    renderWithProviders(<CalendarEvents />)

    await waitFor(() => {
      expect(screen.getByText(/no upcoming events found/i)).toBeInTheDocument()
    })
  })

  it('should handle sync button click', async () => {
    ;(api.get as any).mockResolvedValue({ data: [] })
    ;(api.post as any).mockResolvedValue({
      data: {
        synced: 5,
        created: 3,
        updated: 2,
        errors: [],
      },
    })

    // Mock window.alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    renderWithProviders(<CalendarEvents />)

    await waitFor(() => {
      expect(screen.getByText(/sync calendar/i)).toBeInTheDocument()
    })

    const syncButton = screen.getByText(/sync calendar/i)
    fireEvent.click(syncButton)

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/calendar/sync')
      expect(alertSpy).toHaveBeenCalled()
    })

    alertSpy.mockRestore()
  })

  it('should toggle notetaker for an event', async () => {
    const mockEvent = {
      id: 1,
      title: 'Test Meeting',
      description: null,
      start_time: new Date(Date.now() + 3600000).toISOString(),
      end_time: new Date(Date.now() + 7200000).toISOString(),
      location: null,
      meeting_link: null,
      meeting_platform: null,
      notetaker_enabled: false,
      recall_bot_id: null,
      google_event_id: 'event_123',
    }

    ;(api.get as any).mockResolvedValue({ data: [mockEvent] })
    ;(api.patch as any).mockResolvedValue({
      data: { ...mockEvent, notetaker_enabled: true },
    })

    renderWithProviders(<CalendarEvents />)

    await waitFor(() => {
      expect(screen.getByText('Test Meeting')).toBeInTheDocument()
    })

    // Find the toggle checkbox
    const toggle = screen.getByRole('checkbox', { hidden: true })
    fireEvent.click(toggle)

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith(
        `/calendar/events/1/notetaker`,
        null,
        expect.objectContaining({
          params: { enabled: true },
        })
      )
    })
  })

  it('should display error message on API failure', async () => {
    ;(api.get as any).mockRejectedValue(new Error('Network error'))

    renderWithProviders(<CalendarEvents />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load calendar events/i)).toBeInTheDocument()
    })
  })

  it('should display platform icons for events', async () => {
    const mockEvent = {
      id: 1,
      title: 'Zoom Meeting',
      description: null,
      start_time: new Date(Date.now() + 3600000).toISOString(),
      end_time: new Date(Date.now() + 7200000).toISOString(),
      location: null,
      meeting_link: 'https://zoom.us/j/123',
      meeting_platform: 'zoom',
      notetaker_enabled: false,
      recall_bot_id: null,
      google_event_id: 'event_123',
    }

    ;(api.get as any).mockResolvedValue({ data: [mockEvent] })

    renderWithProviders(<CalendarEvents />)

    await waitFor(() => {
      expect(screen.getByText('Zoom')).toBeInTheDocument()
    })
  })
})

