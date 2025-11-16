# Environment Variables Setup Guide

## Quick Start

1. **Copy the example file:**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit `.env` and fill in your actual values:**
   ```bash
   # Use your preferred editor
   nano .env
   # or
   code .env
   ```

3. **Generate a secure SECRET_KEY:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Copy the output and paste it as your `SECRET_KEY` value.

## Required Variables

The following environment variables **must** be set for the application to run:

### Security
- `SECRET_KEY` - Secret key for JWT token signing (generate a secure random key)

### Database
- `DATABASE_URL` - PostgreSQL connection string

### OAuth - Google
- `GOOGLE_CLIENT_ID` - Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth Client Secret

### OAuth - LinkedIn
- `LINKEDIN_CLIENT_ID` - LinkedIn OAuth Client ID
- `LINKEDIN_CLIENT_SECRET` - LinkedIn OAuth Client Secret

### External APIs
- `RECALL_API_KEY` - Recall.ai API key
- `OPENAI_API_KEY` - OpenAI API key

## Optional Variables

These have sensible defaults but can be overridden:

- `GOOGLE_REDIRECT_URI` - Default: `http://localhost:8000/api/v1/auth/google/callback`
- `LINKEDIN_REDIRECT_URI` - Default: `http://localhost:8000/api/v1/auth/linkedin/callback`
- `FACEBOOK_CLIENT_ID` - Optional (leave empty if not using Facebook)
- `FACEBOOK_CLIENT_SECRET` - Optional (leave empty if not using Facebook)
- `OPENAI_MODEL` - Default: `gpt-3.5-turbo`
- `REDIS_URL` - Default: `redis://localhost:6379/0`
- `FRONTEND_URL` - Default: `http://localhost:5173`
- `DEBUG` - Default: `false`

## Getting API Keys

### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Configure OAuth consent screen
6. Copy Client ID and Client Secret

### LinkedIn OAuth
1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Create a new app
3. Add redirect URL: `http://localhost:8000/api/v1/auth/linkedin/callback`
4. Copy Client ID and Client Secret

### Recall.ai
1. Sign up at [Recall.ai](https://recall.ai)
2. Go to API settings
3. Copy your API key

### OpenAI
1. Sign up at [OpenAI Platform](https://platform.openai.com/)
2. Go to API Keys section
3. Create a new API key
4. Copy the key (it's only shown once!)

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` to version control
- `.env` is already in `.gitignore`
- Rotate keys immediately if they're exposed
- Use different keys for development and production
- Generate a strong `SECRET_KEY` (at least 32 characters)

## Production Deployment

For production, use a secrets management service:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Environment variables in your hosting platform

Never hardcode secrets in your code!

