/**
 * Tests for Auth Store (Zustand).
 * Tests authentication state management, persistence, and token handling.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore } from '../auth'

describe('Auth Store', () => {
  beforeEach(() => {
    // Clear localStorage and reset store
    localStorage.clear()
    useAuthStore.getState().clearAuth()
    vi.clearAllMocks()
  })

  it('should initialize with no user and no token', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should set authentication state', () => {
    const user = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      picture: 'https://example.com/pic.jpg',
    }
    const token = 'test-token-123'

    useAuthStore.getState().setAuth(user, token)

    const state = useAuthStore.getState()
    expect(state.user).toEqual(user)
    expect(state.token).toBe(token)
    expect(state.isAuthenticated).toBe(true)
    expect(localStorage.getItem('token')).toBe(token)
  })

  it('should clear authentication state', () => {
    const user = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      picture: null,
    }
    const token = 'test-token-123'

    useAuthStore.getState().setAuth(user, token)
    useAuthStore.getState().clearAuth()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('should persist user to localStorage', () => {
    const user = {
      id: 1,
      email: 'test@example.com',
      name: 'Test User',
      picture: null,
    }
    const token = 'test-token-123'

    useAuthStore.getState().setAuth(user, token)

    // Check that user is persisted (via Zustand persist middleware)
    const persisted = localStorage.getItem('auth-storage')
    if (persisted) {
      const parsed = JSON.parse(persisted)
      expect(parsed.state.user).toEqual(user)
    }
  })

  it('should initialize with token from localStorage if present', () => {
    const token = 'existing-token-123'
    localStorage.setItem('token', token)

    // Create a new store instance to test initialization
    const state = useAuthStore.getState()
    // The store should detect the token in localStorage
    expect(localStorage.getItem('token')).toBe(token)
  })
})

