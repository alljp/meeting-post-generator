# Frontend Testing Guide

## Testing Framework: Vitest + React Testing Library

The frontend uses **Vitest** as the test runner and **React Testing Library** for component testing.

### Why Vitest?

- **Fast**: Built on Vite, extremely fast test execution
- **ESM first**: Native ES modules support
- **TypeScript**: First-class TypeScript support
- **Compatible**: Jest-compatible API, easy migration
- **Watch mode**: Fast hot module reload for tests

### Why React Testing Library?

- **User-centric**: Tests from user's perspective
- **Accessibility**: Encourages accessible components
- **Simple**: Minimal API, easy to learn
- **Best practices**: Follows React testing best practices

### Test Structure

```
frontend/src/
├── __tests__/              # Test files
│   └── App.test.tsx
├── components/
│   └── __tests__/
│       └── CalendarEvents.test.tsx
├── pages/
│   └── __tests__/
│       └── Home.test.tsx
├── lib/
│   └── __tests__/
│       └── api.test.ts
├── store/
│   └── __tests__/
│       └── auth.test.ts
└── test/
    ├── setup.ts            # Test setup and configuration
    └── utils.tsx          # Test utilities and helpers
```

### Running Tests

```bash
# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with UI
npm test -- --ui

# Run specific test file
npm test CalendarEvents

# Run with coverage
npm test -- --coverage
```

### Configuration

Tests are configured in `vite.config.ts`:

```typescript
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: './src/test/setup.ts',
}
```

### Test Utilities

#### renderWithProviders

Wrapper for rendering components with React Query provider:

```typescript
import { renderWithProviders } from '../test/utils'

renderWithProviders(<MyComponent />)
```

### Writing Tests

#### Component Test Example

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

#### Testing Async Operations

```typescript
import { waitFor } from '@testing-library/react'

it('should load data', async () => {
  render(<MyComponent />)
  
  await waitFor(() => {
    expect(screen.getByText('Loaded')).toBeInTheDocument()
  })
})
```

#### Testing User Interactions

```typescript
import { fireEvent } from '@testing-library/react'

it('should handle button click', () => {
  render(<MyComponent />)
  const button = screen.getByRole('button')
  fireEvent.click(button)
  expect(screen.getByText('Clicked')).toBeInTheDocument()
})
```

#### Mocking API Calls

```typescript
import { vi } from 'vitest'
import api from '../lib/api'

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

it('should fetch data', async () => {
  ;(api.get as any).mockResolvedValue({ data: mockData })
  render(<MyComponent />)
  // ...
})
```

#### Testing Zustand Stores

```typescript
import { useAuthStore } from '../store/auth'

it('should update auth state', () => {
  const user = { id: 1, email: 'test@example.com' }
  useAuthStore.getState().setAuth(user, 'token')
  
  const state = useAuthStore.getState()
  expect(state.user).toEqual(user)
})
```

### Best Practices

1. **Test behavior, not implementation**: Focus on what users see and do
2. **Use semantic queries**: Prefer `getByRole`, `getByLabelText` over `getByTestId`
3. **Test accessibility**: Use accessible queries
4. **Mock external dependencies**: Mock API calls, localStorage, etc.
5. **Clean up**: Tests should clean up after themselves
6. **Descriptive names**: Use clear, descriptive test names

### Query Priority (React Testing Library)

1. **getByRole**: Most accessible, preferred
2. **getByLabelText**: For form inputs
3. **getByPlaceholderText**: For inputs without labels
4. **getByText**: For text content
5. **getByDisplayValue**: For form values
6. **getByTestId**: Last resort, use sparingly

### Common Patterns

#### Testing Loading States

```typescript
it('should show loading state', () => {
  ;(api.get as any).mockImplementation(() => new Promise(() => {}))
  render(<MyComponent />)
  expect(screen.getByText('Loading...')).toBeInTheDocument()
})
```

#### Testing Error States

```typescript
it('should handle errors', async () => {
  ;(api.get as any).mockRejectedValue(new Error('Failed'))
  render(<MyComponent />)
  await waitFor(() => {
    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })
})
```

#### Testing Forms

```typescript
import userEvent from '@testing-library/user-event'

it('should submit form', async () => {
  const user = userEvent.setup()
  render(<MyForm />)
  
  await user.type(screen.getByLabelText('Email'), 'test@example.com')
  await user.click(screen.getByRole('button', { name: 'Submit' }))
  
  await waitFor(() => {
    expect(screen.getByText('Success')).toBeInTheDocument()
  })
})
```

### Coverage Goals

- **Statements**: >80%
- **Branches**: >75%
- **Functions**: >80%
- **Lines**: >80%
