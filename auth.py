"""
Security & Session Layer

This module handles authentication, authorization, and session management.
It provides Google OAuth 2.0 integration for Gmail and Google Sheets access,
session state management, and security middleware.

Dependencies: streamlit, google_auth_oauthlib, google.auth, config.py, database.py
Used by: app.py, integrations.py, database.py
"""

import logging
import json
import time
import os
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
import requests
from urllib.parse import urlparse, parse_qs

# Allow HTTP for localhost development (OAuth 2.0 requirement)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from config import config
from database import db_manager, User

logger = logging.getLogger(__name__)

@dataclass
class OAuthTokens:
    """OAuth token data structure."""
    access_token: str
    refresh_token: str
    token_uri: str
    client_id: str
    client_secret: str
    scopes: list
    expiry: datetime

class AuthManager:
    """Manages authentication and authorization for the platform."""
    
    def __init__(self):
        self.api_config = config.get_api_config()
        self.session_state = st.session_state
        self._setup_session_state()
        logger.info("Auth manager initialized successfully")
    
    def _setup_session_state(self):
        """Initialize Streamlit session state for authentication."""
        if 'authenticated' not in self.session_state:
            self.session_state.authenticated = False
        if 'user_id' not in self.session_state:
            self.session_state.user_id = None
        if 'user_email' not in self.session_state:
            self.session_state.user_email = None
        if 'oauth_tokens' not in self.session_state:
            self.session_state.oauth_tokens = None
        if 'last_auth_check' not in self.session_state:
            self.session_state.last_auth_check = None
    
    def get_oauth_url(self, service: str) -> str:
        """Generate OAuth URL for Gmail or Google Sheets."""
        try:
            if service == 'gmail':
                client_id = self.api_config.gmail_client_id
                client_secret = self.api_config.gmail_client_secret
                redirect_uri = self.api_config.gmail_redirect_uri
                scopes = [
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly'
                ]
            elif service == 'sheets':
                client_id = self.api_config.sheets_client_id
                client_secret = self.api_config.sheets_client_secret
                redirect_uri = self.api_config.sheets_redirect_uri
                scopes = [
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/spreadsheets.readonly'
                ]
            else:
                raise ValueError(f"Unsupported service: {service}")
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=scopes
            )
            
            flow.redirect_uri = redirect_uri
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='false',  # Changed from 'true' to 'false'
                prompt='consent'
            )
            
            logger.info(f"Generated OAuth URL for {service}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to generate OAuth URL for {service}: {e}")
            raise
    
    async def handle_oauth_callback(self, service: str, authorization_response: str) -> bool:
        """Handle OAuth callback and exchange authorization code for tokens."""
        try:
            if service == 'gmail':
                client_id = self.api_config.gmail_client_id
                client_secret = self.api_config.gmail_client_secret
                redirect_uri = self.api_config.gmail_redirect_uri
                scopes = [
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly'
                ]
            elif service == 'sheets':
                client_id = self.api_config.sheets_client_id
                client_secret = self.api_config.sheets_client_secret
                redirect_uri = self.api_config.sheets_redirect_uri
                scopes = [
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/spreadsheets.readonly'
                ]
            else:
                raise ValueError(f"Unsupported service: {service}")
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=scopes
            )
            
            flow.redirect_uri = redirect_uri
            
            # Extract authorization code - handle both full URLs and just the code
            if "code=" in authorization_response:
                # It's a full callback URL, extract the code
                parsed_url = urlparse(authorization_response)
                query_params = parse_qs(parsed_url.query)
                authorization_code = query_params.get('code', [None])[0]
            else:
                # It's just the authorization code
                authorization_code = authorization_response.strip()
            
            if not authorization_code:
                raise ValueError("No authorization code provided")
            
            logger.info(f"Processing authorization code: {authorization_code[:20]}...")
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Validate that we received the expected scopes for this service
            received_scopes = set(credentials.scopes)
            expected_scopes = set(scopes)
            
            logger.info(f"Expected scopes for {service}: {expected_scopes}")
            logger.info(f"Received scopes: {received_scopes}")
            
            # Check if we have the minimum required scopes for this service
            if service == 'gmail':
                required_scopes = {
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly'
                }
                # For Gmail, we should NOT have Sheets scopes
                forbidden_scopes = {
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/spreadsheets.readonly'
                }
                if forbidden_scopes.intersection(received_scopes):
                    logger.warning(f"Gmail OAuth received unexpected Sheets scopes: {forbidden_scopes.intersection(received_scopes)}")
                    logger.info("This might be due to cached Google permissions. Proceeding with Gmail authentication...")
                    # Don't fail - just log the warning
            elif service == 'sheets':
                required_scopes = {
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/spreadsheets.readonly'
                }
            else:
                required_scopes = set()
            
            if not required_scopes.issubset(received_scopes):
                logger.error(f"Missing required scopes for {service}. Expected: {required_scopes}, Got: {received_scopes}")
                raise ValueError(f"OAuth callback received wrong scopes for {service}. Please ensure you're using the correct authorization URL.")
            
            # Store tokens in session state for the specific service
            oauth_tokens = OAuthTokens(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes,
                expiry=credentials.expiry
            )
            
            self.set_oauth_tokens(oauth_tokens, service)
            
            # Get user info and authenticate
            await self._authenticate_user(credentials)
            
            # Set service-specific authentication status
            if service == 'gmail':
                self.session_state.gmail_authenticated = True
                logger.info("Gmail authentication completed successfully")
            elif service == 'sheets':
                self.session_state.sheets_authenticated = True
                self.session_state.sheets_connected = True
                logger.info("Google Sheets authentication completed successfully")
            
            logger.info(f"OAuth callback handled successfully for {service}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback for {service}: {e}")
            logger.error(f"Authorization response: {authorization_response[:200]}...")
            logger.error(f"Service: {service}, Client ID: {client_id[:10]}...")
            
            # Provide more helpful error messages
            if "wrong scopes" in str(e):
                if service == 'gmail':
                    logger.error("Gmail OAuth failed: You may have used the Google Sheets authorization URL instead of Gmail")
                elif service == 'sheets':
                    logger.error("Google Sheets OAuth failed: You may have used the Gmail authorization URL instead of Sheets")
                logger.error("Please ensure you're using the correct authorization button for each service")
            
            return False
    
    async def _authenticate_user(self, credentials: Credentials):
        """Authenticate user using OAuth credentials."""
        try:
            # Get user info from Google
            user_info = await self._get_google_user_info(credentials)
            
            if not user_info:
                raise ValueError("Failed to retrieve user information from Google")
            
            # Check if user exists in database
            user = await db_manager.get_user(user_info['id'])
            
            if not user:
                # Create new user
                user_data = {
                    'user_id': user_info['id'],
                    'email': user_info['email'],
                    'name': user_info['name'],
                    'company': user_info.get('hd', 'Unknown'),  # Hosted domain
                    'role': 'user',
                    'created_at': datetime.utcnow(),
                    'last_login': datetime.utcnow(),
                    'settings': {},
                    'subscription_tier': 'basic'
                }
                
                await db_manager.create_user(user_data)
                logger.info(f"Created new user: {user_info['email']}")
            else:
                # Update last login
                await db_manager.update_user(user_info['id'], {
                    'last_login': datetime.utcnow()
                })
                logger.info(f"User logged in: {user_info['email']}")
            
            # Set session state
            self.session_state.authenticated = True
            self.session_state.user_id = user_info['id']
            self.session_state.user_email = user_info['email']
            self.session_state.user_name = user_info.get('name', user_info['email'].split('@')[0])
            self.session_state.last_auth_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to authenticate user: {e}")
            raise
    
    async def _get_google_user_info(self, credentials: Credentials) -> Optional[Dict[str, Any]]:
        """Get user information from Google OAuth."""
        try:
            headers = {'Authorization': f'Bearer {credentials.token}'}
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve user info: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        if not self.session_state.authenticated:
            return False
        
        # Check if tokens are still valid
        if self.session_state.oauth_tokens:
            if self.session_state.oauth_tokens.expiry <= datetime.utcnow():
                logger.info("OAuth tokens expired, user needs to re-authenticate")
                self.session_state.authenticated = False
                return False
        
        return True
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current authenticated user ID."""
        if self.is_authenticated():
            return self.session_state.user_id
        return None
    
    def get_current_user_email(self) -> Optional[str]:
        """Get current authenticated user email."""
        if self.is_authenticated():
            return self.session_state.user_email
        return None
    
    def get_current_user_name(self) -> Optional[str]:
        """Get current authenticated user name."""
        if self.is_authenticated():
            return self.session_state.user_name
        return None
    
    def get_oauth_tokens(self, service: str = None) -> Optional[OAuthTokens]:
        """Get OAuth tokens for a specific service or all tokens."""
        if service:
            return self.session_state.get(f'{service}_oauth_tokens')
        else:
            # Return the most recently used tokens (for backward compatibility)
            return (self.session_state.get('gmail_oauth_tokens') or 
                   self.session_state.get('sheets_oauth_tokens'))
    
    def set_oauth_tokens(self, tokens: OAuthTokens, service: str):
        """Set OAuth tokens for a specific service."""
        self.session_state[f'{service}_oauth_tokens'] = tokens
        logger.info(f"Stored OAuth tokens for {service}")
    
    def clear_oauth_tokens(self, service: str = None):
        """Clear OAuth tokens for a specific service or all services."""
        if service:
            if f'{service}_oauth_tokens' in self.session_state:
                del self.session_state[f'{service}_oauth_tokens']
            logger.info(f"Cleared OAuth tokens for {service}")
        else:
            # Clear all service tokens
            for key in list(self.session_state.keys()):
                if key.endswith('_oauth_tokens'):
                    del self.session_state[key]
            logger.info("Cleared all OAuth tokens")
    
    async def refresh_tokens(self) -> bool:
        """Refresh OAuth tokens if they're expired."""
        try:
            if not self.session_state.oauth_tokens:
                return False
            
            tokens = self.session_state.oauth_tokens
            
            if tokens.expiry > datetime.utcnow():
                return True  # Tokens are still valid
            
            # Create credentials object for refresh
            creds = Credentials(
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri=tokens.token_uri,
                client_id=tokens.client_id,
                client_secret=tokens.client_secret,
                scopes=tokens.scopes
            )
            
            # Refresh tokens
            creds.refresh(Request())
            
            # Update session state
            updated_tokens = OAuthTokens(
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                token_uri=creds.token_uri,
                client_id=creds.client_id,
                client_secret=creds.client_secret,
                scopes=creds.scopes,
                expiry=creds.expiry
            )
            
            self.session_state.oauth_tokens = updated_tokens
            logger.info("OAuth tokens refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh OAuth tokens: {e}")
            return False
    
    def logout(self):
        """Logout current user and clear session state."""
        try:
            self.session_state.authenticated = False
            self.session_state.user_id = None
            self.session_state.user_email = None
            self.session_state.oauth_tokens = None
            self.session_state.last_auth_check = None
            
            logger.info("User logged out successfully")
            
        except Exception as e:
            logger.error(f"Failed to logout user: {e}")
    
    def require_auth(self, func):
        """Decorator to require authentication for functions."""
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                st.error("Please authenticate to access this feature.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    
    async def check_permissions(self, user_id: str, required_permission: str) -> bool:
        """Check if user has required permission."""
        try:
            user = await db_manager.get_user(user_id)
            if not user:
                return False
            
            # Basic permission system - can be extended
            if required_permission == 'basic_access':
                return user.is_active
            elif required_permission == 'premium_features':
                return user.is_active and user.subscription_tier in ['premium', 'enterprise']
            elif required_permission == 'admin_access':
                return user.is_active and user.role == 'admin'
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check permissions for user {user_id}: {e}")
            return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status and user info."""
        return {
            'authenticated': self.is_authenticated(),
            'user_id': self.get_current_user_id(),
            'user_email': self.get_current_user_email(),
            'last_auth_check': self.session_state.last_auth_check,
            'has_valid_tokens': bool(self.get_oauth_tokens())
        }

# Global auth manager instance
auth_manager = AuthManager()

# Convenience functions for easy access
def get_current_user() -> Optional[User]:
    """Get current authenticated user object."""
    user_id = auth_manager.get_current_user_id()
    if user_id:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we need to handle this differently
                return None  # This will be handled by the calling async function
            else:
                return loop.run_until_complete(db_manager.get_user(user_id))
        except RuntimeError:
            # No event loop, return None
            return None
    return None

def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return auth_manager.is_authenticated()

def require_auth(func):
    """Decorator to require authentication."""
    return auth_manager.require_auth(func)

# Export for easy access
__all__ = [
    'auth_manager', 'AuthManager', 'OAuthTokens', 'get_current_user',
    'is_authenticated', 'require_auth'
]
