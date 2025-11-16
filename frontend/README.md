# Post-Meeting Generator - Frontend

React + TypeScript frontend for the Post-Meeting Social Media Content Generator application.

## Quick Start

### Prerequisites
- Node.js 18+ and npm

### Installation
```bash
npm install
```

### Development
```bash
npm run dev
```
Visit `http://localhost:5173`

### Build
```bash
npm run build
```

### Test
```bash
npm test
```

## Features

- ✅ Google OAuth authentication
- ✅ Protected routes
- ✅ Calendar integration (ready for implementation)
- ✅ Meeting management (ready for implementation)
- ✅ Social media posting (ready for implementation)
- ✅ Settings and automations (ready for implementation)

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router v6** - Routing
- **React Query** - Server state management
- **Zustand** - Client state management
- **Axios** - HTTP client
- **Vitest** - Testing

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   ├── pages/           # Page components
│   ├── store/           # Zustand stores
│   ├── lib/             # Utilities and API client
│   ├── test/            # Test setup
│   └── __tests__/       # Test files
├── public/              # Static assets
└── ...
```

## Documentation

- [Frontend Setup Guide](./FRONTEND_SETUP.md) - Detailed setup instructions
- [Testing Guide](./TESTING.md) - Testing documentation

## API Integration

The frontend communicates with the backend API at `http://localhost:8000`. The Vite dev server proxies `/api` requests to the backend.

## Environment Variables

Create a `.env` file if needed:
```env
VITE_API_URL=http://localhost:8000
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests
- `npm run lint` - Run ESLint

## Next Steps

See [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) for implementation details and next steps.

