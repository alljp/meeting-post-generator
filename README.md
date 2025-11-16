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
- **FastAPI** (Python) - Modern async API framework
- **PostgreSQL** - Database with SQLAlchemy ORM
- **Celery + Redis** - Background task processing
- **Alembic** - Database migrations

### Frontend
- **React 18 + TypeScript** - Modern UI framework
- **Tailwind CSS + shadcn/ui** - Styling and components
- **React Query** - Server state management
- **Vite** - Build tool

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
post-meeting-generator/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/          # API endpoints
│   │   │   ├── models/       # Database models
│   │   │   ├── services/     # Business logic
│   │   │   ├── tasks/        # Celery tasks
│   │   │   └── utils/        # Utilities
│   │   ├── alembic/          # Database migrations
│   │   └── tests/            # Backend tests
│   └── frontend/
│       └── src/              # React application
├── docker-compose.yml        # Docker compose configuration
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
cd src/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd src/frontend
npm install
npm run dev
```

## 📚 Documentation

- [PROJECT_PLAN.md](./PROJECT_PLAN.md) - Complete implementation plan with phases, API design, and architecture

## 🔐 Environment Variables

See PROJECT_PLAN.md for complete list of required environment variables.

## 🧪 Testing

- Backend: `pytest` in `src/backend/` directory
- Frontend: `npm test` in `src/frontend/` directory

## 📝 License

This is a challenge project for Jump Hiring Team.



