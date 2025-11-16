/**
 * Tests for Home page component.
 * Tests rendering of welcome content and feature cards.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Home from '../Home'

describe('Home Page', () => {
  it('should render welcome message', () => {
    render(<Home />)
    expect(screen.getByText(/welcome to post-meeting generator/i)).toBeInTheDocument()
  })

  it('should render description text', () => {
    render(<Home />)
    expect(
      screen.getByText(/automatically generate and post social media content/i)
    ).toBeInTheDocument()
  })

  it('should render feature cards', () => {
    render(<Home />)
    
    expect(screen.getByText('Calendar Sync')).toBeInTheDocument()
    expect(screen.getByText('AI Transcription')).toBeInTheDocument()
    expect(screen.getByText('Social Media')).toBeInTheDocument()
  })

  it('should render feature descriptions', () => {
    render(<Home />)
    
    expect(screen.getByText(/connect your google calendar/i)).toBeInTheDocument()
    expect(screen.getByText(/recall.ai bots attend/i)).toBeInTheDocument()
    expect(screen.getByText(/generate and post content/i)).toBeInTheDocument()
  })
})

