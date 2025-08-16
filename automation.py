"""
Workflow Orchestration Layer

This module handles email sequence management, intelligent scheduling,
campaign orchestration, and automated follow-up workflows.
It coordinates between AI generation, email sending, and response monitoring.

Dependencies: asyncio, datetime, config.py, ai_engine.py, integrations.py, database.py
Used by: app.py
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from config import config
from ai_engine import ai_engine
from integrations import integration_manager
from database import db_manager, Lead, Campaign, Email

logger = logging.getLogger(__name__)

@dataclass
class EmailSequence:
    """Email sequence configuration."""
    sequence_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    conditions: Dict[str, Any]
    max_duration_days: int
    is_active: bool = True

@dataclass
class CampaignJob:
    """Campaign execution job."""
    job_id: str
    campaign_id: str
    user_id: str
    status: str  # pending, running, completed, failed, paused
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any] = None
    error_message: Optional[str] = None

class CampaignOrchestrator:
    """Orchestrates campaign execution and automation."""
    
    def __init__(self):
        self.automation_config = config.get_automation_config()
        self.email_config = config.get_email_config()
        self.active_jobs: Dict[str, CampaignJob] = {}
        self.job_queue = asyncio.Queue()
        self.is_running = False
        logger.info("Campaign orchestrator initialized")
    
    async def start(self):
        """Start the campaign orchestrator."""
        try:
            self.is_running = True
            asyncio.create_task(self._process_job_queue())
            asyncio.create_task(self._monitor_active_jobs())
            logger.info("Campaign orchestrator started")
        except Exception as e:
            logger.error(f"Failed to start campaign orchestrator: {e}")
            raise
    
    async def stop(self):
        """Stop the campaign orchestrator."""
        try:
            self.is_running = False
            # Wait for active jobs to complete
            while self.active_jobs:
                await asyncio.sleep(1)
            logger.info("Campaign orchestrator stopped")
        except Exception as e:
            logger.error(f"Failed to stop campaign orchestrator: {e}")
    
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new campaign."""
        try:
            campaign_id = await db_manager.create_campaign(campaign_data)
            logger.info(f"Campaign created: {campaign_id}")
            return campaign_id
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            raise
    
    async def start_campaign(self, campaign_id: str, user_id: str) -> str:
        """Start a campaign execution."""
        try:
            # Create campaign job
            job = CampaignJob(
                job_id=f"job_{int(time.time() * 1000)}",
                campaign_id=campaign_id,
                user_id=user_id,
                status="pending",
                created_at=datetime.utcnow(),
                progress={"total_leads": 0, "processed": 0, "emails_sent": 0}
            )
            
            # Add to queue
            await self.job_queue.put(job)
            self.active_jobs[job.job_id] = job
            
            logger.info(f"Campaign job queued: {job.job_id}")
            return job.job_id
            
        except Exception as e:
            logger.error(f"Failed to start campaign: {e}")
            raise
    
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a running campaign."""
        try:
            # Find and pause active jobs for this campaign
            paused_count = 0
            for job in self.active_jobs.values():
                if job.campaign_id == campaign_id and job.status == "running":
                    job.status = "paused"
                    paused_count += 1
            
            # Update campaign status in database
            await db_manager.update_campaign_metrics(campaign_id, {"status": "paused"})
            
            logger.info(f"Campaign {campaign_id} paused: {paused_count} jobs affected")
            return paused_count > 0
            
        except Exception as e:
            logger.error(f"Failed to pause campaign {campaign_id}: {e}")
            return False
    
    async def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign."""
        try:
            # Resume paused jobs for this campaign
            resumed_count = 0
            for job in self.active_jobs.values():
                if job.campaign_id == campaign_id and job.status == "paused":
                    job.status = "pending"
                    await self.job_queue.put(job)
                    resumed_count += 1
            
            # Update campaign status in database
            await db_manager.update_campaign_metrics(campaign_id, {"status": "active"})
            
            logger.info(f"Campaign {campaign_id} resumed: {resumed_count} jobs affected")
            return resumed_count > 0
            
        except Exception as e:
            logger.error(f"Failed to resume campaign {campaign_id}: {e}")
            return False
    
    async def _process_job_queue(self):
        """Process jobs from the queue."""
        while self.is_running:
            try:
                # Get job from queue
                try:
                    job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Check if we can run more jobs
                if len([j for j in self.active_jobs.values() if j.status == "running"]) >= self.automation_config.max_concurrent_campaigns:
                    # Put job back in queue
                    await self.job_queue.put(job)
                    await asyncio.sleep(5)
                    continue
                
                # Execute job
                asyncio.create_task(self._execute_campaign_job(job))
                
            except Exception as e:
                logger.error(f"Job queue processing error: {e}")
                await asyncio.sleep(5)
    
    async def _execute_campaign_job(self, job: CampaignJob):
        """Execute a campaign job."""
        try:
            job.status = "running"
            job.started_at = datetime.utcnow()
            
            # Get campaign details
            campaign = await db_manager.get_campaign(job.campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {job.job_id} not found")
            
            # Get leads for campaign
            leads = await db_manager.get_leads_by_user(job.user_id, status="new")
            
            # Update progress
            job.progress["total_leads"] = len(leads)
            
            # Process leads in batches
            batch_size = self.automation_config.batch_size
            for i in range(0, len(leads), batch_size):
                batch = leads[i:i + batch_size]
                await self._process_lead_batch(batch, campaign, job)
                
                # Update progress
                job.progress["processed"] = min(i + batch_size, len(leads))
                
                # Check if job was paused
                if job.status == "paused":
                    logger.info(f"Campaign job {job.job_id} paused")
                    return
                
                # Rate limiting
                await asyncio.sleep(self.automation_config.processing_interval_minutes * 60)
            
            # Mark job as completed
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            logger.info(f"Campaign job {job.job_id} completed successfully")
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            logger.error(f"Campaign job {job.job_id} failed: {e}")
        
        finally:
            # Remove from active jobs
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    async def _process_lead_batch(self, leads: List[Lead], campaign: Campaign, job: CampaignJob):
        """Process a batch of leads."""
        try:
            for lead in leads:
                # Check if lead should be processed
                if not await self._should_process_lead(lead, campaign):
                    continue
                
                # Generate and send email
                await self._process_individual_lead(lead, campaign, job)
                
                # Update lead status
                await db_manager.update_lead_status(lead.lead_id, "contacted", {
                    "campaign_id": campaign.campaign_id,
                    "contacted_at": datetime.utcnow()
                })
                
                # Update job progress
                job.progress["emails_sent"] += 1
                
        except Exception as e:
            logger.error(f"Failed to process lead batch: {e}")
            raise
    
    async def _should_process_lead(self, lead: Lead, campaign: Campaign) -> bool:
        """Determine if a lead should be processed."""
        try:
            # Check if lead is already in a campaign
            if lead.campaign_id and lead.campaign_id != campaign.campaign_id:
                return False
            
            # Check if lead has been contacted recently
            if lead.last_contacted:
                days_since_contact = (datetime.utcnow() - lead.last_contacted).days
                if days_since_contact < self.email_config.follow_up_delay_hours / 24:
                    return False
            
            # Check lead score threshold
            if lead.lead_score < self.automation_config.lead_score_threshold:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Lead processing check failed: {e}")
            return False
    
    async def _process_individual_lead(self, lead: Lead, campaign: Campaign, job: CampaignJob):
        """Process an individual lead."""
        try:
            # Convert lead to LeadData format
            lead_data = self._convert_lead_to_lead_data(lead)
            
            # Generate personalized email
            lead_score, email_response = await ai_engine.process_lead(lead_data)
            
            if not email_response.success:
                logger.warning(f"Failed to generate email for lead {lead.lead_id}")
                return
            
            # Send email
            email_result = await integration_manager.gmail_api.send_email(
                to_email=lead.email,
                subject=f"Reaching out about {lead.company}",
                body=email_response.content
            )
            
            if email_result.success:
                # Store email record
                email_data = {
                    'email_id': email_result.message_id,
                    'campaign_id': campaign.campaign_id,
                    'lead_id': lead.lead_id,
                    'user_id': job.user_id,
                    'subject': f"Reaching out about {lead.company}",
                    'body': email_response.content,
                    'email_type': 'cold_email',
                    'status': 'sent',
                    'sent_at': email_result.sent_at
                }
                
                await db_manager.create_email(email_data)
                
                # Update lead engagement metrics
                await db_manager.update_lead_status(lead.lead_id, "contacted", {
                    "last_contacted": datetime.utcnow(),
                    "campaign_id": campaign.campaign_id,
                    "lead_score": lead_score.score
                })
                
                logger.info(f"Email sent successfully to {lead.email}")
            else:
                logger.error(f"Failed to send email to {lead.email}: {email_result.error_message}")
                
        except Exception as e:
            logger.error(f"Failed to process individual lead {lead.lead_id}: {e}")
    
    def _convert_lead_to_lead_data(self, lead: Lead):
        """Convert database Lead to LeadData format."""
        from integrations import LeadData
        
        return LeadData(
            name=lead.name,
            email=lead.email,
            company=lead.company,
            job_title=lead.job_title,
            phone=lead.phone,
            linkedin_url=lead.linkedin_url,
            company_description=lead.company_description,
            pain_points=lead.pain_points or []
        )
    
    async def _monitor_active_jobs(self):
        """Monitor active jobs for timeouts and errors."""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                for job_id, job in list(self.active_jobs.items()):
                    # Check for stuck jobs
                    if job.status == "running" and job.started_at:
                        running_time = (current_time - job.started_at).total_seconds() / 3600  # hours
                        if running_time > 24:  # 24 hour timeout
                            logger.warning(f"Job {job_id} timed out, marking as failed")
                            job.status = "failed"
                            job.error_message = "Job timed out after 24 hours"
                            job.completed_at = current_time
                            del self.active_jobs[job_id]
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Job monitoring error: {e}")
                await asyncio.sleep(60)

class FollowUpManager:
    """Manages automated follow-up sequences."""
    
    def __init__(self):
        self.email_config = config.get_email_config()
        self.automation_config = config.get_automation_config()
        logger.info("Follow-up manager initialized")
    
    async def schedule_follow_ups(self, lead_id: str, campaign_id: str, original_email: str):
        """Schedule follow-up emails for a lead."""
        try:
            # Get lead information
            lead = await db_manager.get_leads_by_user("", limit=1)  # Placeholder
            if not lead:
                return
            
            lead = lead[0]
            
            # Schedule follow-ups based on configuration
            follow_up_delays = [48, 72, 168]  # 2 days, 3 days, 1 week
            
            for i, delay_hours in enumerate(follow_up_delays[:self.email_config.max_follow_ups]):
                follow_up_time = datetime.utcnow() + timedelta(hours=delay_hours)
                
                # Create follow-up job
                await self._schedule_follow_up_job(
                    lead_id=lead_id,
                    campaign_id=campaign_id,
                    follow_up_number=i + 1,
                    scheduled_time=follow_up_time,
                    original_email=original_email
                )
            
            logger.info(f"Follow-ups scheduled for lead {lead_id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule follow-ups for lead {lead_id}: {e}")
    
    async def _schedule_follow_up_job(self, lead_id: str, campaign_id: str, 
                                    follow_up_number: int, scheduled_time: datetime, 
                                    original_email: str):
        """Schedule a specific follow-up job."""
        try:
            # This would integrate with a job scheduler in production
            # For now, we'll store it in the database
            follow_up_data = {
                'lead_id': lead_id,
                'campaign_id': campaign_id,
                'follow_up_number': follow_up_number,
                'scheduled_time': scheduled_time,
                'original_email': original_email,
                'status': 'scheduled'
            }
            
            # Store in database (you might want a separate collection for this)
            logger.info(f"Follow-up {follow_up_number} scheduled for {scheduled_time}")
            
        except Exception as e:
            logger.error(f"Failed to schedule follow-up job: {e}")
    
    async def process_follow_ups(self):
        """Process scheduled follow-ups."""
        try:
            # This would check for due follow-ups and execute them
            # Implementation depends on your job scheduling system
            pass
            
        except Exception as e:
            logger.error(f"Follow-up processing failed: {e}")

class AutomationManager:
    """Main automation manager that coordinates all automation features."""
    
    def __init__(self):
        self.campaign_orchestrator = CampaignOrchestrator()
        self.follow_up_manager = FollowUpManager()
        logger.info("Automation manager initialized")
    
    async def start(self):
        """Start all automation services."""
        try:
            await self.campaign_orchestrator.start()
            logger.info("Automation services started")
        except Exception as e:
            logger.error(f"Failed to start automation services: {e}")
            raise
    
    async def stop(self):
        """Stop all automation services."""
        try:
            await self.campaign_orchestrator.stop()
            logger.info("Automation services stopped")
        except Exception as e:
            logger.error(f"Failed to stop automation services: {e}")
    
    async def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get status of a campaign."""
        try:
            campaign = await db_manager.get_campaign(campaign_id)
            if not campaign:
                return {"error": "Campaign not found"}
            
            # Get active jobs for this campaign
            active_jobs = [
                job for job in self.campaign_orchestrator.active_jobs.values()
                if job.campaign_id == campaign_id
            ]
            
            return {
                "campaign": campaign,
                "active_jobs": len(active_jobs),
                "job_statuses": [job.status for job in active_jobs]
            }
            
        except Exception as e:
            logger.error(f"Failed to get campaign status: {e}")
            return {"error": str(e)}
    
    async def get_automation_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get automation performance metrics."""
        try:
            # Get user's campaigns
            campaigns = []  # Placeholder for campaign retrieval
            
            # Calculate metrics
            total_campaigns = len(campaigns)
            active_campaigns = len([c for c in campaigns if c.status == "active"])
            completed_campaigns = len([c for c in campaigns if c.status == "completed"])
            
            return {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "completed_campaigns": completed_campaigns,
                "success_rate": completed_campaigns / total_campaigns if total_campaigns > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get automation metrics: {e}")
            return {}

# Global automation manager instance
automation_manager = AutomationManager()

# Export for easy access
__all__ = [
    'automation_manager', 'AutomationManager', 'CampaignOrchestrator',
    'FollowUpManager', 'EmailSequence', 'CampaignJob'
]
