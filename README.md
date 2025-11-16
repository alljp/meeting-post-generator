# Post-Meeting Social Media Content Generator

A web application that automatically generates social media content from meeting transcripts using AI, integrating with Google Calendar, Recall.ai, and social media platforms.

## 🎯 Project Overview

This app helps advisors automatically create and post social media content after client meetings by:
1. Syncing with Google Calendar to track meetings
2. Using Recall.ai bots to attend and transcribe meetings
3. Generating AI-powered social media posts from transcripts
4. Posting directly to LinkedIn and Facebook

## 🏗️ Architecture

### Backend
- **FastAPI** (Python 3.11+) - Modern async API framework
- **PostgreSQL** - Database with SQLAlchemy ORM (async driver: psycopg)
- **Celery + Redis** - Background task processing
- **Alembic** - Database migrations
- **Pydantic** - Data validation and settings management
- **AuthLib** - OAuth 2.0 client library
- **OpenAI API** - AI-powered content generation

### Frontend
- **React 18 + TypeScript** - Modern UI framework
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **TanStack Query (React Query)** - Server state management and data fetching
- **Zustand** - Client state management
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library
- **Axios** - HTTP client
- **React Hook Form + Zod** - Form handling and validation

### Architecture Patterns
- **Factory Pattern** - Used in services (AI, Calendar, Social Media) to support multiple providers/strategies
- **Strategy Pattern** - Implemented for authentication providers (Google OAuth) and social media platforms (LinkedIn, Facebook)
- **Repository Pattern** - Database models abstracted through SQLAlchemy ORM
- **Dependency Injection** - FastAPI's dependency injection for API endpoints and database sessions

## 📋 Key Features

- ✅ Google OAuth login with multiple account support
- ✅ Google Calendar integration with event sync
- ✅ Recall.ai bot integration for meeting transcription
- ✅ AI-generated follow-up emails
- ✅ AI-generated social media posts
- ✅ LinkedIn and Facebook OAuth integration
- ✅ Direct posting to social media platforms
- ✅ Configurable automations per platform
- ✅ Settings page for bot timing and automations

## 🚀 Quick Start

See [PROJECT_PLAN.md](./PROJECT_PLAN.md) for detailed implementation plan.

## 📁 Project Structure

```
meeting-post-generator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/           # API v1 endpoints (auth, calendar, meetings, recall, settings, social)
│   │   ├── auth/             # Authentication strategies (Google, etc.)
│   │   ├── core/             # Core configuration and database setup
│   │   ├── models/           # SQLAlchemy database models
│   │   │   ├── automation.py
│   │   │   ├── calendar_event.py
│   │   │   ├── generated_post.py
│   │   │   ├── meeting.py
│   │   │   ├── settings.py
│   │   │   ├── social_account.py
│   │   │   └── user.py
│   │   ├── services/         # Business logic services
│   │   │   ├── ai/           # AI service (factory pattern with OpenAI strategy)
│   │   │   ├── calendar/     # Calendar service (factory pattern with Google strategy)
│   │   │   ├── social/       # Social media service (factory pattern with LinkedIn/Facebook strategies)
│   │   │   ├── recall_bot_manager.py
│   │   │   └── recall_service.py
│   │   ├── tasks/            # Celery background tasks
│   │   ├── utils/            # Utility functions (JWT, etc.)
│   │   └── main.py           # FastAPI application entry point
│   ├── alembic/              # Database migrations
│   │   └── versions/         # Migration versions
│   ├── tests/                # Backend tests (pytest)
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Backend Docker image
│   ├── Dockerfile.celery     # Celery worker Docker image
│   └── alembic.ini           # Alembic configuration
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── AutomationForm.tsx
│   │   │   ├── AutomationList.tsx
│   │   │   ├── CalendarEvents.tsx
│   │   │   ├── Layout.tsx
│   │   │   └── ...
│   │   ├── pages/            # Page components
│   │   │   ├── Home.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Calendar.tsx
│   │   │   ├── Meetings.tsx
│   │   │   ├── MeetingDetail.tsx
│   │   │   └── Settings.tsx
│   │   ├── contexts/          # React contexts (ToastContext)
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # API client and utilities
│   │   ├── store/            # Zustand stores (auth)
│   │   ├── App.tsx           # Main app component
│   │   └── main.tsx          # Application entry point
│   ├── package.json          # Node.js dependencies
│   ├── vite.config.ts        # Vite configuration
│   ├── tailwind.config.js    # Tailwind CSS configuration
│   └── Dockerfile            # Frontend Docker image
├── docker-compose.yml        # Development Docker Compose configuration
├── docker-compose.prod.yml   # Production Docker Compose configuration
└── README.md                 # This file
```

## 🔧 Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis

### Backend Setup
```bash
cd meeting-post-generator/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd meeting-post-generator/frontend
npm install
npm run dev
```

### Docker Compose Setup (Recommended)
```bash
# From project root
docker-compose up -d

# This will start:
# - PostgreSQL database (port 5432)
# - Redis (port 6379)
# - Backend API (port 8000)
# - Celery worker for background tasks
```

Note: Make sure to configure your `.env` file in `backend/` with required environment variables before starting the services.



## 🚀 Deployment

For deploying the application to production, see:
- **[DEPLOYMENT_QUICK_START.md](../DEPLOYMENT_QUICK_START.md)** - Step-by-step deployment instructions
- **[DEPLOYMENT_PLAN.md](../DEPLOYMENT_PLAN.md)** - Complete deployment options and strategies

Quick deployment using Docker Compose:
```bash
# Configure environment variables
cd meeting-post-generator/backend
cp .env.production.example .env
# Edit .env with production values

# Deploy
cd ../..
docker-compose -f docker-compose.prod.yml up -d
```

Or use the deployment scripts:
- **Linux/Mac**: `./deploy.sh production`
- **Windows**: `.\deploy.ps1 production`

## 🔐 Environment Variables

See PROJECT_PLAN.md for complete list of required environment variables.
For production deployment, see DEPLOYMENT_PLAN.md for environment configuration.

## 🧪 Testing

### Backend Testing
```bash
cd meeting-post-generator/backend
pytest
```

### Frontend Testing
```bash
cd meeting-post-generator/frontend
npm test
```

The backend includes comprehensive test coverage for:
- API endpoints (auth, calendar, meetings, recall, settings, social)
- Services (AI, calendar, recall, social media)
- Database models

## 📝 License

This is a challenge project for Jump Hiring Team.



