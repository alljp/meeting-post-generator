from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field, field_validator
from typing import List, Union


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Post-Meeting Generator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # CORS - Can be set via comma-separated string or list
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/postmeeting",
        description="PostgreSQL database URL"
    )
    
    # Security - REQUIRED in production
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token signing. MUST be set in production!"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # OAuth - Google - Required (with defaults for development)
    GOOGLE_CLIENT_ID: str = Field(
        default="",
        description="Google OAuth Client ID"
    )
    GOOGLE_CLIENT_SECRET: str = Field(
        default="",
        description="Google OAuth Client Secret"
    )
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/google/callback",
        description="Google OAuth redirect URI"
    )
    
    # OAuth - LinkedIn - Required (with defaults for development)
    LINKEDIN_CLIENT_ID: str = Field(
        default="",
        description="LinkedIn OAuth Client ID"
    )
    LINKEDIN_CLIENT_SECRET: str = Field(
        default="",
        description="LinkedIn OAuth Client Secret"
    )
    LINKEDIN_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/linkedin/callback",
        description="LinkedIn OAuth redirect URI"
    )
    
    # OAuth - Facebook - Optional
    FACEBOOK_CLIENT_ID: str = Field(
        default="",
        description="Facebook OAuth Client ID (optional)"
    )
    FACEBOOK_CLIENT_SECRET: str = Field(
        default="",
        description="Facebook OAuth Client Secret (optional)"
    )
    FACEBOOK_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/facebook/callback",
        description="Facebook OAuth redirect URI"
    )
    
    # APIs - Required (with defaults for development)
    RECALL_API_KEY: str = Field(
        default="",
        description="Recall.ai API key"
    )
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-3.5-turbo",
        description="OpenAI model to use. Options: gpt-3.5-turbo, gpt-4o, gpt-4-turbo"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery"
    )
    
    # Frontend URL
    FRONTEND_URL: str = Field(
        default="http://localhost:5173",
        description="Frontend application URL"
    )
    
    # Backend URL (for OAuth redirects)
    BACKEND_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API URL"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_parse_none_str="",
    )


settings = Settings()

