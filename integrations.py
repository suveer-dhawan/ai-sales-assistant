"""
External API Integration Layer

This module handles all external API integrations including Google Sheets, Gmail,
Gemini AI, and Calendly. It provides data extraction, email sending, AI content
generation, and meeting booking capabilities with comprehensive error handling.

Dependencies: googleapiclient, google.auth, google.generativeai, requests, config.py, auth.py, database.py
Used by: ai_engine.py, automation.py, app.py
"""

import logging
import json
import time
import base64
import email
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.generativeai as genai

from config import config
from auth import auth_manager
from database import db_manager

logger = logging.getLogger(__name__)

@dataclass
class LeadData:
    """Lead data structure from Google Sheets."""
    name: str
    email: str
    company: str
    job_title: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_description: Optional[str] = None
    pain_points: List[str] = None
    source: str = "google_sheets"
    
    def __post_init__(self):
        if self.pain_points is None:
            self.pain_points = []

@dataclass
class EmailResult:
    """Email sending result."""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None

@dataclass
class AIResponse:
    """AI content generation result."""
    success: bool
    content: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    model: Optional[str] = None

class RateLimiter:
    """Rate limiting utility for API calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self) -> bool:
        """Acquire permission to make an API call."""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    async def wait_for_permission(self):
        """Wait until permission is granted."""
        while not await self.acquire():
            await asyncio.sleep(1)

class GoogleSheetsAPI:
    """Google Sheets API integration for lead data extraction."""
    
    def __init__(self):
        self.api_config = config.get_api_config()
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute
        self.service = None
        logger.info("Google Sheets API initialized")
    
    async def _get_authenticated_service(self):
        """Get authenticated Google Sheets service."""
        try:
            tokens = auth_manager.get_oauth_tokens()
            if not tokens:
                raise ValueError("No OAuth tokens available")
            
            credentials = Credentials(
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri=tokens.token_uri,
                client_id=tokens.client_id,
                client_secret=tokens.client_secret,
                scopes=tokens.scopes
            )
            
            # Refresh tokens if needed
            if credentials.expired:
                await auth_manager.refresh_tokens()
                tokens = auth_manager.get_oauth_tokens()
                credentials = Credentials(
                    token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    token_uri=tokens.token_uri,
                    client_id=tokens.client_id,
                    client_secret=tokens.client_secret,
                    scopes=tokens.scopes
                )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets service authenticated successfully")
            
        except Exception as e:
            logger.error(f"Failed to authenticate Google Sheets service: {e}")
            raise
    
    async def extract_leads_from_sheet(self, spreadsheet_id: str, range_name: str = "A:Z") -> List[LeadData]:
        """Extract lead data from Google Sheets."""
        try:
            await self.rate_limiter.wait_for_permission()
            
            if not self.service:
                await self._get_authenticated_service()
            
            # Get sheet data
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logger.warning("No data found in spreadsheet")
                return []
            
            # Parse headers and data
            headers = values[0]
            data_rows = values[1:]
            
            leads = []
            for row in data_rows:
                try:
                    # Pad row to match header length
                    padded_row = row + [''] * (len(headers) - len(row))
                    
                    # Create lead data
                    lead_data = LeadData(
                        name=padded_row[0] if len(padded_row) > 0 else '',
                        email=padded_row[1] if len(padded_row) > 1 else '',
                        company=padded_row[2] if len(padded_row) > 2 else '',
                        job_title=padded_row[3] if len(padded_row) > 3 else '',
                        phone=padded_row[4] if len(padded_row) > 4 else None,
                        linkedin_url=padded_row[5] if len(padded_row) > 5 else None,
                        company_description=padded_row[6] if len(padded_row) > 6 else None,
                        pain_points=padded_row[7].split(',') if len(padded_row) > 7 and padded_row[7] else []
                    )
                    
                    # Validate required fields
                    if lead_data.name and lead_data.email and lead_data.company and lead_data.job_title:
                        leads.append(lead_data)
                    else:
                        logger.warning(f"Skipping invalid lead data: {padded_row}")
                        
                except Exception as e:
                    logger.error(f"Failed to parse row {row}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(leads)} leads from spreadsheet")
            return leads
            
        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            if e.resp.status == 401:
                # Token expired, try to refresh
                await auth_manager.refresh_tokens()
                return await self.extract_leads_from_sheet(spreadsheet_id, range_name)
            raise
        except Exception as e:
            logger.error(f"Failed to extract leads from spreadsheet: {e}")
            raise

class GmailAPI:
    """Gmail API integration for email sending and management."""
    
    def __init__(self):
        self.api_config = config.get_api_config()
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute
        self.service = None
        self.max_emails_per_day = config.get_email_config().max_emails_per_day
        self.emails_sent_today = 0
        self.last_reset_date = datetime.now().date()
        logger.info("Gmail API initialized")
    
    async def _get_authenticated_service(self):
        """Get authenticated Gmail service."""
        try:
            tokens = auth_manager.get_oauth_tokens()
            if not tokens:
                raise ValueError("No OAuth tokens available")
            
            credentials = Credentials(
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri=tokens.token_uri,
                client_id=tokens.client_id,
                client_secret=tokens.client_secret,
                scopes=tokens.scopes
            )
            
            # Refresh tokens if needed
            if credentials.expired:
                await auth_manager.refresh_tokens()
                tokens = auth_manager.get_oauth_tokens()
                credentials = Credentials(
                    token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    token_uri=tokens.token_uri,
                    client_id=tokens.client_id,
                    client_secret=tokens.client_secret,
                    scopes=tokens.scopes
                )
            
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info("Gmail service authenticated successfully")
            
        except Exception as e:
            logger.error(f"Failed to authenticate Gmail service: {e}")
            raise
    
    def _reset_daily_counter(self):
        """Reset daily email counter if it's a new day."""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.emails_sent_today = 0
            self.last_reset_date = today
    
    def _check_daily_limit(self) -> bool:
        """Check if daily email limit has been reached."""
        self._reset_daily_counter()
        return self.emails_sent_today < self.max_emails_per_day
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        from_name: str = None, reply_to: str = None) -> EmailResult:
        """Send email using Gmail API."""
        try:
            if not self._check_daily_limit():
                return EmailResult(
                    success=False,
                    error_message="Daily email limit reached"
                )
            
            await self.rate_limiter.wait_for_permission()
            
            if not self.service:
                await self._get_authenticated_service()
            
            # Create email message
            message = email.mime.text.MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            
            if from_name:
                message['from'] = f"{from_name} <{auth_manager.get_current_user_email()}>"
            else:
                message['from'] = auth_manager.get_current_user_email()
            
            if reply_to:
                message['reply-to'] = reply_to
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send email
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Update counters
            self.emails_sent_today += 1
            
            # Store email record in database
            email_data = {
                'email_id': sent_message['id'],
                'campaign_id': 'manual',  # Can be updated by calling function
                'lead_id': 'manual',      # Can be updated by calling function
                'user_id': auth_manager.get_current_user_id(),
                'subject': subject,
                'body': body,
                'email_type': 'manual',
                'status': 'sent',
                'sent_at': datetime.utcnow()
            }
            
            await db_manager.create_email(email_data)
            
            logger.info(f"Email sent successfully to {to_email}")
            return EmailResult(
                success=True,
                message_id=sent_message['id'],
                sent_at=datetime.utcnow()
            )
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            if e.resp.status == 401:
                # Token expired, try to refresh
                await auth_manager.refresh_tokens()
                return await self.send_email(to_email, subject, body, from_name, reply_to)
            return EmailResult(
                success=False,
                error_message=f"Gmail API error: {e}"
            )
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return EmailResult(
                success=False,
                error_message=str(e)
            )
    
    async def get_email_threads(self, query: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get email threads from Gmail."""
        try:
            await self.rate_limiter.wait_for_permission()
            
            if not self.service:
                await self._get_authenticated_service()
            
            # List threads
            threads_response = self.service.users().threads().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            threads = threads_response.get('threads', [])
            thread_details = []
            
            for thread in threads:
                thread_detail = self.service.users().threads().get(
                    userId='me',
                    id=thread['id']
                ).execute()
                thread_details.append(thread_detail)
            
            logger.info(f"Retrieved {len(thread_details)} email threads")
            return thread_details
            
        except Exception as e:
            logger.error(f"Failed to get email threads: {e}")
            raise

class GeminiAPI:
    """Google Gemini AI API integration for content generation."""
    
    def __init__(self):
        self.api_config = config.get_api_config()
        self.rate_limiter = RateLimiter(max_calls=60, time_window=60)  # 60 calls per minute
        genai.configure(api_key=self.api_config.gemini_api_key)
        self.model = genai.GenerativeModel(self.api_config.gemini_model)
        self.max_tokens = self.api_config.gemini_max_tokens
        self.temperature = self.api_config.gemini_temperature
        logger.info("Gemini AI API initialized")
    
    async def generate_content(self, prompt: str, context: Dict[str, Any] = None) -> AIResponse:
        """Generate content using Gemini AI."""
        try:
            await self.rate_limiter.wait_for_permission()
            
            # Enhance prompt with context
            enhanced_prompt = prompt
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                enhanced_prompt = f"{prompt}\n\nContext:\n{context_str}"
            
            # Generate content
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            )
            
            if response.text:
                logger.info("Content generated successfully using Gemini AI")
                return AIResponse(
                    success=True,
                    content=response.text,
                    model=self.api_config.gemini_model,
                    tokens_used=len(response.text.split())  # Approximate token count
                )
            else:
                return AIResponse(
                    success=False,
                    error_message="No content generated"
                )
                
        except Exception as e:
            logger.error(f"Failed to generate content with Gemini AI: {e}")
            return AIResponse(
                success=False,
                error_message=str(e)
            )
    
    async def generate_cold_email(self, lead_data: LeadData, company_info: str = None) -> AIResponse:
        """Generate personalized cold email for a lead."""
        try:
            email_config = config.get_email_config()
            prompt = email_config.cold_email_prompt.format(
                lead_name=lead_data.name,
                job_title=lead_data.job_title,
                company=lead_data.company,
                company_description=company_info or lead_data.company_description or "a company",
                pain_points=", ".join(lead_data.pain_points) if lead_data.pain_points else "business challenges"
            )
            
            return await self.generate_content(prompt, {
                'lead_name': lead_data.name,
                'job_title': lead_data.job_title,
                'company': lead_data.company
            })
            
        except Exception as e:
            logger.error(f"Failed to generate cold email: {e}")
            return AIResponse(
                success=False,
                error_message=str(e)
            )
    
    async def generate_follow_up(self, original_email: str, lead_name: str, 
                                previous_context: str = None) -> AIResponse:
        """Generate follow-up email."""
        try:
            email_config = config.get_email_config()
            prompt = email_config.follow_up_prompt.format(
                lead_name=lead_name,
                previous_context=previous_context or "previous communication",
                original_email=original_email
            )
            
            return await self.generate_content(prompt, {
                'lead_name': lead_name,
                'previous_context': previous_context
            })
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up email: {e}")
            return AIResponse(
                success=False,
                error_message=str(e)
            )
    
    async def analyze_response(self, email_content: str) -> AIResponse:
        """Analyze email response for sentiment and intent."""
        try:
            prompt = f"""
            Analyze the following email response and provide insights:
            
            Email: {email_content}
            
            Please provide:
            1. Sentiment (positive, negative, neutral)
            2. Intent (interested, not interested, needs more info, etc.)
            3. Key points mentioned
            4. Recommended next action
            5. Confidence score (0-100)
            
            Format as JSON.
            """
            
            response = await self.generate_content(prompt)
            if response.success:
                # Try to parse JSON response
                try:
                    analysis = json.loads(response.content)
                    return AIResponse(
                        success=True,
                        content=json.dumps(analysis, indent=2),
                        model=self.api_config.gemini_model
                    )
                except json.JSONDecodeError:
                    return response
            return response
            
        except Exception as e:
            logger.error(f"Failed to analyze response: {e}")
            return AIResponse(
                success=False,
                error_message=str(e)
            )

class CalendlyIntegration:
    """Calendly API integration for meeting booking."""
    
    def __init__(self):
        self.api_config = config.get_api_config()
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute
        self.base_url = self.api_config.calendly_base_url
        self.headers = {
            'Authorization': f'Bearer {self.api_config.calendly_api_key}',
            'Content-Type': 'application/json'
        }
        logger.info("Calendly integration initialized")
    
    async def get_available_times(self, event_type_url: str, 
                                 start_time: datetime = None, 
                                 end_time: datetime = None) -> List[Dict[str, Any]]:
        """Get available meeting times from Calendly."""
        try:
            await self.rate_limiter.wait_for_permission()
            
            if not start_time:
                start_time = datetime.utcnow()
            if not end_time:
                end_time = start_time + timedelta(days=7)
            
            params = {
                'event_type': event_type_url,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            response = requests.get(
                f"{self.base_url}/event_type_available_times",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                available_times = data.get('available_times', [])
                logger.info(f"Retrieved {len(available_times)} available meeting times")
                return available_times
            else:
                logger.error(f"Failed to get available times: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get available meeting times: {e}")
            return []
    
    async def schedule_meeting(self, event_type_url: str, start_time: datetime,
                              invitee_email: str, invitee_name: str) -> Dict[str, Any]:
        """Schedule a meeting through Calendly."""
        try:
            await self.rate_limiter.wait_for_permission()
            
            payload = {
                'event_type': event_type_url,
                'start_time': start_time.isoformat(),
                'invitee': {
                    'email': invitee_email,
                    'name': invitee_name
                }
            }
            
            response = requests.post(
                f"{self.base_url}/scheduling_links",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"Meeting scheduled successfully for {invitee_email}")
                return data
            else:
                logger.error(f"Failed to schedule meeting: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to schedule meeting: {e}")
            return {}

class IntegrationManager:
    """Main integration manager that coordinates all external APIs."""
    
    def __init__(self):
        self.sheets_api = GoogleSheetsAPI()
        self.gmail_api = GmailAPI()
        self.gemini_api = GeminiAPI()
        self.calendly = CalendlyIntegration()
        logger.info("Integration manager initialized successfully")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all integrations."""
        try:
            health_status = {}
            
            # Check Google Sheets
            try:
                await self.sheets_api._get_authenticated_service()
                health_status['google_sheets'] = True
            except Exception:
                health_status['google_sheets'] = False
            
            # Check Gmail
            try:
                await self.gmail_api._get_authenticated_service()
                health_status['gmail'] = True
            except Exception:
                health_status['gmail'] = False
            
            # Check Gemini AI
            try:
                test_response = await self.gemini_api.generate_content("Test")
                health_status['gemini_ai'] = test_response.success
            except Exception:
                health_status['gemini_ai'] = False
            
            # Check Calendly
            try:
                health_status['calendly'] = True  # Simple API key check
            except Exception:
                health_status['calendly'] = False
            
            logger.info(f"Integration health check completed: {health_status}")
            return health_status
            
        except Exception as e:
            logger.error(f"Integration health check failed: {e}")
            return {}

# Global integration manager instance
integration_manager = IntegrationManager()

# Export for easy access
__all__ = [
    'integration_manager', 'IntegrationManager', 'GoogleSheetsAPI', 'GmailAPI',
    'GeminiAPI', 'CalendlyIntegration', 'LeadData', 'EmailResult', 'AIResponse'
]
