"""
Configuration and Constants Management

This module provides centralized configuration management for the AI Sales Assistant platform.
It handles environment variables, API configurations, AI model parameters, and system constants.

Dependencies: os, logging, typing
Used by: ALL other modules
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.info("Successfully loaded .env file")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("python-dotenv not installed. Make sure environment variables are set manually.")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to load .env file: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_sales_assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """API configuration settings for external services."""
    # Required fields (no defaults)
    gemini_api_key: str
    gmail_client_id: str
    gmail_client_secret: str
    gmail_redirect_uri: str
    sheets_client_id: str
    sheets_client_secret: str
    sheets_redirect_uri: str
    calendly_api_key: str
    firebase_project_id: str
    firebase_private_key_id: str
    firebase_private_key: str
    firebase_client_email: str
    firebase_client_id: str
    
    # Optional fields (with defaults)
    gemini_model: str = "gemini-2.5-flash-lite" # Higher limits, better performance
    gemini_max_tokens: int = 2048
    gemini_temperature: float = 0.7
    calendly_base_url: str = "https://api.calendly.com"

@dataclass
class EmailConfig:
    """Email generation and sending configuration."""
    max_emails_per_day: int = 100
    follow_up_delay_hours: int = 48
    max_follow_ups: int = 3
    business_hours_start: int = 9
    business_hours_end: int = 17
    timezone: str = "UTC"
    
    # AI prompt templates
    cold_email_prompt: str = """
    Generate a personalized cold email for {lead_name} who works as {job_title} at {company}.
    Company description: {company_description}
    Pain points to address: {pain_points}
    
    Requirements:
    - Maximum 150 words
    - Professional but conversational tone
    - Include specific value proposition
    - End with clear call-to-action
    - No generic templates
    """
    
    follow_up_prompt: str = """
    Generate a follow-up email for {lead_name} based on previous interaction: {previous_context}
    Original email: {original_email}
    
    Requirements:
    - Maximum 100 words
    - Reference previous communication
    - Provide additional value
    - Gentle reminder of next steps
    """

@dataclass
class AutomationConfig:
    """Automation workflow configuration."""
    batch_size: int = 50
    processing_interval_minutes: int = 15
    max_concurrent_campaigns: int = 10
    lead_score_threshold: float = 0.7
    engagement_timeout_hours: int = 168  # 1 week
    
    # Campaign settings
    min_emails_between_followups: int = 2
    max_campaign_duration_days: int = 30
    auto_pause_on_low_engagement: bool = True
    engagement_threshold: float = 0.1

@dataclass
class DatabaseConfig:
    """Database and storage configuration."""
    firestore_collections: Dict[str, str] = None
    batch_write_size: int = 500
    cache_ttl_seconds: int = 3600
    max_query_results: int = 1000
    
    def __post_init__(self):
        if self.firestore_collections is None:
            self.firestore_collections = {
                'users': 'users',
                'leads': 'leads',
                'campaigns': 'campaigns',
                'emails': 'emails',
                'analytics': 'analytics'
            }

class Config:
    """Main configuration class that manages all settings."""
    
    def __init__(self):
        self._load_environment_variables()
        self._validate_configuration()
        self._setup_logging()
    
    def _load_environment_variables(self):
        """Load configuration from environment variables."""
        try:
            # Debug: Print environment variables being loaded
            logger.info("Loading environment variables...")
            logger.debug(f"GEMINI_API_KEY: {'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
            logger.debug(f"GMAIL_CLIENT_ID: {'SET' if os.getenv('GMAIL_CLIENT_ID') else 'NOT SET'}")
            logger.debug(f"SHEETS_CLIENT_ID: {'SET' if os.getenv('SHEETS_CLIENT_ID') else 'NOT SET'}")
            logger.debug(f"CALENDLY_API_KEY: {'SET' if os.getenv('CALENDLY_API_KEY') else 'NOT SET'}")
            logger.debug(f"FIREBASE_PROJECT_ID: {'SET' if os.getenv('FIREBASE_PROJECT_ID') else 'NOT SET'}")
            
            # API Configuration
            self.api = APIConfig(
                gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
                gmail_client_id=os.getenv('GMAIL_CLIENT_ID', ''),
                gmail_client_secret=os.getenv('GMAIL_CLIENT_SECRET', ''),
                gmail_redirect_uri=os.getenv('GMAIL_REDIRECT_URI', ''),
                sheets_client_id=os.getenv('SHEETS_CLIENT_ID', ''),
                sheets_client_secret=os.getenv('SHEETS_CLIENT_SECRET', ''),
                sheets_redirect_uri=os.getenv('SHEETS_REDIRECT_URI', ''),
                calendly_api_key=os.getenv('CALENDLY_API_KEY', ''),
                firebase_project_id=os.getenv('FIREBASE_PROJECT_ID', ''),
                firebase_private_key_id=os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
                firebase_private_key=os.getenv('FIREBASE_PRIVATE_KEY', ''),
                firebase_client_email=os.getenv('FIREBASE_CLIENT_EMAIL', ''),
                firebase_client_id=os.getenv('FIREBASE_CLIENT_ID', '')
            )
            
            # Email Configuration
            self.email = EmailConfig(
                max_emails_per_day=int(os.getenv('MAX_EMAILS_PER_DAY', '100')),
                follow_up_delay_hours=int(os.getenv('FOLLOW_UP_DELAY_HOURS', '48')),
                max_follow_ups=int(os.getenv('MAX_FOLLOW_UPS', '3')),
                business_hours_start=int(os.getenv('BUSINESS_HOURS_START', '9')),
                business_hours_end=int(os.getenv('BUSINESS_HOURS_END', '17')),
                timezone=os.getenv('TIMEZONE', 'UTC')
            )
            
            # Automation Configuration
            self.automation = AutomationConfig(
                batch_size=int(os.getenv('BATCH_SIZE', '50')),
                processing_interval_minutes=int(os.getenv('PROCESSING_INTERVAL_MINUTES', '15')),
                max_concurrent_campaigns=int(os.getenv('MAX_CONCURRENT_CAMPAIGNS', '10')),
                lead_score_threshold=float(os.getenv('LEAD_SCORE_THRESHOLD', '0.7')),
                engagement_timeout_hours=int(os.getenv('ENGAGEMENT_TIMEOUT_HOURS', '168'))
            )
            
            # Database Configuration
            self.database = DatabaseConfig(
                batch_write_size=int(os.getenv('BATCH_WRITE_SIZE', '500')),
                cache_ttl_seconds=int(os.getenv('CACHE_TTL_SECONDS', '3600')),
                max_query_results=int(os.getenv('MAX_QUERY_RESULTS', '1000'))
            )
            
            # System Configuration
            self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
            self.environment = os.getenv('ENVIRONMENT', 'production')
            self.log_level = os.getenv('LOG_LEVEL', 'INFO')
            
        except Exception as e:
            logger.error(f"Failed to load environment variables: {e}")
            raise
    
    def _validate_configuration(self):
        """Validate that all required configuration is present."""
        required_fields = [
            'gemini_api_key', 'gmail_client_id', 'gmail_client_secret',
            'sheets_client_id', 'sheets_client_secret', 'calendly_api_key',
            'firebase_project_id', 'firebase_private_key_id', 'firebase_private_key',
            'firebase_client_email', 'firebase_client_id'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self.api, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Missing required configuration fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation completed successfully")
    
    def _setup_logging(self):
        """Configure logging based on environment."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration."""
        return self.api
    
    def get_email_config(self) -> EmailConfig:
        """Get email configuration."""
        return self.email
    
    def get_automation_config(self) -> AutomationConfig:
        """Get automation configuration."""
        return self.automation
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return self.database
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == 'production'
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self.debug
    
    def debug_environment_variables(self) -> Dict[str, str]:
        """Debug method to check which environment variables are loaded."""
        return {
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', 'NOT SET'),
            'GMAIL_CLIENT_ID': os.getenv('GMAIL_CLIENT_ID', 'NOT SET'),
            'GMAIL_CLIENT_SECRET': os.getenv('GMAIL_CLIENT_SECRET', 'NOT SET'),
            'SHEETS_CLIENT_ID': os.getenv('SHEETS_CLIENT_ID', 'NOT SET'),
            'SHEETS_CLIENT_SECRET': os.getenv('SHEETS_CLIENT_SECRET', 'NOT SET'),
            'CALENDLY_API_KEY': os.getenv('CALENDLY_API_KEY', 'NOT SET'),
            'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID', 'NOT SET'),
            'FIREBASE_PRIVATE_KEY_ID': os.getenv('FIREBASE_PRIVATE_KEY_ID', 'NOT SET'),
            'FIREBASE_CLIENT_EMAIL': os.getenv('FIREBASE_CLIENT_EMAIL', 'NOT SET'),
            'FIREBASE_CLIENT_ID': os.getenv('FIREBASE_CLIENT_ID', 'NOT SET'),
            'ENV_FILE_PATH': os.path.abspath('.env') if os.path.exists('.env') else 'NOT FOUND'
        }

# Global configuration instance
config = Config()

# Export configuration for easy access
__all__ = ['config', 'Config', 'APIConfig', 'EmailConfig', 'AutomationConfig', 'DatabaseConfig']
