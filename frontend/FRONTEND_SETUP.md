# Frontend Setup and Testing Guide

## ✅ Completed Setup

### 1. Project Structure
- ✅ Vite + React + TypeScript configured
- ✅ Tailwind CSS configured
- ✅ React Router v6 setup
- ✅ React Query for server state
- ✅ Zustand for client state
- ✅ Axios for API calls

### 2. Authentication
- ✅ Auth store with Zustand (persisted to localStorage)
- ✅ Protected routes component
- ✅ Login page with Google OAuth placeholder
- ✅ Logout functionality in Layout

### 3. Pages & Components
- ✅ Home page (dashboard)
- ✅ Login page
- ✅ Calendar page (placeholder)
- ✅ Meetings page (placeholder)
- ✅ MeetingDetail page (placeholder)
- ✅ Settings page (placeholder)
- ✅ Layout with navigation

### 4. Testing Setup
- ✅ Vitest configured
- ✅ React Testing Library setup
- ✅ Test setup file
- ✅ Basic App test

### 5. Styling
- ✅ Fixed CSS conflicts
- ✅ Tailwind CSS properly configured
- ✅ Responsive layout

## 📦 Installation

**Prerequisites:**
- Node.js 18+ installed
- npm or yarn

**Install dependencies:**
```bash
cd frontend
npm install
```

## 🚀 Development

**Start development server:**
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

**Build for production:**
```bash
npm run build
```

**Preview production build:**
```bash
npm run preview
```

## 🧪 Testing

**Run tests:**
```bash
npm test
```

**Run tests in watch mode:**
```bash
npm test -- --watch
```

**Run tests with UI:**
```bash
npm test -- --ui
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.tsx          # Main layout with navigation
│   │   └── ProtectedRoute.tsx  # Route protection component
│   ├── pages/
│   │   ├── Home.tsx            # Dashboard
│   │   ├── Login.tsx           # Google OAuth login
│   │   ├── Calendar.tsx        # Calendar events view
│   │   ├── Meetings.tsx        # Past meetings list
│   │   ├── MeetingDetail.tsx   # Meeting details
│   │   └── Settings.tsx        # Settings page
│   ├── store/
│   │   └── auth.ts             # Authentication state (Zustand)
│   ├── lib/
│   │   └── api.ts              # Axios instance with interceptors
│   ├── test/
│   │   └── setup.ts            # Test setup file
│   ├── __tests__/
│   │   └── App.test.tsx        # Basic app tests
│   ├── App.tsx                 # Main app component with routes
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles + Tailwind
├── index.html
├── package.json
├── vite.config.ts              # Vite configuration
├── tsconfig.json               # TypeScript configuration
└── tailwind.config.js          # Tailwind configuration
```

## 🔧 Configuration

### API Proxy
The Vite dev server proxies `/api` requests to `http://localhost:8000` (backend).

### Environment Variables
Create a `.env` file in the `frontend/` directory if needed:
```env
VITE_API_URL=http://localhost:8000
```

### TypeScript Path Aliases
Use `@/` to import from `src/`:
```typescript
import { useAuthStore } from '@/store/auth'
```

## 🎨 Styling

- **Framework**: Tailwind CSS
- **Icons**: Lucide React
- **Design**: Modern, clean UI with responsive layout

## 🔐 Authentication Flow

1. User visits any protected route
2. `ProtectedRoute` checks `isAuthenticated` from auth store
3. If not authenticated, redirects to `/login`
4. User clicks "Sign in with Google"
5. Redirects to backend OAuth endpoint
6. Backend handles OAuth callback and returns JWT token
7. Frontend stores token and user info in auth store
8. User is redirected to home page

## 📝 Next Steps

1. **Implement Google OAuth flow** - Connect to backend auth endpoints
2. **Calendar integration** - Fetch and display calendar events
3. **Meeting management** - Display past meetings with data
4. **AI content generation** - Show generated posts and emails
5. **Social media OAuth** - Connect LinkedIn and Facebook
6. **Settings page** - Configure automations and bot timing
7. **Error handling** - Add error boundaries and toast notifications
8. **Loading states** - Add loading spinners and skeletons

## 🐛 Troubleshooting

**Port already in use:**
- Change port in `vite.config.ts` or kill the process using port 5173

**TypeScript errors:**
- Run `npm run build` to check for type errors
- Ensure all dependencies are installed

**Tests not running:**
- Ensure `jsdom` is installed: `npm install -D jsdom`
- Check `vite.config.ts` test configuration

**API calls failing:**
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in backend
- Verify proxy settings in `vite.config.ts`

## ✅ Testing Checklist

- [x] Frontend structure complete
- [x] Authentication state management
- [x] Protected routes
- [x] Navigation layout
- [x] Test setup configured
- [ ] Dependencies installed (requires Node.js)
- [ ] Dev server tested (requires Node.js)
- [ ] Build tested (requires Node.js)
- [ ] Tests passing (requires Node.js)

## 📚 Resources

- [Vite Documentation](https://vitejs.dev/)
- [React Router v6](https://reactrouter.com/)
- [React Query](https://tanstack.com/query/latest)
- [Zustand](https://zustand-demo.pmnd.rs/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vitest](https://vitest.dev/)

