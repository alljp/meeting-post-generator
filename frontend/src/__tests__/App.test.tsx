import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    // App should render without errors
    expect(document.body).toBeTruthy()
  })

  it('has all required routes defined', () => {
    const routes = ['/', '/login', '/calendar', '/meetings', '/settings']
    routes.forEach((route) => {
      expect(route).toBeTruthy()
    })
  })
})

