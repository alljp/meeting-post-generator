#!/usr/bin/env python3
"""
Quick diagnostic script to check Google OAuth configuration.
Run this to verify your Google OAuth credentials are set correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.core.config import settings
    
    print("=" * 60)
    print("Google OAuth Configuration Check")
    print("=" * 60)
    print()
    
    # Check if credentials are set
    has_client_id = bool(settings.GOOGLE_CLIENT_ID)
    has_client_secret = bool(settings.GOOGLE_CLIENT_SECRET)
    
    print(f"✓ GOOGLE_CLIENT_ID is set: {has_client_id}")
    if has_client_id:
        client_id_preview = settings.GOOGLE_CLIENT_ID[:20] + "..." if len(settings.GOOGLE_CLIENT_ID) > 20 else settings.GOOGLE_CLIENT_ID
        print(f"  Preview: {client_id_preview}")
        if not settings.GOOGLE_CLIENT_ID.strip():
            print("  ⚠ WARNING: GOOGLE_CLIENT_ID is empty/whitespace only")
    else:
        print("  ❌ ERROR: GOOGLE_CLIENT_ID is not set")
    
    print()
    print(f"✓ GOOGLE_CLIENT_SECRET is set: {has_client_secret}")
    if has_client_secret:
        secret_preview = settings.GOOGLE_CLIENT_SECRET[:10] + "..." if len(settings.GOOGLE_CLIENT_SECRET) > 10 else settings.GOOGLE_CLIENT_SECRET
        print(f"  Preview: {secret_preview[:13]}...")
        if not settings.GOOGLE_CLIENT_SECRET.strip():
            print("  ⚠ WARNING: GOOGLE_CLIENT_SECRET is empty/whitespace only")
    else:
        print("  ❌ ERROR: GOOGLE_CLIENT_SECRET is not set")
    
    print()
    print(f"✓ GOOGLE_REDIRECT_URI: {settings.GOOGLE_REDIRECT_URI}")
    print()
    
    # Validate format
    errors = []
    if has_client_id:
        # Google Client IDs typically end with .apps.googleusercontent.com or are just long strings
        if len(settings.GOOGLE_CLIENT_ID.strip()) < 10:
            errors.append("GOOGLE_CLIENT_ID seems too short (should be longer)")
    else:
        errors.append("GOOGLE_CLIENT_ID is missing")
    
    if has_client_secret:
        # Google Client Secrets are typically long strings
        if len(settings.GOOGLE_CLIENT_SECRET.strip()) < 10:
            errors.append("GOOGLE_CLIENT_SECRET seems too short (should be longer)")
    else:
        errors.append("GOOGLE_CLIENT_SECRET is missing")
    
    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("To fix:")
        print("1. Make sure you have a .env file in the backend/ directory")
        print("2. Add the following to your .env file:")
        print("   GOOGLE_CLIENT_ID=your-client-id-here")
        print("   GOOGLE_CLIENT_SECRET=your-client-secret-here")
        print("3. Get these values from Google Cloud Console:")
        print("   https://console.cloud.google.com/apis/credentials")
        print("4. Make sure the redirect URI matches:")
        print(f"   {settings.GOOGLE_REDIRECT_URI}")
        sys.exit(1)
    
    # Try to create OAuth flow (this will catch invalid credentials)
    try:
        from app.auth.strategies.google import GoogleOAuthProvider
        provider = GoogleOAuthProvider()
        flow = provider._get_oauth_flow()
        print("✓ OAuth flow created successfully")
        print()
        print("✓ Configuration appears valid!")
        print()
        print("If you're still getting 'Error 401: invalid_client', verify:")
        print("1. The Client ID and Secret match exactly what's in Google Cloud Console")
        print("2. The OAuth 2.0 Client ID is not disabled in Google Cloud Console")
        print("3. The redirect URI in your .env matches what's configured in Google Cloud Console")
        print(f"   Expected: {settings.GOOGLE_REDIRECT_URI}")
        print("4. You've authorized the correct APIs (OAuth2, Calendar, etc.)")
    except ValueError as e:
        print("❌ ERROR creating OAuth flow:")
        print(f"   {str(e)}")
        sys.exit(1)
    except Exception as e:
        print("❌ UNEXPECTED ERROR:")
        print(f"   {type(e).__name__}: {str(e)}")
        sys.exit(1)
    
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Failed to check configuration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

