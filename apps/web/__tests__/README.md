# TripSense AI - Frontend Testing Guide

## Overview

Frontend tests use Vitest and React Testing Library for comprehensive component and integration testing.

## Test Structure

```
__tests__/
├── README.md                   # This file
├── page.test.tsx               # Home page tests
└── components.test.tsx         # Component tests
```

## Running Tests

### Run All Tests
```bash
cd apps/web
npm test
```

### Run with UI
```bash
npm run test:ui
```

### Run with Coverage
```bash
npm run test:coverage
```

### Watch Mode
```bash
npm test -- --watch
```

## Test Configuration

- **Framework**: Vitest
- **Testing Library**: React Testing Library
- **Environment**: jsdom
- **Coverage**: v8 provider

## Writing Tests

### Basic Component Test

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

### User Interaction Tests

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Button from '@/components/Button'

describe('Button', () => {
  it('handles click events', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()
    
    render(<Button onClick={handleClick}>Click Me</Button>)
    
    await user.click(screen.getByRole('button'))
    
    expect(handleClick).toHaveBeenCalledOnce()
  })
})
```

### Async Tests

```typescript
import { describe, it, expect, waitFor } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataComponent from '@/components/DataComponent'

describe('DataComponent', () => {
  it('loads and displays data', async () => {
    render(<DataComponent />)
    
    await waitFor(() => {
      expect(screen.getByText('Loaded Data')).toBeInTheDocument()
    })
  })
})
```

## Best Practices

1. **Test User Behavior**: Focus on what users see and do
2. **Avoid Implementation Details**: Don't test internal state
3. **Use Semantic Queries**: Prefer `getByRole`, `getByLabelText`
4. **Clean Up**: Let Testing Library handle cleanup
5. **Mock Sparingly**: Only mock external dependencies

## Query Priority

Use queries in this order (from React Testing Library docs):

1. `getByRole` - Accessible to everyone
2. `getByLabelText` - Form elements
3. `getByPlaceholderText` - Form elements without labels
4. `getByText` - Non-interactive elements
5. `getByDisplayValue` - Current form values
6. `getByAltText` - Images
7. `getByTitle` - Last resort
8. `getByTestId` - Only for dynamic content

## Coverage Goals

- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

## Viewing Coverage

After running `npm run test:coverage`, open:
```bash
open coverage/index.html  # macOS
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Install dependencies
  run: cd apps/web && npm ci

- name: Run tests
  run: cd apps/web && npm run test:coverage

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./apps/web/coverage/coverage-final.json
```

## Debugging Tests

### Debug in Browser
```bash
npm run test:ui
```

### Console Output
```bash
npm test -- --reporter=verbose
```

## Common Patterns

### Testing Forms

```typescript
it('submits form data', async () => {
  const user = userEvent.setup()
  const onSubmit = vi.fn()
  
  render(<LoginForm onSubmit={onSubmit} />)
  
  await user.type(screen.getByLabelText('Email'), 'test@test.com')
  await user.type(screen.getByLabelText('Password'), 'password123')
  await user.click(screen.getByRole('button', { name: 'Submit' }))
  
  expect(onSubmit).toHaveBeenCalledWith({
    email: 'test@test.com',
    password: 'password123'
  })
})
```

### Testing API Calls

```typescript
import { vi } from 'vitest'

it('fetches and displays data', async () => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      json: () => Promise.resolve({ data: 'test' }),
    })
  ) as any
  
  render(<DataComponent />)
  
  await waitFor(() => {
    expect(screen.getByText('test')).toBeInTheDocument()
  })
})
```

### Testing Navigation

```typescript
import { useRouter } from 'next/navigation'

vi.mock('next/navigation', () => ({
  useRouter: vi.fn()
}))

it('navigates on click', async () => {
  const push = vi.fn()
  vi.mocked(useRouter).mockReturnValue({ push } as any)
  
  render(<NavigationComponent />)
  await user.click(screen.getByRole('link'))
  
  expect(push).toHaveBeenCalledWith('/destination')
})
```

## Next Steps

- [ ] Add component tests as components are created
- [ ] Add E2E tests with Playwright
- [ ] Add accessibility tests
- [ ] Add visual regression tests
- [ ] Set up coverage thresholds in CI

## References

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
