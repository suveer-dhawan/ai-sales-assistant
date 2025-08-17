"""
AI Intelligence Core

This module provides the core AI capabilities for the sales assistant platform.
It handles personalized email generation, response analysis, lead scoring,
and machine learning algorithms for optimizing sales processes.

Dependencies: numpy, pandas, sklearn, config.py, integrations.py, database.py
Used by: automation.py, app.py
"""

import logging
import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os
import hashlib

from config import config
from integrations import integration_manager, LeadData, AIResponse
from database import db_manager, Lead, Email

logger = logging.getLogger(__name__)

@dataclass
class LeadScore:
    """Lead scoring result."""
    lead_id: str
    score: float
    factors: Dict[str, float]
    confidence: float
    recommendations: List[str]

@dataclass
class EmailAnalysis:
    """Email analysis result."""
    email_id: str
    sentiment: str
    intent: str
    key_points: List[str]
    next_action: str
    confidence: float
    urgency: str
    engagement_score: float

@dataclass
class PersonalizationData:
    """Data used for email personalization."""
    lead_data: LeadData
    company_research: Dict[str, Any]
    industry_insights: Dict[str, Any]
    pain_point_analysis: Dict[str, Any]
    personalization_score: float

class LeadScoringEngine:
    """Machine learning engine for lead scoring and qualification."""
    
    def __init__(self):
        self.model_path = "models/lead_scoring_model.pkl"
        self.scaler_path = "models/lead_scoring_scaler.pkl"
        self.vectorizer_path = "models/lead_scoring_vectorizer.pkl"
        self.model = None
        self.scaler = None
        self.vectorizer = None
        self.feature_columns = [
            'company_size_score', 'job_title_score', 'industry_score',
            'pain_points_score', 'engagement_score', 'response_rate_score'
        ]
        self._load_or_create_model()
        logger.info("Lead scoring engine initialized")
    
    def _load_or_create_model(self):
        """Load existing model or create a new one."""
        try:
            if (os.path.exists(self.model_path) and 
                os.path.exists(self.scaler_path) and 
                os.path.exists(self.vectorizer_path)):
                
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                
                logger.info("Loaded existing lead scoring model")
            else:
                self._create_new_model()
                logger.info("Created new lead scoring model")
                
        except Exception as e:
            logger.error(f"Failed to load/create model: {e}")
            self._create_new_model()
    
    def _create_new_model(self):
        """Create a new lead scoring model."""
        try:
            # Create directories if they don't exist
            os.makedirs("models", exist_ok=True)
            
            # Initialize new model components
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            
            # Save the new model
            self._save_model()
            
        except Exception as e:
            logger.error(f"Failed to create new model: {e}")
            raise
    
    def _save_model(self):
        """Save the current model to disk."""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            logger.info("Model saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _extract_features(self, lead_data: LeadData, engagement_data: Dict[str, Any] = None) -> np.ndarray:
        """Extract numerical features from lead data."""
        try:
            features = []
            
            # Company size scoring (based on company description length and keywords)
            company_size_score = min(len(lead_data.company_description or '') / 100, 1.0)
            features.append(company_size_score)
            
            # Job title scoring (higher for decision makers)
            decision_maker_titles = ['ceo', 'cto', 'cfo', 'vp', 'director', 'manager', 'head']
            job_title_lower = lead_data.job_title.lower()
            job_title_score = sum(1 for title in decision_maker_titles if title in job_title_lower) / len(decision_maker_titles)
            features.append(job_title_score)
            
            # Industry scoring (based on company description keywords)
            industry_keywords = {
                'tech': ['software', 'technology', 'saas', 'startup', 'digital'],
                'finance': ['banking', 'financial', 'insurance', 'investment'],
                'healthcare': ['health', 'medical', 'pharmaceutical', 'hospital'],
                'retail': ['ecommerce', 'retail', 'consumer', 'shopping']
            }
            
            company_desc = (lead_data.company_description or '').lower()
            industry_score = 0
            for industry, keywords in industry_keywords.items():
                if any(keyword in company_desc for keyword in keywords):
                    industry_score = 1.0
                    break
            features.append(industry_score)
            
            # Pain points scoring
            pain_points_score = min(len(lead_data.pain_points) / 5, 1.0) if lead_data.pain_points else 0
            features.append(pain_points_score)
            
            # Engagement scoring
            engagement_score = engagement_data.get('engagement_score', 0.0) if engagement_data else 0.0
            features.append(engagement_score)
            
            # Response rate scoring (placeholder for future implementation)
            response_rate_score = 0.5  # Default neutral score
            features.append(response_rate_score)
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Failed to extract features: {e}")
            return np.zeros((1, len(self.feature_columns)))
    
    async def score_lead(self, lead_data: LeadData, engagement_data: Dict[str, Any] = None) -> LeadScore:
        """Score a lead using the ML model."""
        try:
            # Extract features
            features = self._extract_features(lead_data, engagement_data)
            
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Get prediction probability
            if self.model is not None:
                score_prob = self.model.predict_proba(scaled_features)[0]
                score = score_prob[1] if len(score_prob) > 1 else score_prob[0]  # Probability of positive class
            else:
                # Fallback scoring if model not available
                score = self._fallback_scoring(lead_data, engagement_data)
            
            # Calculate confidence based on feature quality
            confidence = self._calculate_confidence(features[0])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(lead_data, score, features[0])
            
            # Create lead score result
            lead_score = LeadScore(
                lead_id=getattr(lead_data, 'lead_id', 'unknown'),
                score=float(score),
                factors={
                    'company_size': float(features[0][0]),
                    'job_title': float(features[0][1]),
                    'industry': float(features[0][2]),
                    'pain_points': float(features[0][3]),
                    'engagement': float(features[0][4]),
                    'response_rate': float(features[0][5])
                },
                confidence=confidence,
                recommendations=recommendations
            )
            
            logger.info(f"Lead scored successfully: {lead_score.score:.3f}")
            return lead_score
            
        except Exception as e:
            logger.error(f"Failed to score lead: {e}")
            # Return default score
            return LeadScore(
                lead_id=getattr(lead_data, 'lead_id', 'unknown'),
                score=0.5,
                factors={},
                confidence=0.0,
                recommendations=["Unable to score lead due to error"]
            )
    
    def _fallback_scoring(self, lead_data: LeadData, engagement_data: Dict[str, Any] = None) -> float:
        """Fallback scoring when ML model is not available."""
        try:
            score = 0.5  # Base score
            
            # Adjust based on job title
            decision_maker_titles = ['ceo', 'cto', 'cfo', 'vp', 'director', 'manager']
            if any(title in lead_data.job_title.lower() for title in decision_maker_titles):
                score += 0.2
            
            # Adjust based on pain points
            if lead_data.pain_points and len(lead_data.pain_points) > 0:
                score += 0.1
            
            # Adjust based on company description
            if lead_data.company_description and len(lead_data.company_description) > 50:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Fallback scoring failed: {e}")
            return 0.5
    
    def _calculate_confidence(self, features: np.ndarray) -> float:
        """Calculate confidence in the score based on feature quality."""
        try:
            # Higher confidence for more complete data
            non_zero_features = np.count_nonzero(features)
            confidence = min(non_zero_features / len(features), 1.0)
            
            # Boost confidence for high-quality features
            if features[1] > 0.5:  # Good job title
                confidence += 0.1
            if features[3] > 0.5:  # Good pain points
                confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            return 0.5
    
    def _generate_recommendations(self, lead_data: LeadData, score: float, features: np.ndarray) -> List[str]:
        """Generate recommendations based on lead score and features."""
        try:
            recommendations = []
            
            if score < 0.3:
                recommendations.append("Low priority lead - consider nurturing campaign")
                recommendations.append("Focus on building awareness before sales pitch")
            elif score < 0.7:
                recommendations.append("Medium priority - standard outreach sequence")
                recommendations.append("Monitor engagement and adjust approach")
            else:
                recommendations.append("High priority lead - immediate follow-up recommended")
                recommendations.append("Consider personalized demo or meeting request")
            
            # Specific recommendations based on features
            if features[1] < 0.3:  # Low job title score
                recommendations.append("Target higher-level decision makers in organization")
            
            if features[3] < 0.3:  # Low pain points
                recommendations.append("Research company to identify potential pain points")
            
            if features[4] < 0.3:  # Low engagement
                recommendations.append("Improve email personalization and timing")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations"]

class EmailPersonalizationEngine:
    """Engine for creating highly personalized email content."""
    
    def __init__(self):
        self.gemini_api = integration_manager.gemini_api
        self.personalization_cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.request_cache = {}  # Cache for AI requests to avoid duplicates
        self.request_cache_ttl = 1800  # 30 minutes
        self.rate_limit_delay = 1.0  # 1 second between API calls
        self.last_api_call = 0
        self.daily_api_calls = 0
        self.max_daily_calls = 1000  # Conservative daily limit for Gemini 2.5 Flash-Lite
        logger.info("Email personalization engine initialized with rate limiting")
    
    async def personalize_email(self, lead_data: LeadData, email_type: str = "cold_email",
                              context: Dict[str, Any] = None) -> AIResponse:
        """Generate personalized email content."""
        try:
            # Check cache first to avoid duplicate API calls
            cache_key = self._get_cache_key(lead_data, email_type, context)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
            
            # Get personalization data
            personalization_data = await self._get_personalization_data(lead_data)
            
            # Generate personalized prompt
            prompt = self._create_personalized_prompt(lead_data, personalization_data, email_type, context)
            
            # Check rate limits before making API call
            await self._check_rate_limits()
            
            # Generate content using AI
            response = await self.gemini_api.generate_content(prompt, {
                'lead_name': lead_data.name,
                'job_title': lead_data.job_title,
                'company': lead_data.company,
                'personalization_score': personalization_data.personalization_score
            })
            
            # Increment API call counter
            self.daily_api_calls += 1
            
            if response.success:
                logger.info(f"Personalized {email_type} generated successfully")
                
                # Store personalization data for future use
                self._cache_personalization_data(lead_data.email, personalization_data)
                
                # Cache the AI response
                self._cache_ai_response(cache_key, response)
            else:
                logger.warning(f"AI generation failed, will not cache failed response")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to personalize email: {e}")
            return AIResponse(
                success=False,
                error_message=str(e)
            )
    
    async def _get_personalization_data(self, lead_data: LeadData) -> PersonalizationData:
        """Gather comprehensive personalization data for a lead."""
        try:
            # Company research (placeholder for future implementation)
            company_research = await self._research_company(lead_data.company)
            
            # Industry insights
            industry_insights = await self._get_industry_insights(lead_data.company_description)
            
            # Pain point analysis
            pain_point_analysis = await self._analyze_pain_points(lead_data.pain_points)
            
            # Calculate personalization score
            personalization_score = self._calculate_personalization_score(
                company_research, industry_insights, pain_point_analysis
            )
            
            return PersonalizationData(
                lead_data=lead_data,
                company_research=company_research,
                industry_insights=industry_insights,
                pain_point_analysis=pain_point_analysis,
                personalization_score=personalization_score
            )
            
        except Exception as e:
            logger.error(f"Failed to get personalization data: {e}")
            # Return minimal personalization data
            return PersonalizationData(
                lead_data=lead_data,
                company_research={},
                industry_insights={},
                pain_point_analysis={},
                personalization_score=0.5
            )
    
    async def _research_company(self, company_name: str) -> Dict[str, Any]:
        """Research company information (placeholder for future implementation)."""
        try:
            # This would integrate with company research APIs in the future
            return {
                'size': 'unknown',
                'industry': 'unknown',
                'recent_news': [],
                'key_metrics': {}
            }
        except Exception as e:
            logger.error(f"Company research failed: {e}")
            return {}
    
    async def _get_industry_insights(self, company_description: str) -> Dict[str, Any]:
        """Get industry insights based on company description."""
        try:
            if not company_description:
                return {}
            
            # Simple keyword-based industry detection
            industry_keywords = {
                'technology': ['software', 'saas', 'tech', 'digital', 'platform'],
                'finance': ['financial', 'banking', 'investment', 'insurance'],
                'healthcare': ['health', 'medical', 'pharmaceutical', 'hospital'],
                'retail': ['ecommerce', 'retail', 'consumer', 'shopping']
            }
            
            description_lower = company_description.lower()
            detected_industries = []
            
            for industry, keywords in industry_keywords.items():
                if any(keyword in description_lower for keyword in keywords):
                    detected_industries.append(industry)
            
            return {
                'detected_industries': detected_industries,
                'trends': self._get_industry_trends(detected_industries)
            }
            
        except Exception as e:
            logger.error(f"Industry insights failed: {e}")
            return {}
    
    def _get_industry_trends(self, industries: List[str]) -> List[str]:
        """Get industry trends (placeholder for future implementation)."""
        # This would integrate with industry research APIs
        return ["Digital transformation", "Remote work adoption", "AI integration"]
    
    async def _analyze_pain_points(self, pain_points: List[str]) -> Dict[str, Any]:
        """Analyze and categorize pain points."""
        try:
            if not pain_points:
                return {}
            
            # Categorize pain points
            categories = {
                'efficiency': ['slow', 'manual', 'time-consuming', 'inefficient'],
                'cost': ['expensive', 'costly', 'budget', 'expensive'],
                'technology': ['outdated', 'integration', 'compatibility', 'technical'],
                'scalability': ['growth', 'scale', 'capacity', 'performance']
            }
            
            categorized_points = {}
            for point in pain_points:
                point_lower = point.lower()
                for category, keywords in categories.items():
                    if any(keyword in point_lower for keyword in keywords):
                        if category not in categorized_points:
                            categorized_points[category] = []
                        categorized_points[category].append(point)
                        break
                else:
                    if 'other' not in categorized_points:
                        categorized_points['other'] = []
                    categorized_points['other'].append(point)
            
            return {
                'categories': categorized_points,
                'primary_category': max(categorized_points.keys(), key=lambda k: len(categorized_points[k])) if categorized_points else 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Pain point analysis failed: {e}")
            return {}
    
    def _calculate_personalization_score(self, company_research: Dict[str, Any],
                                       industry_insights: Dict[str, Any],
                                       pain_point_analysis: Dict[str, Any]) -> float:
        """Calculate overall personalization score."""
        try:
            score = 0.5  # Base score
            
            # Company research contribution
            if company_research.get('size') != 'unknown':
                score += 0.1
            if company_research.get('industry') != 'unknown':
                score += 0.1
            
            # Industry insights contribution
            if industry_insights.get('detected_industries'):
                score += 0.1
            if industry_insights.get('trends'):
                score += 0.1
            
            # Pain point analysis contribution
            if pain_point_analysis.get('categories'):
                score += 0.1
            if pain_point_analysis.get('primary_category') != 'unknown':
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Personalization score calculation failed: {e}")
            return 0.5
    
    def _create_personalized_prompt(self, lead_data: LeadData, personalization_data: PersonalizationData,
                                   email_type: str, context: Dict[str, Any] = None) -> str:
        """Create highly personalized prompt for AI generation."""
        try:
            base_prompt = config.get_email_config().cold_email_prompt
            
            # Enhance with personalization data
            enhanced_prompt = f"""
            {base_prompt}
            
            Additional Personalization Context:
            - Company Size: {personalization_data.company_research.get('size', 'Unknown')}
            - Industry: {', '.join(personalization_data.industry_insights.get('detected_industries', ['Unknown']))}
            - Industry Trends: {', '.join(personalization_data.industry_insights.get('trends', []))}
            - Pain Point Categories: {', '.join(personalization_data.pain_point_analysis.get('categories', {}).keys())}
            - Primary Pain Point Category: {personalization_data.pain_point_analysis.get('primary_category', 'Unknown')}
            
            Personalization Score: {personalization_data.personalization_score:.2f}
            
            Instructions:
            - Use the personalization data to make the email highly relevant
            - Reference specific industry trends and pain points
            - Ensure the tone matches the lead's role and company size
            - Include specific examples related to their industry
            """
            
            if context:
                context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])
                enhanced_prompt += f"\n\nAdditional Context:\n{context_str}"
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Failed to create personalized prompt: {e}")
            return base_prompt
    
    def _cache_personalization_data(self, email: str, data: PersonalizationData):
        """Cache personalization data for future use."""
        try:
            self.personalization_cache[email] = {
                'data': data,
                'timestamp': time.time()
            }
            
            # Clean up old cache entries
            current_time = time.time()
            expired_keys = [
                key for key, value in self.personalization_cache.items()
                if current_time - value['timestamp'] > self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.personalization_cache[key]
                
        except Exception as e:
            logger.error(f"Failed to cache personalization data: {e}")
    
    def _get_cache_key(self, lead_data: LeadData, email_type: str, context: Dict[str, Any] = None) -> str:
        """Generate a unique cache key for AI requests."""
        try:
            # Create a hash of the request parameters
            key_data = {
                'email': lead_data.email,
                'job_title': lead_data.job_title,
                'company': lead_data.company,
                'email_type': email_type,
                'context_hash': hash(str(sorted(context.items()))) if context else 0
            }
            key_string = json.dumps(key_data, sort_keys=True)
            return hashlib.md5(key_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to generate cache key: {e}")
            return f"{lead_data.email}_{email_type}_{int(time.time())}"
    
    def _is_cached_request(self, cache_key: str) -> bool:
        """Check if a request is cached and still valid."""
        try:
            if cache_key in self.request_cache:
                cache_entry = self.request_cache[cache_key]
                age = (datetime.utcnow() - cache_entry['timestamp']).total_seconds()
                return age < self.request_cache_ttl
            return False
        except Exception as e:
            logger.error(f"Failed to check cache: {e}")
            return False
    
    def _cache_ai_response(self, cache_key: str, response: AIResponse):
        """Cache AI response to avoid duplicate API calls."""
        try:
            self.request_cache[cache_key] = {
                'response': response,
                'timestamp': datetime.utcnow()
            }
            logger.debug(f"Cached AI response for key: {cache_key[:10]}...")
        except Exception as e:
            logger.error(f"Failed to cache AI response: {e}")
    
    def _get_cached_response(self, cache_key: str) -> Optional[AIResponse]:
        """Get cached AI response if available."""
        try:
            if cache_key in self.request_cache:
                cache_entry = self.request_cache[cache_key]
                age = (datetime.utcnow() - cache_entry['timestamp']).total_seconds()
                if age < self.request_cache_ttl:
                    logger.info(f"Using cached AI response for key: {self.daily_api_calls}/{self.max_daily_calls} API calls used today")
                    return cache_entry['response']
            return None
        except Exception as e:
            logger.error(f"Failed to get cached response: {e}")
            return None
    
    async def _check_rate_limits(self):
        """Check and enforce rate limits to optimize API usage."""
        import time
        import asyncio
        
        current_time = time.time()
        
        # Check daily limit
        if self.daily_api_calls >= self.max_daily_calls:
            raise Exception(f"Daily API call limit reached ({self.max_daily_calls}). Please try again tomorrow.")
        
        # Check rate limiting delay
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.rate_limit_delay:
            delay_needed = self.rate_limit_delay - time_since_last_call
            logger.info(f"Rate limiting: waiting {delay_needed:.2f}s before next API call")
            await asyncio.sleep(delay_needed)
        
        self.last_api_call = current_time
        
        # Log API usage
        logger.info(f"API call made. Daily usage: {self.daily_api_calls}/{self.max_daily_calls}")
    
    def reset_daily_counter(self):
        """Reset the daily API call counter (call this daily)."""
        self.daily_api_calls = 0
        logger.info("Daily API call counter reset")
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """Get current API usage statistics."""
        return {
            'daily_calls_used': self.daily_api_calls,
            'daily_calls_limit': self.max_daily_calls,
            'calls_remaining': self.max_daily_calls - self.daily_api_calls,
            'cache_hit_rate': len(self.request_cache) / max(1, self.daily_api_calls) if self.daily_api_calls > 0 else 0
        }

class ResponseAnalysisEngine:
    """Engine for analyzing email responses and determining next actions."""
    
    def __init__(self):
        self.gemini_api = integration_manager.gemini_api
        logger.info("Response analysis engine initialized")
    
    async def analyze_response(self, email_content: str, lead_context: Dict[str, Any] = None) -> EmailAnalysis:
        """Analyze email response content."""
        try:
            # Use Gemini AI to analyze the response
            analysis_response = await self.gemini_api.analyze_response(email_content)
            
            if not analysis_response.success:
                return EmailAnalysis(
                    email_id='unknown',
                    sentiment='unknown',
                    intent='unknown',
                    key_points=[],
                    next_action='manual_review',
                    confidence=0.0,
                    urgency='low',
                    engagement_score=0.0
                )
            
            # Parse the analysis
            try:
                analysis_data = json.loads(analysis_response.content)
                
                # Extract analysis components
                sentiment = analysis_data.get('sentiment', 'neutral')
                intent = analysis_data.get('intent', 'unknown')
                key_points = analysis_data.get('key_points', [])
                next_action = analysis_data.get('recommended_next_action', 'manual_review')
                confidence = float(analysis_data.get('confidence_score', 0)) / 100
                
                # Calculate urgency and engagement score
                urgency = self._calculate_urgency(sentiment, intent, key_points)
                engagement_score = self._calculate_engagement_score(sentiment, intent, confidence)
                
                email_analysis = EmailAnalysis(
                    email_id='unknown',  # Will be set by calling function
                    sentiment=sentiment,
                    intent=intent,
                    key_points=key_points,
                    next_action=next_action,
                    confidence=confidence,
                    urgency=urgency,
                    engagement_score=engagement_score
                )
                
                logger.info(f"Response analyzed successfully: {sentiment} sentiment, {intent} intent")
                return email_analysis
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI analysis, using fallback")
                return self._fallback_analysis(email_content)
                
        except Exception as e:
            logger.error(f"Response analysis failed: {e}")
            return self._fallback_analysis(email_content)
    
    def _calculate_urgency(self, sentiment: str, intent: str, key_points: List[str]) -> str:
        """Calculate urgency level based on analysis."""
        try:
            urgency_score = 0
            
            # Sentiment contribution
            if sentiment == 'positive':
                urgency_score += 2
            elif sentiment == 'negative':
                urgency_score += 1
            
            # Intent contribution
            if intent == 'interested':
                urgency_score += 3
            elif intent == 'needs_more_info':
                urgency_score += 2
            elif intent == 'not_interested':
                urgency_score += 0
            
            # Key points contribution
            urgency_keywords = ['urgent', 'asap', 'immediate', 'critical', 'emergency']
            for point in key_points:
                if any(keyword in point.lower() for keyword in urgency_keywords):
                    urgency_score += 2
            
            if urgency_score >= 5:
                return 'high'
            elif urgency_score >= 3:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Urgency calculation failed: {e}")
            return 'low'
    
    def _calculate_engagement_score(self, sentiment: str, intent: str, confidence: float) -> float:
        """Calculate engagement score based on analysis."""
        try:
            score = 0.0
            
            # Sentiment contribution
            if sentiment == 'positive':
                score += 0.4
            elif sentiment == 'neutral':
                score += 0.2
            elif sentiment == 'negative':
                score += 0.1
            
            # Intent contribution
            if intent == 'interested':
                score += 0.4
            elif intent == 'needs_more_info':
                score += 0.3
            elif intent == 'not_interested':
                score += 0.0
            
            # Confidence contribution
            score += confidence * 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Engagement score calculation failed: {e}")
            return 0.5
    
    def _fallback_analysis(self, email_content: str) -> EmailAnalysis:
        """Fallback analysis when AI analysis fails."""
        try:
            content_lower = email_content.lower()
            
            # Simple keyword-based analysis
            positive_words = ['interested', 'yes', 'great', 'good', 'like', 'love']
            negative_words = ['not interested', 'no', 'bad', 'dislike', 'unfortunately']
            
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > negative_count:
                sentiment = 'positive'
                intent = 'interested'
            elif negative_count > positive_count:
                sentiment = 'negative'
                intent = 'not_interested'
            else:
                sentiment = 'neutral'
                intent = 'needs_more_info'
            
            return EmailAnalysis(
                email_id='unknown',
                sentiment=sentiment,
                intent=intent,
                key_points=['Fallback analysis used'],
                next_action='manual_review',
                confidence=0.3,
                urgency='low',
                engagement_score=0.5
            )
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return EmailAnalysis(
                email_id='unknown',
                sentiment='unknown',
                intent='unknown',
                key_points=[],
                next_action='manual_review',
                confidence=0.0,
                urgency='low',
                engagement_score=0.0
            )

class AIEngine:
    """Main AI engine that coordinates all AI capabilities for sales automation."""
    
    def __init__(self):
        self.lead_scoring = LeadScoringEngine()
        self.personalization = EmailPersonalizationEngine()
        self.response_analysis = ResponseAnalysisEngine()
        self.gemini_api = integration_manager.gemini_api
        logger.info("AI engine initialized successfully")
    
    # =============================================================================
    # CORE SALES AUTOMATION FUNCTIONS
    # =============================================================================
    
    async def generate_cold_email(self, lead_data: LeadData, user_settings: Dict[str, Any]) -> AIResponse:
        """
        Generate completely unique, personalized cold email for sales automation.
        
        Args:
            lead_data: Lead information including job title, company, pain points
            user_settings: User's sales approach, value proposition, calendly link
            
        Returns:
            AIResponse with personalized email content including subject line
        """
        try:
            # Analyze job title and company for pain points
            job_analysis = await self.analyze_job_title(lead_data.job_title, lead_data.company)
            
            # Create comprehensive prompt for cold email generation
            prompt = self._create_cold_email_prompt(lead_data, job_analysis, user_settings)
            
            # Generate email using Gemini AI
            response = await self.gemini_api.generate_content(prompt, {
                'lead_name': lead_data.name,
                'job_title': lead_data.job_title,
                'company': lead_data.company,
                'pain_points': lead_data.pain_points,
                'company_description': lead_data.company_description
            })
            
            if response.success:
                logger.info(f"Cold email generated successfully for {lead_data.email}")
                
                # Parse and structure the response
                parsed_response = self._parse_email_response(response.content)
                return AIResponse(
                    success=True,
                    content=parsed_response['email_body'],
                    metadata={
                        'subject_line': parsed_response['subject_line'],
                        'personalization_score': parsed_response['personalization_score'],
                        'pain_points_addressed': parsed_response['pain_points_addressed'],
                        'calendly_integration': parsed_response['calendly_integration']
                    }
                )
            else:
                logger.error(f"Failed to generate cold email: {response.error_message}")
                return response
                
        except Exception as e:
            logger.error(f"Cold email generation failed: {e}")
            return AIResponse(
                success=False,
                error_message=f"Cold email generation failed: {str(e)}"
            )
    
    async def classify_response(self, email_content: str) -> AIResponse:
        """
        Analyze reply sentiment and intent for automated follow-up decisions.
        
        Args:
            email_content: The email response content to analyze
            
        Returns:
            AIResponse with classification, confidence score, and reasoning
        """
        try:
            prompt = self._create_response_classification_prompt(email_content)
            
            response = await self.gemini_api.generate_content(prompt, {
                'email_content': email_content
            })
            
            if response.success:
                # Parse the structured response
                classification_data = self._parse_classification_response(response.content)
                
                return AIResponse(
                    success=True,
                    content=json.dumps(classification_data, indent=2),
                    metadata={
                        'classification': classification_data.get('classification'),
                        'confidence_score': classification_data.get('confidence_score'),
                        'sentiment': classification_data.get('sentiment'),
                        'urgency_level': classification_data.get('urgency_level')
                    }
                )
            else:
                logger.error(f"Response classification failed: {response.error_message}")
                return response
                
        except Exception as e:
            logger.error(f"Response classification failed: {e}")
            return AIResponse(
                success=False,
                error_message=f"Response classification failed: {str(e)}"
            )
    
    async def score_lead(self, lead_data: LeadData) -> LeadScore:
        """
        Comprehensive lead scoring with Hot/Warm/Cold classification.
        
        Args:
            lead_data: Lead information for scoring analysis
            
        Returns:
            LeadScore with classification, score, and detailed reasoning
        """
        try:
            # Use existing ML-based scoring
            ml_score = await self.lead_scoring.score_lead(lead_data)
            
            # Enhanced scoring with AI analysis
            ai_analysis = await self._enhance_lead_scoring_with_ai(lead_data)
            
            # Combine ML and AI scores
            final_score = (ml_score.score * 0.6) + (ai_analysis.get('ai_score', 0.5) * 0.4)
            
            # Determine classification
            if final_score >= 0.8:
                classification = "Hot"
                priority = "Immediate follow-up"
            elif final_score >= 0.6:
                classification = "Warm"
                priority = "Standard sequence"
            else:
                classification = "Cold"
                priority = "Nurturing campaign"
            
            # Create enhanced lead score
            enhanced_score = LeadScore(
                lead_id=getattr(lead_data, 'lead_id', 'unknown'),
                score=final_score,
                factors={
                    **ml_score.factors,
                    'ai_analysis_score': ai_analysis.get('ai_score', 0.0),
                    'decision_authority': ai_analysis.get('decision_authority', 0.0),
                    'company_relevance': ai_analysis.get('company_relevance', 0.0)
                },
                confidence=ml_score.confidence,
                recommendations=[
                    f"Classification: {classification}",
                    f"Priority: {priority}",
                    *ai_analysis.get('recommendations', []),
                    *ml_score.recommendations
                ]
            )
            
            logger.info(f"Enhanced lead scoring completed: {classification} ({final_score:.3f})")
            return enhanced_score
            
        except Exception as e:
            logger.error(f"Enhanced lead scoring failed: {e}")
            # Fallback to basic scoring
            return await self.lead_scoring.score_lead(lead_data)
    
    async def generate_followup_email(self, lead_data: LeadData, previous_emails: List[Dict[str, Any]], 
                                    sequence_step: int) -> AIResponse:
        """
        Generate context-aware follow-up email with progressive value delivery.
        
        Args:
            lead_data: Lead information
            previous_emails: List of previous email interactions
            sequence_step: Current step in the follow-up sequence
            
        Returns:
            AIResponse with personalized follow-up email
        """
        try:
            # Analyze previous interactions
            interaction_context = self._analyze_interaction_context(previous_emails, sequence_step)
            
            # Create follow-up specific prompt
            prompt = self._create_followup_prompt(lead_data, interaction_context, sequence_step)
            
            # Generate follow-up email
            response = await self.gemini_api.generate_content(prompt, {
                'lead_name': lead_data.name,
                'sequence_step': sequence_step,
                'previous_context': interaction_context
            })
            
            if response.success:
                logger.info(f"Follow-up email generated for step {sequence_step}")
                
                # Parse and structure the response
                parsed_response = self._parse_email_response(response.content)
                return AIResponse(
                    success=True,
                    content=parsed_response['email_body'],
                    metadata={
                        'subject_line': parsed_response['subject_line'],
                        'sequence_step': sequence_step,
                        'urgency_level': parsed_response.get('urgency_level', 'medium'),
                        'value_proposition': parsed_response.get('value_proposition', ''),
                        'next_action': parsed_response.get('next_action', '')
                    }
                )
            else:
                logger.error(f"Follow-up generation failed: {response.error_message}")
                return response
                
        except Exception as e:
            logger.error(f"Follow-up generation failed: {e}")
            return AIResponse(
                success=False,
                error_message=f"Follow-up generation failed: {str(e)}"
            )
    
    async def analyze_job_title(self, job_title: str, company: str) -> Dict[str, Any]:
        """
        Comprehensive job title analysis for personalization and pain point identification.
        
        Args:
            job_title: The job title to analyze
            company: Company name for context
            
        Returns:
            Dictionary with analysis results
        """
        try:
            prompt = self._create_job_title_analysis_prompt(job_title, company)
            
            response = await self.gemini_api.generate_content(prompt, {
                'job_title': job_title,
                'company': company
            })
            
            if response.success:
                # Parse the structured response
                analysis_data = self._parse_job_analysis_response(response.content)
                
                logger.info(f"Job title analysis completed for {job_title}")
                return analysis_data
            else:
                logger.error(f"Job title analysis failed: {response.error_message}")
                return self._fallback_job_analysis(job_title, company)
                
        except Exception as e:
            logger.error(f"Job title analysis failed: {e}")
            return self._fallback_job_analysis(job_title, company)
    
    # =============================================================================
    # PROMPT CREATION METHODS
    # =============================================================================
    
    def _create_cold_email_prompt(self, lead_data: LeadData, job_analysis: Dict[str, Any], 
                                 user_settings: Dict[str, Any]) -> str:
        """Create comprehensive prompt for cold email generation."""
        return f"""
        You are an expert sales professional writing a personalized cold email. Your goal is to create a completely unique, compelling email that addresses the recipient's specific situation.

        LEAD INFORMATION:
        - Name: {lead_data.name}
        - Job Title: {lead_data.job_title}
        - Company: {lead_data.company}
        - Company Description: {lead_data.company_description or 'Not provided'}
        - Pain Points: {', '.join(lead_data.pain_points) if lead_data.pain_points else 'To be identified'}

        JOB ANALYSIS:
        - Seniority Level: {job_analysis.get('seniority_level', 'Unknown')}
        - Decision Authority: {job_analysis.get('decision_authority', 'Unknown')}
        - Likely Pain Points: {', '.join(job_analysis.get('likely_pain_points', []))}
        - Industry Context: {job_analysis.get('industry_context', 'Unknown')}

        USER SETTINGS:
        - Value Proposition: {user_settings.get('value_proposition', 'To be customized')}
        - Calendly Link: {user_settings.get('calendly_link', 'To be included')}
        - Sales Approach: {user_settings.get('sales_approach', 'Professional and consultative')}

        REQUIREMENTS:
        1. Create a compelling subject line (max 60 characters)
        2. Write a personalized email body (max 150 words)
        3. Address specific pain points based on their role and company
        4. Include the Calendly link naturally in the flow
        5. End with a clear, specific call-to-action
        6. Use their name naturally throughout
        7. Reference their company and role specifically
        8. Avoid generic templates - make it completely unique

        FORMAT YOUR RESPONSE AS JSON:
        {{
            "subject_line": "Your compelling subject line",
            "email_body": "Your personalized email content",
            "personalization_score": 0.95,
            "pain_points_addressed": ["pain point 1", "pain point 2"],
            "calendly_integration": "How the calendly link was integrated"
        }}

        Remember: This email should feel like it was written specifically for {lead_data.name} at {lead_data.company}, not a mass email.
        """
    
    def _create_response_classification_prompt(self, email_content: str) -> str:
        """Create prompt for email response classification."""
        return f"""
        You are an expert sales professional analyzing an email response to determine the next action.

        EMAIL CONTENT:
        {email_content}

        TASK:
        Analyze this email response and classify it into one of these categories:
        1. INTERESTED - Shows genuine interest, asks questions, wants to learn more
        2. NOT_INTERESTED - Clearly states they're not interested, no further contact
        3. NEUTRAL - Polite but non-committal, needs more information
        4. OUT_OF_OFFICE - Automated response, person unavailable
        5. NEEDS_MORE_INFO - Interested but needs specific details
        6. OBJECTION - Has concerns that need to be addressed

        FOR EACH CLASSIFICATION, PROVIDE:
        - Classification category
        - Confidence score (0-100)
        - Sentiment (positive/negative/neutral)
        - Key points mentioned
        - Urgency level (low/medium/high)
        - Recommended next action
        - Reasoning for your decision

        FORMAT YOUR RESPONSE AS JSON:
        {{
            "classification": "INTERESTED",
            "confidence_score": 85,
            "sentiment": "positive",
            "key_points": ["point 1", "point 2"],
            "urgency_level": "medium",
            "recommended_next_action": "Send detailed proposal within 24 hours",
            "reasoning": "Clear interest shown through specific questions about pricing and implementation"
        }}

        Be precise and actionable in your analysis.
        """
    
    def _create_followup_prompt(self, lead_data: LeadData, interaction_context: Dict[str, Any], 
                               sequence_step: int) -> str:
        """Create prompt for follow-up email generation."""
        return f"""
        You are an expert sales professional writing a follow-up email in a sequence. This is step {sequence_step} in the follow-up process.

        LEAD INFORMATION:
        - Name: {lead_data.name}
        - Job Title: {lead_data.job_title}
        - Company: {lead_data.company}

        PREVIOUS INTERACTIONS:
        {json.dumps(interaction_context, indent=2)}

        FOLLOW-UP STRATEGY:
        - Step {sequence_step}: {self._get_followup_strategy(sequence_step)}
        - Goal: {self._get_followup_goal(sequence_step)}
        - Tone: {self._get_followup_tone(sequence_step)}

        REQUIREMENTS:
        1. Reference previous communication naturally
        2. Provide additional value or insights
        3. Address any objections or concerns raised
        4. Include appropriate urgency based on their engagement
        5. End with a clear next step
        6. Keep it concise (max 100 words)
        7. Make it feel personal and relevant

        FORMAT YOUR RESPONSE AS JSON:
        {{
            "email_body": "Your follow-up email content",
            "subject_line": "Your follow-up subject line",
            "urgency_level": "medium",
            "value_proposition": "What value you're providing",
            "next_action": "What you want them to do next"
        }}

        Remember: Each follow-up should build on the previous interaction and move the conversation forward.
        """
    
    def _create_job_title_analysis_prompt(self, job_title: str, company: str) -> str:
        """Create prompt for job title analysis."""
        return f"""
        You are an expert business analyst specializing in organizational structures and job roles.

        ANALYZE THIS JOB TITLE:
        - Job Title: {job_title}
        - Company: {company}

        PROVIDE ANALYSIS ON:
        1. Seniority Level (Junior/Mid/Senior/Executive)
        2. Decision Authority (Low/Medium/High)
        3. Likely Pain Points (based on their role)
        4. Industry Context and Trends
        5. Personalization Opportunities
        6. Influence Level in Purchasing Decisions

        FOR EACH CATEGORY, PROVIDE:
        - Score (0-100)
        - Reasoning
        - Specific examples or insights

        FORMAT YOUR RESPONSE AS JSON:
        {{
            "seniority_level": "Senior",
            "seniority_score": 75,
            "decision_authority": "Medium",
            "decision_score": 60,
            "likely_pain_points": ["pain point 1", "pain point 2"],
            "industry_context": "Technology sector insights",
            "personalization_opportunities": ["opportunity 1", "opportunity 2"],
            "influence_level": "Medium",
            "overall_score": 70,
            "reasoning": "Detailed explanation of your analysis"
        }}

        Be specific and actionable in your analysis.
        """
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _parse_email_response(self, content: str) -> Dict[str, Any]:
        """Parse AI-generated email response."""
        try:
            if isinstance(content, str):
                # Try to parse JSON response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Fallback parsing for non-JSON responses
                    return {
                        'email_body': content,
                        'subject_line': 'Reaching out about your business',
                        'personalization_score': 0.8,
                        'pain_points_addressed': [],
                        'calendly_integration': 'Standard integration'
                    }
            return content
        except Exception as e:
            logger.error(f"Failed to parse email response: {e}")
            return {
                'email_body': content,
                'subject_line': 'Reaching out about your business',
                'personalization_score': 0.5,
                'pain_points_addressed': [],
                'calendly_integration': 'Standard integration'
            }
    
    def _parse_classification_response(self, content: str) -> Dict[str, Any]:
        """Parse AI-generated classification response."""
        try:
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return self._fallback_classification()
            return content
        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            return self._fallback_classification()
    
    def _parse_job_analysis_response(self, content: str) -> Dict[str, Any]:
        """Parse AI-generated job analysis response."""
        try:
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return self._fallback_job_analysis("Unknown", "Unknown")
            return content
        except Exception as e:
            logger.error(f"Failed to parse job analysis response: {e}")
            return self._fallback_job_analysis("Unknown", "Unknown")
    
    def _fallback_classification(self) -> Dict[str, Any]:
        """Fallback classification when AI analysis fails."""
        return {
            'classification': 'NEUTRAL',
            'confidence_score': 50,
            'sentiment': 'neutral',
            'key_points': ['Fallback analysis used'],
            'urgency_level': 'low',
            'recommended_next_action': 'Manual review required',
            'reasoning': 'AI analysis failed, manual review needed'
        }
    
    def _fallback_job_analysis(self, job_title: str, company: str) -> Dict[str, Any]:
        """Fallback job analysis when AI analysis fails."""
        return {
            'seniority_level': 'Unknown',
            'seniority_score': 50,
            'decision_authority': 'Unknown',
            'decision_score': 50,
            'likely_pain_points': ['General business challenges'],
            'industry_context': 'General business context',
            'personalization_opportunities': ['Standard personalization'],
            'influence_level': 'Unknown',
            'overall_score': 50,
            'reasoning': 'Fallback analysis due to AI failure'
        }
    
    def _analyze_interaction_context(self, previous_emails: List[Dict[str, Any]], sequence_step: int) -> Dict[str, Any]:
        """Analyze previous email interactions for context."""
        try:
            if not previous_emails:
                return {'context': 'No previous interactions', 'engagement_level': 'low'}
            
            # Analyze engagement patterns
            engagement_levels = [email.get('engagement_score', 0.5) for email in previous_emails]
            avg_engagement = sum(engagement_levels) / len(engagement_levels)
            
            # Get last interaction details
            last_email = previous_emails[-1]
            
            return {
                'context': f'Step {sequence_step-1} completed',
                'engagement_level': 'high' if avg_engagement > 0.7 else 'medium' if avg_engagement > 0.4 else 'low',
                'last_interaction': last_email.get('content', ''),
                'last_sentiment': last_email.get('sentiment', 'neutral'),
                'response_time': last_email.get('response_time', 'unknown'),
                'key_points': last_email.get('key_points', [])
            }
        except Exception as e:
            logger.error(f"Failed to analyze interaction context: {e}")
            return {'context': 'Context analysis failed', 'engagement_level': 'unknown'}
    
    def _get_followup_strategy(self, step: int) -> str:
        """Get follow-up strategy for specific step."""
        strategies = {
            1: "Value reinforcement and objection handling",
            2: "Social proof and case studies",
            3: "Urgency and limited-time offer",
            4: "Final attempt with alternative approach",
            5: "Last chance with strongest value proposition"
        }
        return strategies.get(step, "Standard follow-up approach")
    
    def _get_followup_goal(self, step: int) -> str:
        """Get follow-up goal for specific step."""
        goals = {
            1: "Address concerns and provide additional value",
            2: "Build credibility and trust",
            3: "Create urgency and encourage action",
            4: "Try different approach or angle",
            5: "Final attempt to engage or close"
        }
        return goals.get(step, "Continue engagement")
    
    def _get_followup_tone(self, step: int) -> str:
        """Get follow-up tone for specific step."""
        tones = {
            1: "Professional and helpful",
            2: "Confident and credible",
            3: "Urgent but respectful",
            4: "Creative and different",
            5: "Direct and final"
        }
        return tones.get(step, "Professional")
    
    async def _enhance_lead_scoring_with_ai(self, lead_data: LeadData) -> Dict[str, Any]:
        """Enhance ML scoring with AI analysis."""
        try:
            # Analyze job title and company
            job_analysis = await self.analyze_job_title(lead_data.job_title, lead_data.company)
            
            # Calculate AI-based scores
            decision_authority = job_analysis.get('decision_score', 50) / 100
            company_relevance = 0.7  # Placeholder for company analysis
            
            # Combine factors for AI score
            ai_score = (decision_authority * 0.4) + (company_relevance * 0.3) + (0.3)  # Base score
            
            return {
                'ai_score': ai_score,
                'decision_authority': decision_authority,
                'company_relevance': company_relevance,
                'recommendations': [
                    f"Decision authority: {decision_authority:.1%}",
                    f"Company relevance: {company_relevance:.1%}",
                    "Consider targeting higher-level decision makers if score is low"
                ]
            }
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return {
                'ai_score': 0.5,
                'decision_authority': 0.5,
                'company_relevance': 0.5,
                'recommendations': ['AI analysis failed, using fallback scores']
            }
    
    # =============================================================================
    # LEGACY METHODS (Maintained for compatibility)
    # =============================================================================
    
    async def process_lead(self, lead_data: LeadData) -> Tuple[LeadScore, AIResponse]:
        """Process a lead through the complete AI pipeline."""
        try:
            # Score the lead
            lead_score = await self.score_lead(lead_data)
            
            # Get user's Calendly link from database
            user_calendly = None
            try:
                # This would get the user's Calendly link from their profile
                # For now, we'll use a placeholder
                user_calendly = "https://calendly.com/yourusername"
            except:
                pass
            
            # Generate personalized email with Calendly integration
            user_settings = {
                'calendly_link': user_calendly,
                'include_calendly': user_calendly is not None
            }
            
            email_response = await self.generate_cold_email(lead_data, user_settings)
            
            logger.info(f"Lead processing completed: score={lead_score.score:.3f}, email_success={email_response.success}")
            return lead_score, email_response
            
        except Exception as e:
            logger.error(f"Lead processing failed: {e}")
            raise
    
    async def analyze_email_response(self, email_content: str, lead_context: Dict[str, Any] = None) -> EmailAnalysis:
        """Analyze an email response."""
        try:
            return await self.response_analysis.analyze_response(email_content, lead_context)
        except Exception as e:
            logger.error(f"Email response analysis failed: {e}")
            raise
    
    async def get_ai_insights(self, user_id: str, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get AI-generated insights for user's campaigns."""
        try:
            # Get analytics data
            analytics = await db_manager.get_user_analytics(user_id, date_range[0], date_range[1])
            
            # Process analytics for insights
            insights = {
                'total_leads': len(analytics),
                'engagement_trends': self._analyze_engagement_trends(analytics),
                'performance_metrics': self._calculate_performance_metrics(analytics),
                'recommendations': self._generate_ai_recommendations(analytics)
            }
            
            logger.info(f"AI insights generated for user {user_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            return {}
    
    def _analyze_engagement_trends(self, analytics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze engagement trends from analytics data."""
        try:
            # Placeholder for engagement trend analysis
            return {
                'trend': 'stable',
                'peak_hours': ['9:00', '14:00'],
                'best_days': ['Tuesday', 'Wednesday']
            }
        except Exception as e:
            logger.error(f"Engagement trend analysis failed: {e}")
            return {}
    
    def _calculate_performance_metrics(self, analytics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics from analytics data."""
        try:
            # Placeholder for performance metrics calculation
            return {
                'open_rate': 0.25,
                'response_rate': 0.08,
                'meeting_booked_rate': 0.02
            }
        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {e}")
            return {}
    
    def _generate_ai_recommendations(self, analytics: List[Dict[str, Any]]) -> List[str]:
        """Generate AI-powered recommendations."""
        try:
            # Placeholder for AI recommendations
            return [
                "Send emails between 9-11 AM for higher open rates",
                "Follow up within 48 hours for better response rates",
                "Personalize subject lines based on job titles"
            ]
        except Exception as e:
            logger.error(f"AI recommendations generation failed: {e}")
            return []

# Global AI engine instance
ai_engine = AIEngine()

# Export for easy access
__all__ = [
    'ai_engine', 'AIEngine', 'LeadScoringEngine', 'EmailPersonalizationEngine',
    'ResponseAnalysisEngine', 'LeadScore', 'EmailAnalysis', 'PersonalizationData'
]
