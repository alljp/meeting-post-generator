/**
 * Tests for MeetingDetail page component.
 * Tests meeting details rendering, tabs, transcript, email, posts, and draft post generation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import MeetingDetail from '../MeetingDetail'
import api from '@/lib/api.ts'

// Mock the API
vi.mock('@/lib/api.ts', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    Link: ({ children, to, ...props }: any) => <a href={to} {...props}>{children}</a>,
    useParams: () => ({ id: '1' }),
  }
})

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(() => Promise.resolve()),
  },
})

describe('MeetingDetail Page', () => {
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
      <MemoryRouter initialEntries={['/meetings/1']}>
        <QueryClientProvider client={queryClient}>
          {component}
        </QueryClientProvider>
      </MemoryRouter>
    )
  }

  const mockMeeting = {
    id: 1,
    title: 'Test Meeting',
    start_time: new Date(Date.now() - 86400000).toISOString(),
    end_time: new Date(Date.now() - 82800000).toISOString(),
    platform: 'zoom',
    transcript: 'This is a test transcript.',
    transcript_available: true,
    recording_url: 'https://example.com/recording.mp4',
    attendees: [
      { id: 1, name: 'John Doe', email: 'john@example.com' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
    ],
    recall_bot_id: 'bot_123',
  }

  it('should render loading state', async () => {
    ;(api.get as any).mockImplementation(() => new Promise(() => {}))

    renderWithProviders(<MeetingDetail />)

    const loader = document.querySelector('.animate-spin')
    expect(loader).toBeTruthy()
  })

  it('should render meeting details', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText('Test Meeting')).toBeInTheDocument()
      expect(screen.getByText(/John Doe/i)).toBeInTheDocument()
    })
  })

  it('should render transcript tab by default', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText(/transcript/i)).toBeInTheDocument()
      expect(screen.getByText('This is a test transcript.')).toBeInTheDocument()
    })
  })

  it('should switch to email tab', async () => {
    ;(api.get as any).mockImplementation((url: string) => {
      if (url.includes('/email')) {
        return Promise.resolve({ data: { email: 'Subject: Follow-up\n\nEmail content.' } })
      }
      return Promise.resolve({ data: mockMeeting })
    })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText('Test Meeting')).toBeInTheDocument()
    })

    const emailTab = screen.getByText(/follow-up email/i)
    fireEvent.click(emailTab)

    await waitFor(() => {
      expect(screen.getByText(/follow-up/i)).toBeInTheDocument()
    })
  })

  it('should switch to posts tab', async () => {
    const mockPosts = {
      posts: [
        {
          id: 1,
          platform: 'linkedin',
          content: 'LinkedIn post content',
          status: 'draft',
          created_at: new Date().toISOString(),
        },
      ],
    }

    ;(api.get as any).mockImplementation((url: string) => {
      if (url.includes('/posts')) {
        return Promise.resolve({ data: mockPosts })
      }
      return Promise.resolve({ data: mockMeeting })
    })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText('Test Meeting')).toBeInTheDocument()
    })

    const postsTab = screen.getByText(/social media posts/i)
    fireEvent.click(postsTab)

    await waitFor(() => {
      expect(screen.getByText('LinkedIn post content')).toBeInTheDocument()
    })
  })

  it('should switch to draft tab', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText('Test Meeting')).toBeInTheDocument()
    })

    const draftTab = screen.getByText(/draft post/i)
    fireEvent.click(draftTab)

    await waitFor(() => {
      expect(screen.getByText(/generate a draft post/i)).toBeInTheDocument()
    })
  })

  it('should copy transcript to clipboard', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText('This is a test transcript.')).toBeInTheDocument()
    })

    const copyButton = screen.getByText(/copy transcript/i)
    fireEvent.click(copyButton)

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('This is a test transcript.')
    })
  })

  it('should generate draft post', async () => {
    const mockGeneratedPost = {
      id: 1,
      platform: 'linkedin',
      content: 'Generated LinkedIn post',
      status: 'draft',
      message: 'Post generated successfully',
    }

    ;(api.get as any).mockResolvedValue({ data: mockMeeting })
    ;(api.post as any).mockResolvedValue({ data: mockGeneratedPost })

    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText('Test Meeting')).toBeInTheDocument()
    })

    // Switch to draft tab
    const draftTab = screen.getByText(/draft post/i)
    fireEvent.click(draftTab)

    await waitFor(() => {
      expect(screen.getByText(/generate post/i)).toBeInTheDocument()
    })

    const generateButton = screen.getByText(/generate post/i)
    fireEvent.click(generateButton)

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        '/meetings/1/generate-post?platform=linkedin'
      )
    })

    alertSpy.mockRestore()
  })

  it('should display recording link when available', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      const recordingLink = screen.getByText(/view recording/i)
      expect(recordingLink).toBeInTheDocument()
      expect(recordingLink.closest('a')).toHaveAttribute('href', 'https://example.com/recording.mp4')
    })
  })

  it('should handle error state', async () => {
    ;(api.get as any).mockRejectedValue(new Error('Network error'))

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load meeting/i)).toBeInTheDocument()
    })
  })

  it('should show transcript not available message', async () => {
    const meetingNoTranscript = {
      ...mockMeeting,
      transcript_available: false,
      transcript: null,
    }

    ;(api.get as any).mockResolvedValue({ data: meetingNoTranscript })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText(/transcript not available yet/i)).toBeInTheDocument()
    })
  })

  it('should change platform in draft tab', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText('Test Meeting')).toBeInTheDocument()
    })

    const draftTab = screen.getByText(/draft post/i)
    fireEvent.click(draftTab)

    await waitFor(() => {
      const platformSelect = screen.getByRole('combobox') || screen.getByDisplayValue('linkedin')
      expect(platformSelect).toBeInTheDocument()
      
      fireEvent.change(platformSelect, { target: { value: 'facebook' } })
      expect((platformSelect as HTMLSelectElement).value).toBe('facebook')
    })
  })

  it('should display attendees list', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      expect(screen.getByText(/2 attendees/i)).toBeInTheDocument()
      expect(screen.getByText(/John Doe/i)).toBeInTheDocument()
      expect(screen.getByText(/Jane Smith/i)).toBeInTheDocument()
    })
  })

  it('should show back to meetings link', async () => {
    ;(api.get as any).mockResolvedValue({ data: mockMeeting })

    renderWithProviders(<MeetingDetail />)

    await waitFor(() => {
      const backLink = screen.getByText(/back to meetings/i)
      expect(backLink).toBeInTheDocument()
      expect(backLink.closest('a')).toHaveAttribute('href', '/meetings')
    })
  })
})

