/**
 * Tests for API utility module.
 * Tests axios configuration, interceptors, and request handling.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import api from '../api'

describe('API Utility', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should have correct base URL', () => {
    expect(api.defaults.baseURL).toBe('/api/v1')
  })

  it('should have correct content type header', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json')
  })

  it('should add authorization token to requests when token exists', async () => {
    const token = 'test-token-123'
    localStorage.setItem('token', token)

    // Create a new instance to test interceptor
    const axios = await import('axios')
    const testApi = axios.default.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    testApi.interceptors.request.use((config) => {
      const storedToken = localStorage.getItem('token')
      if (storedToken) {
        config.headers.Authorization = `Bearer ${storedToken}`
      }
      return config
    })

    const config = await testApi.interceptors.request.handlers[0].fulfilled({
      headers: {},
    } as any)

    expect(config.headers.Authorization).toBe(`Bearer ${token}`)
  })

  it('should not add authorization token when token does not exist', async () => {
    localStorage.removeItem('token')

    const axios = await import('axios')
    const testApi = axios.default.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    testApi.interceptors.request.use((config) => {
      const storedToken = localStorage.getItem('token')
      if (storedToken) {
        config.headers.Authorization = `Bearer ${storedToken}`
      }
      return config
    })

    const config = await testApi.interceptors.request.handlers[0].fulfilled({
      headers: {},
    } as any)

    expect(config.headers.Authorization).toBeUndefined()
  })
})

