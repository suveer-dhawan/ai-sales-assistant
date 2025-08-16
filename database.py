"""
Data Persistence Layer

This module handles all database operations using Firebase Firestore.
It provides CRUD operations for users, leads, campaigns, emails, and analytics data.
Includes schema validation, batch operations, and comprehensive error handling.

Dependencies: firebase_admin, google.cloud.firestore, config.py, auth.py
Used by: integrations.py, ai_engine.py, automation.py, app.py
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from google.cloud import firestore
from google.cloud.firestore import DocumentReference, CollectionReference
import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

from config import config
from auth import get_current_user

logger = logging.getLogger(__name__)

@dataclass
class User:
    """User data model."""
    user_id: str
    email: str
    name: str
    company: str
    role: str
    created_at: datetime
    last_login: datetime
    settings: Dict[str, Any]
    subscription_tier: str = "basic"
    is_active: bool = True

@dataclass
class Lead:
    """Lead data model."""
    lead_id: str
    user_id: str
    name: str
    email: str
    company: str
    job_title: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_description: Optional[str] = None
    pain_points: List[str] = None
    lead_score: float = 0.0
    status: str = "new"  # new, contacted, responded, qualified, booked, lost
    created_at: datetime = None
    last_contacted: Optional[datetime] = None
    campaign_id: Optional[str] = None
    engagement_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.pain_points is None:
            self.pain_points = []
        if self.engagement_metrics is None:
            self.engagement_metrics = {}

@dataclass
class Campaign:
    """Campaign data model."""
    campaign_id: str
    user_id: str
    name: str
    description: str
    status: str  # draft, active, paused, completed, archived
    created_at: datetime
    updated_at: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    target_leads: int = 0
    sent_emails: int = 0
    responses: int = 0
    meetings_booked: int = 0
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}

@dataclass
class Email:
    """Email data model."""
    email_id: str
    campaign_id: str
    lead_id: str
    user_id: str
    subject: str
    body: str
    email_type: str  # cold_email, follow_up, response
    status: str  # draft, sent, delivered, opened, clicked, replied, bounced
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    bounce_reason: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DatabaseManager:
    """Manages all database operations with Firebase Firestore."""
    
    def __init__(self):
        self._initialize_firebase()
        self.db = firestore.client()
        self.batch_size = config.get_database_config().batch_write_size
        self.collections = config.get_database_config().firestore_collections
        logger.info("Database manager initialized successfully")
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            api_config = config.get_api_config()
            cred_dict = {
                "type": "service_account",
                "project_id": api_config.firebase_project_id,
                "private_key_id": api_config.firebase_private_key_id,
                "private_key": api_config.firebase_private_key.replace('\\n', '\n'),
                "client_email": api_config.firebase_client_email,
                "client_id": api_config.firebase_client_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{api_config.firebase_client_email}"
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def _get_collection(self, collection_name: str) -> CollectionReference:
        """Get Firestore collection reference."""
        return self.db.collection(self.collections[collection_name])
    
    def _validate_document(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate document data against required fields."""
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
        return True
    
    def _serialize_datetime(self, obj: Any) -> Any:
        """Serialize datetime objects for Firestore storage."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        return obj
    
    def _deserialize_datetime(self, obj: Any) -> Any:
        """Deserialize datetime objects from Firestore storage."""
        if isinstance(obj, str) and 'T' in obj and 'Z' in obj:
            try:
                return datetime.fromisoformat(obj.replace('Z', '+00:00'))
            except ValueError:
                return obj
        elif isinstance(obj, dict):
            return {k: self._deserialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_datetime(item) for item in obj]
        return obj
    
    # User Operations
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user."""
        try:
            required_fields = ['user_id', 'email', 'name', 'company', 'role']
            if not self._validate_document(user_data, required_fields):
                raise ValueError("Missing required user fields")
            
            user_data['created_at'] = datetime.utcnow()
            user_data['last_login'] = datetime.utcnow()
            user_data['is_active'] = True
            
            serialized_data = self._serialize_datetime(user_data)
            doc_ref = self._get_collection('users').document(user_data['user_id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"User created successfully: {user_data['user_id']}")
            return user_data['user_id']
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            doc = self._get_collection('users').document(user_id).get()
            if doc.exists:
                data = self._deserialize_datetime(doc.to_dict())
                return User(**data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data."""
        try:
            updates['updated_at'] = datetime.utcnow()
            serialized_updates = self._serialize_datetime(updates)
            
            doc_ref = self._get_collection('users').document(user_id)
            doc_ref.update(serialized_updates)
            
            logger.info(f"User updated successfully: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    # Lead Operations
    async def create_lead(self, lead_data: Dict[str, Any]) -> str:
        """Create a new lead."""
        try:
            required_fields = ['lead_id', 'user_id', 'name', 'email', 'company', 'job_title']
            if not self._validate_document(lead_data, required_fields):
                raise ValueError("Missing required lead fields")
            
            lead_data['created_at'] = datetime.utcnow()
            lead_data['status'] = 'new'
            lead_data['lead_score'] = 0.0
            
            serialized_data = self._serialize_datetime(lead_data)
            doc_ref = self._get_collection('leads').document(lead_data['lead_id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Lead created successfully: {lead_data['lead_id']}")
            return lead_data['lead_id']
            
        except Exception as e:
            logger.error(f"Failed to create lead: {e}")
            raise
    
    async def get_leads_by_user(self, user_id: str, status: Optional[str] = None, limit: int = 100) -> List[Lead]:
        """Get leads for a specific user."""
        try:
            query = self._get_collection('leads').where('user_id', '==', user_id)
            if status:
                query = query.where('status', '==', status)
            
            query = query.limit(limit)
            docs = query.stream()
            
            leads = []
            for doc in docs:
                data = self._deserialize_datetime(doc.to_dict())
                leads.append(Lead(**data))
            
            logger.info(f"Retrieved {len(leads)} leads for user {user_id}")
            return leads
            
        except Exception as e:
            logger.error(f"Failed to get leads for user {user_id}: {e}")
            raise
    
    async def update_lead_status(self, lead_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update lead status and metadata."""
        try:
            updates = {'status': status, 'updated_at': datetime.utcnow()}
            if metadata:
                updates['engagement_metrics'] = metadata
            
            serialized_updates = self._serialize_datetime(updates)
            doc_ref = self._get_collection('leads').document(lead_id)
            doc_ref.update(serialized_updates)
            
            logger.info(f"Lead {lead_id} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update lead {lead_id} status: {e}")
            raise
    
    async def bulk_create_leads(self, leads_data: List[Dict[str, Any]]) -> List[str]:
        """Create multiple leads in batch."""
        try:
            if len(leads_data) > self.batch_size:
                raise ValueError(f"Batch size {len(leads_data)} exceeds limit {self.batch_size}")
            
            batch = self.db.batch()
            lead_ids = []
            
            for lead_data in leads_data:
                lead_id = f"lead_{int(time.time() * 1000)}_{len(lead_ids)}"
                lead_data['lead_id'] = lead_id
                lead_data['created_at'] = datetime.utcnow()
                lead_data['status'] = 'new'
                lead_data['lead_score'] = 0.0
                
                serialized_data = self._serialize_datetime(lead_data)
                doc_ref = self._get_collection('leads').document(lead_id)
                batch.set(doc_ref, serialized_data)
                lead_ids.append(lead_id)
            
            batch.commit()
            logger.info(f"Bulk created {len(lead_ids)} leads successfully")
            return lead_ids
            
        except Exception as e:
            logger.error(f"Failed to bulk create leads: {e}")
            raise
    
    # Campaign Operations
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new campaign."""
        try:
            required_fields = ['campaign_id', 'user_id', 'name', 'description']
            if not self._validate_document(campaign_data, required_fields):
                raise ValueError("Missing required campaign fields")
            
            campaign_data['created_at'] = datetime.utcnow()
            campaign_data['updated_at'] = datetime.utcnow()
            campaign_data['status'] = 'draft'
            campaign_data['sent_emails'] = 0
            campaign_data['responses'] = 0
            campaign_data['meetings_booked'] = 0
            
            serialized_data = self._serialize_datetime(campaign_data)
            doc_ref = self._get_collection('campaigns').document(campaign_data['campaign_id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Campaign created successfully: {campaign_data['campaign_id']}")
            return campaign_data['campaign_id']
            
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            raise
    
    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        try:
            doc = self._get_collection('campaigns').document(campaign_id).get()
            if doc.exists:
                data = self._deserialize_datetime(doc.to_dict())
                return Campaign(**data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get campaign {campaign_id}: {e}")
            raise
    
    async def update_campaign_metrics(self, campaign_id: str, metrics: Dict[str, Any]) -> bool:
        """Update campaign performance metrics."""
        try:
            metrics['updated_at'] = datetime.utcnow()
            serialized_metrics = self._serialize_datetime(metrics)
            
            doc_ref = self._get_collection('campaigns').document(campaign_id)
            doc_ref.update(serialized_metrics)
            
            logger.info(f"Campaign {campaign_id} metrics updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update campaign {campaign_id} metrics: {e}")
            raise
    
    # Email Operations
    async def create_email(self, email_data: Dict[str, Any]) -> str:
        """Create a new email record."""
        try:
            required_fields = ['email_id', 'campaign_id', 'lead_id', 'user_id', 'subject', 'body', 'email_type']
            if not self._validate_document(email_data, required_fields):
                raise ValueError("Missing required email fields")
            
            email_data['status'] = 'draft'
            email_data['metadata'] = email_data.get('metadata', {})
            
            serialized_data = self._serialize_datetime(email_data)
            doc_ref = self._get_collection('emails').document(email_data['email_id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Email created successfully: {email_data['email_id']}")
            return email_data['email_id']
            
        except Exception as e:
            logger.error(f"Failed to create email: {e}")
            raise
    
    async def update_email_status(self, email_id: str, status: str, timestamp_field: Optional[str] = None) -> bool:
        """Update email status and timestamp."""
        try:
            updates = {'status': status, 'updated_at': datetime.utcnow()}
            
            if timestamp_field and hasattr(datetime, timestamp_field):
                updates[timestamp_field] = datetime.utcnow()
            
            serialized_updates = self._serialize_datetime(updates)
            doc_ref = self._get_collection('emails').document(email_id)
            doc_ref.update(serialized_updates)
            
            logger.info(f"Email {email_id} status updated to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update email {email_id} status: {e}")
            raise
    
    # Analytics Operations
    async def store_analytics(self, analytics_data: Dict[str, Any]) -> str:
        """Store analytics data."""
        try:
            analytics_data['timestamp'] = datetime.utcnow()
            analytics_data['analytics_id'] = f"analytics_{int(time.time() * 1000)}"
            
            serialized_data = self._serialize_datetime(analytics_data)
            doc_ref = self._get_collection('analytics').document(analytics_data['analytics_id'])
            doc_ref.set(serialized_data)
            
            logger.info(f"Analytics stored successfully: {analytics_data['analytics_id']}")
            return analytics_data['analytics_id']
            
        except Exception as e:
            logger.error(f"Failed to store analytics: {e}")
            raise
    
    async def get_user_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get analytics data for a user within a date range."""
        try:
            query = self._get_collection('analytics').where('user_id', '==', user_id)
            query = query.where('timestamp', '>=', start_date)
            query = query.where('timestamp', '<=', end_date)
            
            docs = query.stream()
            analytics = []
            
            for doc in docs:
                data = self._deserialize_datetime(doc.to_dict())
                analytics.append(data)
            
            logger.info(f"Retrieved {len(analytics)} analytics records for user {user_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics for user {user_id}: {e}")
            raise
    
    # Utility Methods
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            # Try to access a collection to verify connectivity
            self._get_collection('users').limit(1).stream()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def cleanup_old_data(self, days_old: int = 90) -> int:
        """Clean up old analytics and email data."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = 0
            
            # Clean up old analytics
            analytics_query = self._get_collection('analytics').where('timestamp', '<', cutoff_date)
            analytics_docs = analytics_query.stream()
            
            batch = self.db.batch()
            for doc in analytics_docs:
                batch.delete(doc.reference)
                deleted_count += 1
            
            if deleted_count > 0:
                batch.commit()
                logger.info(f"Cleaned up {deleted_count} old records")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

# Export for easy access
__all__ = ['db_manager', 'DatabaseManager', 'User', 'Lead', 'Campaign', 'Email']
