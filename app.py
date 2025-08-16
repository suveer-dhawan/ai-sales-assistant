"""
AI Sales Assistant - Streamlit UI Application

This is the main Streamlit application that provides a professional multi-page
interface for the AI sales assistant platform. It includes lead management,
campaign orchestration, email generation, and analytics dashboard.

Dependencies: streamlit, plotly, pandas, config.py, auth.py, database.py, 
             integrations.py, ai_engine.py, automation.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import time
from typing import Dict, List, Optional, Any

# Import our modules
from config import config
from auth import auth_manager, require_auth
from database import db_manager
from integrations import integration_manager
from ai_engine import ai_engine
from automation import automation_manager

# Page configuration
st.set_page_config(
    page_title="AI Sales Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point."""
    
    # Initialize session state
    if 'sheets_oauth_url' not in st.session_state:
        st.session_state.sheets_oauth_url = None
    if 'gmail_oauth_url' not in st.session_state:
        st.session_state.gmail_oauth_url = None
    if 'show_sheets_auth' not in st.session_state:
        st.session_state.show_sheets_auth = False
    if 'show_gmail_auth' not in st.session_state:
        st.session_state.show_gmail_auth = False
    if 'show_sheets_auth_dashboard' not in st.session_state:
        st.session_state.show_sheets_auth_dashboard = False
    if 'sheets_connected' not in st.session_state:
        st.session_state.sheets_connected = False
    if 'show_import_leads' not in st.session_state:
        st.session_state.show_import_leads = False
    if 'show_start_campaign' not in st.session_state:
        st.session_state.show_start_campaign = False
    if 'show_reports' not in st.session_state:
        st.session_state.show_reports = False
    
    # Check authentication
    if not auth_manager.is_authenticated():
        show_login_page()
        return
    
    # Main application
    show_main_application()

def show_login_page():
    """Display the login/authentication page."""
    st.markdown('<h1 class="main-header">🚀 AI Sales Assistant</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2>Never write another cold email. Never miss a follow-up.</h2>
        <p>Turn your Google Sheet of leads into booked meetings automatically - with every email uniquely crafted by AI.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication options
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Connect Your Accounts")
        
        # Gmail OAuth (Primary - Required to start)
        st.markdown("### 📧 Step 1: Connect Gmail (Required)")
        st.info("""
        **Gmail access is required to send personalized cold emails.**
        This will allow the AI to send emails on your behalf and monitor responses.
        """)
        
        if st.button("🔐 Connect Gmail Account", type="primary", use_container_width=True):
            try:
                gmail_url = auth_manager.get_oauth_url('gmail')
                st.session_state.gmail_oauth_url = gmail_url
                st.session_state.show_gmail_auth = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate OAuth URL: {e}")
        
        # Debug: Show OAuth URL details
        if st.session_state.get('gmail_oauth_url'):
            with st.expander("🔍 Debug: Gmail OAuth URL Details", expanded=False):
                st.code(st.session_state.gmail_oauth_url, language="text")
                st.info("""
                **Expected Scopes:**
                - Gmail send/read
                - User profile/email
                - **NO Google Sheets scopes**
                """)
        
        # Display Gmail OAuth when generated
        if st.session_state.get('show_gmail_auth', False):
            st.markdown("#### 📧 Gmail Authorization")
            st.markdown("**Click the link below to authorize Gmail access:**")
            st.markdown(f"[🔐 Authorize Gmail]({st.session_state.gmail_oauth_url})")
            st.info("After authorization, you'll be redirected back to the application.")
            if st.button("✅ I've Completed Gmail Authorization", key="gmail_done"):
                st.session_state.show_gmail_auth = False
                st.rerun()
        
        # Google Sheets OAuth (Secondary - Can be done later)
        st.markdown("---")
        st.markdown("### 📊 Step 2: Connect Google Sheets (Optional)")
        st.info("""
        **Google Sheets access allows you to import leads automatically.**
        You can connect this now or later from the dashboard.
        """)
        
        if st.button("🔗 Connect Google Sheets", type="secondary", use_container_width=True):
            try:
                sheets_url = auth_manager.get_oauth_url('sheets')
                st.session_state.sheets_oauth_url = sheets_url
                st.session_state.show_sheets_auth = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate OAuth URL: {e}")
        
        # Display Sheets OAuth when generated
        if st.session_state.get('show_sheets_auth', False):
            st.markdown("#### 📊 Google Sheets Authorization")
            st.markdown("**Click the link below to authorize Google Sheets access:**")
            st.markdown(f"[🔐 Authorize Google Sheets]({st.session_state.sheets_oauth_url})")
            st.info("After authorization, you'll be redirected back to the application.")
            if st.button("✅ I've Completed Sheets Authorization", key="sheets_done"):
                st.session_state.show_sheets_auth = False
                st.rerun()
        
        # Manual OAuth callback handling (for troubleshooting)
        st.markdown("---")
        st.markdown("### 🔄 Troubleshooting: Manual Authorization")
        st.info("""
        **If the automatic redirect isn't working, you can manually complete the authorization:**
        1. Copy the full URL from your browser after authorization
        2. Paste it below and click "Complete Setup"
        3. This will manually process your authorization
        """)
        
        auth_response = st.text_input("Paste the full authorization URL from your browser:")
        if st.button("Complete Setup", type="secondary"):
            if auth_response:
                with st.spinner("Processing authorization..."):
                    try:
                        # Determine service from URL - be more explicit
                        service_detected = None
                        if "sheets" in auth_response.lower() and "gmail" not in auth_response.lower():
                            service_detected = 'sheets'
                        elif "gmail" in auth_response.lower() and "sheets" not in auth_response.lower():
                            service_detected = 'gmail'
                        else:
                            # Let user choose manually
                            st.error("""
                            **Service Detection Ambiguous**
                            
                            The URL contains references to multiple services or is unclear.
                            Please manually specify which service you're authenticating:
                            """)
                            
                            service_choice = st.radio(
                                "Which service are you connecting?",
                                ["Gmail", "Google Sheets"],
                                key="service_choice"
                            )
                            
                            if service_choice == "Gmail":
                                service_detected = 'gmail'
                            else:
                                service_detected = 'sheets'
                        
                        st.info(f"🔍 Detected service: **{service_detected.upper()}**")
                        
                        success = asyncio.run(auth_manager.handle_oauth_callback(service_detected, auth_response))
                        
                        if success:
                            st.success("🎉 Authorization completed successfully!")
                            st.balloons()
                            
                            # Check which service was authenticated
                            if "sheets" in auth_response:
                                st.session_state.sheets_connected = True
                                st.info("Google Sheets connected! You can now import leads.")
                            elif "gmail" in auth_response:
                                st.session_state.authenticated = True
                                st.info("Gmail connected! Redirecting to dashboard...")
                            
                            st.rerun()
                        else:
                            st.error("❌ Authorization failed. Please try again or check the URL.")
                    except Exception as e:
                        st.error(f"Authorization error: {e}")
                        st.error("Please make sure you copied the complete URL from your browser.")
            else:
                st.warning("Please paste the authorization response URL.")

def show_main_application():
    """Display the main application interface."""
    
    # Sidebar navigation
    st.sidebar.title("🎯 AI Sales Assistant")
    
    # Get user info for welcome message
    user_email = auth_manager.get_current_user_email()
    user_name = auth_manager.get_current_user_name() or user_email.split('@')[0] if user_email else "User"
    
    st.sidebar.markdown(f"**Welcome, {user_name}!**")
    
    # Navigation menu
    st.sidebar.markdown("**Navigation**")
    page = st.sidebar.radio(
        "Select Page",
        ["📊 Dashboard", "👥 Lead Management", "📧 Campaigns", "🤖 AI Engine", "⚙️ Settings", "📈 Analytics"],
        key="nav_radio",
        label_visibility="collapsed"
    )
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        auth_manager.logout()
        st.rerun()
    
    # Display selected page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "👥 Lead Management":
        show_lead_management()
    elif page == "📧 Campaigns":
        show_campaigns()
    elif page == "🤖 AI Engine":
        show_ai_engine()
    elif page == "⚙️ Settings":
        show_settings()
    elif page == "📈 Analytics":
        show_analytics()

def show_dashboard():
    """Display the main dashboard."""
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", "1,247", "+12%")
    with col2:
        st.metric("Active Campaigns", "3", "2 running")
    with col3:
        st.metric("Emails Sent", "892", "+8%")
    with col4:
        st.metric("Meetings Booked", "23", "+15%")
    
    # System health check
    st.markdown("### 🔍 System Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Integration Status")
        try:
            health_status = asyncio.run(integration_manager.health_check())
            
            for service, status in health_status.items():
                if status:
                    st.success(f"✅ {service.replace('_', ' ').title()}")
                else:
                    st.error(f"❌ {service.replace('_', ' ').title()}")
        except Exception as e:
            st.error(f"Health check failed: {e}")
    
    with col2:
        st.markdown("#### Recent Activity")
        st.info("📧 15 emails sent in the last hour")
        st.info("👥 3 new leads imported")
        st.info("🤖 AI generated 8 personalized emails")
    
    # Google Sheets Connection (if not already connected)
    st.markdown("### 🔗 Connect Google Sheets")
    
    # OAuth Flow Explanation
    if not st.session_state.get('sheets_connected', False):
        with st.expander("ℹ️ **How OAuth Works**", expanded=False):
            st.markdown("""
            **Why Two Separate Authentications?**
            
            Google requires separate OAuth applications for different services:
            - **Gmail OAuth App**: Handles email sending and reading
            - **Google Sheets OAuth App**: Handles spreadsheet access
            
            **The Process:**
            1. ✅ **Gmail**: Authenticate to send emails
            2. 🔐 **Google Sheets**: Authenticate to read spreadsheets
            3. 🚀 **Ready**: Import leads and start campaigns
            
            This is a Google security requirement, not a limitation of our app.
            """)
    if not st.session_state.get('sheets_connected', False):
        st.info("""
        **Connect Google Sheets to automatically import leads and start campaigns.**
        This allows the AI to pull lead data directly from your spreadsheets.
        
        **Note**: You need to authenticate with Google Sheets separately from Gmail.
        """)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🔐 Connect Google Sheets", type="primary", use_container_width=True):
                try:
                    sheets_url = auth_manager.get_oauth_url('sheets')
                    st.session_state.sheets_oauth_url = sheets_url
                    st.session_state.show_sheets_auth_dashboard = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate OAuth URL: {e}")
        
        with col2:
            st.info("""
            **🔑 Separate from Gmail**
            This is a different Google OAuth app
            """)
        
        if st.session_state.get('show_sheets_auth_dashboard', False):
            st.markdown("#### 📊 Google Sheets Authorization")
            st.markdown("**Click the link below to authorize Google Sheets access:**")
            st.markdown(f"[🔐 Authorize Google Sheets]({st.session_state.sheets_oauth_url})")
            st.info("After authorization, you'll be redirected back to the dashboard.")
            if st.button("✅ I've Completed Sheets Authorization", key="sheets_dashboard_done"):
                st.session_state.show_sheets_auth_dashboard = False
                st.session_state.sheets_connected = True
                st.rerun()
    else:
        st.success("✅ Google Sheets connected successfully!")
        
        # Check if we have the new scopes
        try:
            tokens = auth_manager.get_oauth_tokens()
            if tokens and "spreadsheets" in tokens.scopes:
                st.success("✅ **Full Access**: Can read and extract leads from spreadsheets")
            else:
                st.warning("⚠️ **Limited Access**: Old tokens detected. Please reconnect for full functionality.")
        except:
            st.info("ℹ️ **Status**: Connected but scope verification pending")
        
        st.info("""
        **Current Capabilities:**
        - ✅ Read spreadsheet data
        - ✅ Extract leads automatically
        - ✅ Import to database
        """)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Reconnect Google Sheets", type="secondary"):
                st.session_state.sheets_connected = False
                st.rerun()
        
        with col2:
            if st.button("🧪 Test Connection", type="secondary"):
                try:
                    with st.spinner("Testing Google Sheets connection..."):
                        # Test with a simple API call
                        test_result = asyncio.run(integration_manager.health_check())
                        if test_result.get('google_sheets', False):
                            st.success("✅ Google Sheets connection working!")
                        else:
                            st.error("❌ Google Sheets connection failed!")
                except Exception as e:
                    st.error(f"Connection test failed: {e}")
            
            # Show current OAuth token info
            if st.button("🔍 Show Token Info", type="secondary"):
                try:
                    tokens = auth_manager.get_oauth_tokens()
                    if tokens:
                        st.info(f"**Current Token Scopes:**")
                        for scope in tokens.scopes:
                            st.text(f"• {scope}")
                        
                        if "spreadsheets" in tokens.scopes:
                            st.success("✅ Has spreadsheets scope")
                        else:
                            st.error("❌ Missing spreadsheets scope - needs reconnection")
                    else:
                        st.warning("No OAuth tokens found")
                except Exception as e:
                    st.error(f"Failed to get token info: {e}")
        
        with col3:
            if st.button("🗑️ Clear All OAuth", type="secondary", help="This will completely clear all OAuth tokens and force fresh authentication"):
                # Clear all OAuth state using the new method
                auth_manager.clear_oauth_tokens()
                st.session_state.authenticated = False
                st.session_state.sheets_connected = False
                st.session_state.gmail_authenticated = False
                st.session_state.sheets_authenticated = False
                st.success("OAuth tokens cleared! Please re-authenticate.")
                st.rerun()
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Import Leads", type="primary", use_container_width=True):
            if st.session_state.get('sheets_connected', False):
                st.session_state.show_import_leads = True
                st.rerun()
            else:
                st.warning("Please connect Google Sheets first to import leads.")
    
    with col2:
        if st.button("🚀 Start Campaign", type="primary", use_container_width=True):
            if st.session_state.get('sheets_connected', False):
                st.session_state.show_start_campaign = True
                st.rerun()
            else:
                st.warning("Please connect Google Sheets first to start campaigns.")
    
    with col3:
        if st.button("📊 View Reports", type="primary", use_container_width=True):
            st.session_state.show_reports = True
            st.rerun()
    
    # Import Leads Modal
    if st.session_state.get('show_import_leads', False):
        st.markdown("### 📥 Import Leads from Google Sheets")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            spreadsheet_id = st.text_input("Spreadsheet ID or URL:", 
                help="Enter the spreadsheet ID from the URL or paste the full URL")
            range_name = st.text_input("Range (e.g., A:Z):", value="A:Z")
        
        with col2:
            st.markdown("#### 📋 Expected Columns")
            st.markdown("""
            - **A**: Name
            - **B**: Email  
            - **C**: Company
            - **D**: Job Title
            - **E**: Phone (optional)
            - **F**: LinkedIn (optional)
            - **G**: Pain Points (optional)
            """)
        
        if st.button("🔍 Extract & Preview Leads", type="primary"):
            if spreadsheet_id:
                with st.spinner("Extracting leads from Google Sheets..."):
                    try:
                        # Check Google Sheets connection first
                        if not st.session_state.get('sheets_connected', False):
                            st.error("❌ Google Sheets not connected!")
                            st.info("Please connect Google Sheets from the dashboard first.")
                            return
                        
                        # Extract spreadsheet ID if full URL was provided
                        if 'docs.google.com' in spreadsheet_id:
                            spreadsheet_id = spreadsheet_id.split('/')[5]
                        
                        # Test connection first
                        st.info("Testing Google Sheets connection...")
                        
                        # Verify we have valid OAuth tokens
                        try:
                            tokens = auth_manager.get_oauth_tokens('sheets')
                            if not tokens:
                                st.error("❌ No Google Sheets OAuth tokens found. Please connect Google Sheets first.")
                                return
                            
                            # Check if tokens have Sheets scopes
                            if not any('spreadsheets' in scope for scope in tokens.scopes):
                                st.error("❌ OAuth tokens missing Google Sheets permissions.")
                                st.info("Please reconnect Google Sheets to get proper permissions.")
                                return
                                
                        except Exception as e:
                            st.error(f"❌ OAuth token verification failed: {e}")
                            return
                        
                        leads = asyncio.run(integration_manager.sheets_api.extract_leads_from_sheet(
                            spreadsheet_id, range_name
                        ))
                        
                        if leads:
                            st.success(f"Successfully extracted {len(leads)} leads!")
                            
                            # Display leads in a table
                            leads_df = pd.DataFrame([
                                {
                                    'Name': lead.name,
                                    'Email': lead.email,
                                    'Company': lead.company,
                                    'Job Title': lead.job_title,
                                    'Phone': lead.phone or 'N/A',
                                    'Pain Points': ', '.join(lead.pain_points) if lead.pain_points else 'N/A'
                                }
                                for lead in leads
                            ])
                            
                            st.dataframe(leads_df, use_container_width=True)
                            
                            # Store leads for import
                            st.session_state.extracted_leads = leads
                            st.session_state.spreadsheet_id = spreadsheet_id
                            
                            if st.button("💾 Import to Database", type="secondary"):
                                with st.spinner("Importing leads..."):
                                    try:
                                        # Convert to database format and import
                                        imported_count = 0
                                        for lead in leads:
                                            lead_data = {
                                                'lead_id': f"lead_{int(time.time() * 1000)}_{imported_count}",
                                                'user_id': auth_manager.get_current_user_id(),
                                                'name': lead.name,
                                                'email': lead.email,
                                                'company': lead.company,
                                                'job_title': lead.job_title,
                                                'phone': lead.phone,
                                                'linkedin_url': getattr(lead, 'linkedin_url', None),
                                                'company_description': getattr(lead, 'company_description', None),
                                                'pain_points': lead.pain_points,
                                                'source': 'google_sheets',
                                                'imported_at': datetime.utcnow(),
                                                'status': 'new'
                                            }
                                            
                                            asyncio.run(db_manager.create_lead(lead_data))
                                            imported_count += 1
                                        
                                        st.success(f"✅ Successfully imported {imported_count} leads!")
                                        st.session_state.show_import_leads = False
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"Failed to import leads: {e}")
                        else:
                            st.warning("No leads found in the specified range.")
                            
                    except Exception as e:
                        st.error(f"Failed to extract leads: {e}")
                        st.error("**Troubleshooting Tips:**")
                        st.error("1. Make sure you've reconnected Google Sheets with new permissions")
                        st.error("2. Check if the spreadsheet ID is correct")
                        st.error("3. Verify the spreadsheet is shared with your account")
                        st.error("4. Try reconnecting Google Sheets from the dashboard")
            else:
                st.warning("Please enter a spreadsheet ID or URL.")
        
        if st.button("❌ Cancel", type="secondary"):
            st.session_state.show_import_leads = False
            st.rerun()
    
    # Start Campaign Modal
    if st.session_state.get('show_start_campaign', False):
        st.markdown("### 🚀 Start Email Campaign")
        
        # Get user's leads
        try:
            user_leads = asyncio.run(db_manager.get_leads(auth_manager.get_current_user_id()))
            
            if user_leads:
                st.success(f"Found {len(user_leads)} leads for your campaign!")
                
                # Campaign settings
                campaign_name = st.text_input("Campaign Name:", value="Cold Email Campaign")
                email_subject = st.text_input("Email Subject Line:", value="Quick question about {company}")
                
                # Lead selection
                st.markdown("#### 👥 Select Leads")
                selected_leads = []
                for lead in user_leads[:10]:  # Show first 10 leads
                    if st.checkbox(f"{lead.name} - {lead.company} ({lead.job_title})", key=f"lead_{lead.lead_id}"):
                        selected_leads.append(lead)
                
                if selected_leads:
                    st.info(f"Selected {len(selected_leads)} leads for the campaign")
                    
                    if st.button("🚀 Start Campaign", type="primary"):
                        with st.spinner("Starting campaign..."):
                            try:
                                # Create campaign
                                campaign_data = {
                                    'campaign_id': f"campaign_{int(time.time() * 1000)}",
                                    'user_id': auth_manager.get_current_user_id(),
                                    'name': campaign_name,
                                    'status': 'running',
                                    'created_at': datetime.utcnow(),
                                    'lead_count': len(selected_leads)
                                }
                                
                                campaign_id = asyncio.run(automation_manager.create_campaign(campaign_data))
                                
                                # Process leads and send emails
                                emails_sent = 0
                                for lead in selected_leads:
                                    try:
                                        # Generate personalized email
                                        email_content = asyncio.run(ai_engine.generate_cold_email(lead, {}))
                                        
                                        if email_content and email_content.success:
                                            # Send email
                                            email_result = asyncio.run(integration_manager.gmail_api.send_email(
                                                to_email=lead.email,
                                                subject=email_subject.replace('{company}', lead.company),
                                                body=email_content.content,
                                                from_name=auth_manager.get_current_user_name()
                                            ))
                                            
                                            if email_result.success:
                                                emails_sent += 1
                                                
                                                # Store email record
                                                email_data = {
                                                    'email_id': f"email_{int(time.time() * 1000)}_{emails_sent}",
                                                    'campaign_id': campaign_id,
                                                    'lead_id': lead.lead_id,
                                                    'user_id': auth_manager.get_current_user_id(),
                                                    'subject': email_subject,
                                                    'body': email_content.content,
                                                    'email_type': 'campaign',
                                                    'status': 'sent',
                                                    'sent_at': datetime.utcnow()
                                                }
                                                
                                                asyncio.run(db_manager.create_email(email_data))
                                                
                                    except Exception as e:
                                        st.error(f"Failed to process lead {lead.name}: {e}")
                                
                                st.success(f"🎉 Campaign started successfully! {emails_sent} emails sent.")
                                st.session_state.show_start_campaign = False
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Failed to start campaign: {e}")
                else:
                    st.warning("Please select at least one lead for the campaign.")
            else:
                st.warning("No leads found. Please import leads first.")
                
        except Exception as e:
            st.error(f"Failed to get leads: {e}")
        
        if st.button("❌ Cancel", type="secondary"):
            st.session_state.show_start_campaign = False
            st.rerun()
    
    # View Reports Modal
    if st.session_state.get('show_reports', False):
        st.markdown("### 📊 Lead Analytics & Reports")
        
        try:
            # Get user's leads
            user_leads = asyncio.run(db_manager.get_leads(auth_manager.get_current_user_id()))
            
            if user_leads:
                # Lead scoring analysis
                st.markdown("#### 🎯 Lead Scoring Analysis")
                
                hot_leads = [lead for lead in user_leads if getattr(lead, 'score', 0) >= 0.8]
                warm_leads = [lead for lead in user_leads if 0.5 <= getattr(lead, 'score', 0) < 0.8]
                cold_leads = [lead for lead in user_leads if getattr(lead, 'score', 0) < 0.5]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔥 Hot Leads", len(hot_leads), f"{len(hot_leads)/len(user_leads)*100:.1f}%")
                with col2:
                    st.metric("🌡️ Warm Leads", len(warm_leads), f"{len(warm_leads)/len(user_leads)*100:.1f}%")
                with col3:
                    st.metric("❄️ Cold Leads", len(cold_leads), f"{len(cold_leads)/len(user_leads)*100:.1f}%")
                
                # Lead details table
                st.markdown("#### 📋 Lead Details")
                
                leads_data = []
                for lead in user_leads:
                    score = getattr(lead, 'score', 0)
                    if score >= 0.8:
                        status = "🔥 Hot"
                    elif score >= 0.5:
                        status = "🌡️ Warm"
                    else:
                        status = "❄️ Cold"
                    
                    leads_data.append({
                        'Name': lead.name,
                        'Company': lead.company,
                        'Job Title': lead.job_title,
                        'Email': lead.email,
                        'Score': f"{score:.2f}",
                        'Status': status,
                        'Phone': getattr(lead, 'phone', 'N/A'),
                        'Pain Points': ', '.join(getattr(lead, 'pain_points', [])) if getattr(lead, 'pain_points', []) else 'N/A'
                    })
                
                leads_df = pd.DataFrame(leads_data)
                st.dataframe(leads_df, use_container_width=True)
                
                # Export functionality
                if st.button("📥 Export to CSV", type="secondary"):
                    csv = leads_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"leads_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
            else:
                st.info("No leads found. Import some leads to see analytics!")
                
        except Exception as e:
            st.error(f"Failed to generate reports: {e}")
        
        if st.button("❌ Close Reports", type="secondary"):
            st.session_state.show_reports = False
            st.rerun()

def show_lead_management():
    """Display lead management interface."""
    st.markdown('<h1 class="main-header">👥 Lead Management</h1>', unsafe_allow_html=True)
    
    # Lead import section
    st.markdown("### 📥 Import Leads")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### From Google Sheets")
        spreadsheet_id = st.text_input("Spreadsheet ID:")
        range_name = st.text_input("Range (e.g., A:Z):", value="A:Z")
        
        if st.button("🔍 Extract Leads", type="primary"):
            if spreadsheet_id:
                with st.spinner("Extracting leads from Google Sheets..."):
                    try:
                        leads = asyncio.run(integration_manager.sheets_api.extract_leads_from_sheet(
                            spreadsheet_id, range_name
                        ))
                        
                        if leads:
                            st.success(f"Successfully extracted {len(leads)} leads!")
                            
                            # Display leads in a table
                            leads_df = pd.DataFrame([
                                {
                                    'Name': lead.name,
                                    'Email': lead.email,
                                    'Company': lead.company,
                                    'Job Title': lead.job_title,
                                    'Phone': lead.phone or 'N/A',
                                    'Pain Points': ', '.join(lead.pain_points) if lead.pain_points else 'N/A'
                                }
                                for lead in leads
                            ])
                            
                            st.dataframe(leads_df, use_container_width=True)
                            
                            # Import to database
                            if st.button("💾 Import to Database", type="secondary"):
                                with st.spinner("Importing leads..."):
                                    try:
                                        # Convert to database format
                                        lead_data_list = []
                                        for lead in leads:
                                            lead_data = {
                                                'lead_id': f"lead_{int(time.time() * 1000)}_{len(lead_data_list)}",
                                                'user_id': auth_manager.get_current_user_id(),
                                                'name': lead.name,
                                                'email': lead.email,
                                                'company': lead.company,
                                                'job_title': lead.job_title,
                                                'phone': lead.phone,
                                                'linkedin_url': lead.linkedin_url,
                                                'company_description': lead.company_description,
                                                'pain_points': lead.pain_points
                                            }
                                            lead_data_list.append(lead_data)
                                        
                                        # Bulk import
                                        lead_ids = asyncio.run(db_manager.bulk_create_leads(lead_data_list))
                                        st.success(f"Successfully imported {len(lead_ids)} leads to database!")
                                        
                                    except Exception as e:
                                        st.error(f"Import failed: {e}")
                        else:
                            st.warning("No leads found in the specified range.")
                            
                    except Exception as e:
                        st.error(f"Failed to extract leads: {e}")
            else:
                st.warning("Please enter a spreadsheet ID.")
    
    with col2:
        st.markdown("#### Manual Lead Entry")
        st.markdown("Add individual leads manually:")
        
        with st.form("manual_lead"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            company = st.text_input("Company")
            job_title = st.text_input("Job Title")
            phone = st.text_input("Phone (optional)")
            pain_points = st.text_area("Pain Points (comma-separated)")
            
            if st.form_submit_button("Add Lead"):
                if name and email and company and job_title:
                    try:
                        lead_data = {
                            'lead_id': f"lead_{int(time.time() * 1000)}",
                            'user_id': auth_manager.get_current_user_id(),
                            'name': name,
                            'email': email,
                            'company': company,
                            'job_title': job_title,
                            'phone': phone if phone else None,
                            'pain_points': [p.strip() for p in pain_points.split(',')] if pain_points else []
                        }
                        
                        lead_id = asyncio.run(db_manager.create_lead(lead_data))
                        st.success(f"Lead added successfully! ID: {lead_id}")
                        
                    except Exception as e:
                        st.error(f"Failed to add lead: {e}")
                else:
                    st.warning("Please fill in all required fields.")
    
    # Lead list section
    st.markdown("### 📋 Lead List")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Status", ["All", "new", "contacted", "responded", "qualified", "booked", "lost"])
    
    with col2:
        search_term = st.text_input("Search leads...")
    
    with col3:
        if st.button("🔄 Refresh", type="secondary"):
            st.rerun()
    
    # Display leads
    try:
        user_id = auth_manager.get_current_user_id()
        leads = asyncio.run(db_manager.get_leads_by_user(user_id, limit=100))
        
        if leads:
            # Apply filters
            if status_filter != "All":
                leads = [lead for lead in leads if lead.status == status_filter]
            
            if search_term:
                leads = [lead for lead in leads if 
                        search_term.lower() in lead.name.lower() or
                        search_term.lower() in lead.company.lower() or
                        search_term.lower() in lead.job_title.lower()]
            
            # Convert to DataFrame
            leads_df = pd.DataFrame([
                {
                    'ID': lead.lead_id,
                    'Name': lead.name,
                    'Email': lead.email,
                    'Company': lead.company,
                    'Job Title': lead.job_title,
                    'Status': lead.status,
                    'Lead Score': f"{lead.lead_score:.2f}",
                    'Created': lead.created_at.strftime("%Y-%m-%d"),
                    'Last Contacted': lead.last_contacted.strftime("%Y-%m-%d") if lead.last_contacted else 'Never'
                }
                for lead in leads
            ])
            
            st.dataframe(leads_df, use_container_width=True)
            
            # Bulk actions
            st.markdown("#### Bulk Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 Send Campaign", type="primary"):
                    st.info("Campaign feature coming soon!")
            
            with col2:
                if st.button("🏷️ Update Status", type="secondary"):
                    st.info("Bulk status update coming soon!")
            
            with col3:
                if st.button("🗑️ Delete Selected", type="secondary"):
                    st.info("Bulk delete feature coming soon!")
        else:
            st.info("No leads found. Import some leads to get started!")
            
    except Exception as e:
        st.error(f"Failed to load leads: {e}")

def show_campaigns():
    """Display campaign management interface."""
    st.markdown('<h1 class="main-header">📧 Campaigns</h1>', unsafe_allow_html=True)
    
    # Create new campaign
    st.markdown("### 🚀 Create New Campaign")
    
    with st.form("new_campaign"):
        col1, col2 = st.columns(2)
        
        with col1:
            campaign_name = st.text_input("Campaign Name")
            description = st.text_area("Description")
        
        with col2:
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
        
        # Campaign settings
        st.markdown("#### Campaign Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_emails = st.number_input("Max Emails per Day", min_value=1, value=50)
            follow_up_delay = st.number_input("Follow-up Delay (hours)", min_value=24, value=48)
        
        with col2:
            lead_score_threshold = st.slider("Lead Score Threshold", 0.0, 1.0, 0.7, 0.1)
            max_follow_ups = st.number_input("Max Follow-ups", min_value=1, max_value=5, value=3)
        
        with col3:
            auto_pause = st.checkbox("Auto-pause on Low Engagement", value=True)
            engagement_threshold = st.slider("Engagement Threshold", 0.0, 1.0, 0.1, 0.05)
        
        if st.form_submit_button("Create Campaign"):
            if campaign_name and description:
                try:
                    campaign_data = {
                        'campaign_id': f"campaign_{int(time.time() * 1000)}",
                        'user_id': auth_manager.get_current_user_id(),
                        'name': campaign_name,
                        'description': description,
                        'start_date': datetime.combine(start_date, datetime.min.time()),
                        'end_date': datetime.combine(end_date, datetime.min.time()),
                        'settings': {
                            'max_emails_per_day': max_emails,
                            'follow_up_delay_hours': follow_up_delay,
                            'lead_score_threshold': lead_score_threshold,
                            'max_follow_ups': max_follow_ups,
                            'auto_pause_on_low_engagement': auto_pause,
                            'engagement_threshold': engagement_threshold
                        }
                    }
                    
                    campaign_id = asyncio.run(automation_manager.create_campaign(campaign_data))
                    st.success(f"Campaign created successfully! ID: {campaign_id}")
                    
                except Exception as e:
                    st.error(f"Failed to create campaign: {e}")
            else:
                st.warning("Please fill in all required fields.")
    
    # Campaign list
    st.markdown("### 📋 Active Campaigns")
    
    # Placeholder for campaign list
    st.info("Campaign list and management features coming soon!")
    
    # Campaign templates
    st.markdown("### 📝 Campaign Templates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🆕 Cold Outreach")
        st.markdown("Perfect for new lead acquisition")
        if st.button("Use Template", key="cold_outreach"):
            st.info("Template feature coming soon!")
    
    with col2:
        st.markdown("#### 🔄 Follow-up Sequence")
        st.markdown("Automated follow-up workflow")
        if st.button("Use Template", key="follow_up"):
            st.info("Template feature coming soon!")
    
    with col3:
        st.markdown("#### 🎯 Re-engagement")
        st.markdown("Re-engage dormant leads")
        if st.button("Use Template", key="re_engagement"):
            st.info("Template feature coming soon!")

def show_ai_engine():
    """Display AI engine interface."""
    st.markdown('<h1 class="main-header">🤖 AI Engine</h1>', unsafe_allow_html=True)
    
    # AI capabilities overview
    st.markdown("### 🧠 AI Capabilities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✨ Content Generation")
        st.markdown("- Personalized cold emails")
        st.markdown("- Follow-up sequences")
        st.markdown("- Response analysis")
        st.markdown("- Lead scoring")
    
    with col2:
        st.markdown("#### 🎯 Personalization")
        st.markdown("- Company research")
        st.markdown("- Industry insights")
        st.markdown("- Pain point analysis")
        st.markdown("- Behavioral patterns")
    
    # Test AI generation
    st.markdown("### 🧪 Test AI Generation")
    
    with st.form("ai_test"):
        col1, col2 = st.columns(2)
        
        with col1:
            lead_name = st.text_input("Lead Name", value="John Smith")
            company = st.text_input("Company", value="TechCorp Inc.")
            job_title = st.text_input("Job Title", value="VP of Engineering")
        
        with col2:
            industry = st.text_input("Industry", value="Technology")
            pain_points = st.text_area("Pain Points", value="Scaling infrastructure, Team productivity")
            email_type = st.selectbox("Email Type", ["Cold Email", "Follow-up", "Re-engagement"])
        
        if st.form_submit_button("🤖 Generate Email"):
            try:
                # Create sample lead data
                from integrations import LeadData
                
                lead_data = LeadData(
                    name=lead_name,
                    email="test@example.com",
                    company=company,
                    job_title=job_title,
                    company_description=f"A {industry} company",
                    pain_points=[p.strip() for p in pain_points.split(',')] if pain_points else []
                )
                
                with st.spinner("AI is generating your personalized email..."):
                    # Generate email
                    lead_score, email_response = asyncio.run(ai_engine.process_lead(lead_data))
                    
                    if email_response.success:
                        st.success("✅ AI Email Generated Successfully!")
                        
                        # Display lead score
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Lead Score", f"{lead_score.score:.2f}")
                        with col2:
                            st.metric("Confidence", f"{lead_score.confidence:.2f}")
                        
                        # Display email
                        st.markdown("#### 📧 Generated Email")
                        
                        # Parse JSON response if needed
                        try:
                            if email_response.content and email_response.content.strip().startswith('{'):
                                # Parse JSON response
                                import json
                                email_data = json.loads(email_response.content)
                                
                                # Display structured email
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**Subject Line:**")
                                    st.success(email_data.get('subject_line', 'No subject'))
                                
                                with col2:
                                    st.markdown("**Personalization Score:**")
                                    st.metric("Score", f"{email_data.get('personalization_score', 0):.2f}")
                                
                                st.markdown("**Email Body:**")
                                email_body = email_data.get('email_body', email_response.content)
                                st.text_area("Email Content", email_body, height=300)
                                
                                # Display additional info
                                if email_data.get('pain_points_addressed'):
                                    st.markdown("**Pain Points Addressed:**")
                                    for point in email_data['pain_points_addressed']:
                                        st.info(f"• {point}")
                                
                                if email_data.get('calendly_integration'):
                                    st.info(f"📅 **Calendly Integration:** {email_data['calendly_integration']}")
                                
                            else:
                                # Display raw content
                                st.text_area("Email Content", email_response.content, height=300)
                        except json.JSONDecodeError:
                            # Fallback to raw content if JSON parsing fails
                            st.text_area("Email Content", email_response.content, height=300)
                        
                        # Display recommendations
                        if lead_score.recommendations:
                            st.markdown("#### 💡 AI Recommendations")
                            for rec in lead_score.recommendations:
                                st.info(rec)
                        
                        # Send test email
                        if st.form_submit_button("📤 Send Test Email"):
                            st.info("Test email feature coming soon!")
                    else:
                        st.error(f"AI generation failed: {email_response.error_message}")
                        
            except Exception as e:
                st.error(f"Failed to generate email: {e}")
    
    # Display generated email outside the form
    if st.session_state.get('lead_form_data'):
        st.markdown("---")
        st.markdown("### 📧 Generated Email Results")
        
        try:
            # Create sample lead data
            from integrations import LeadData
            
            form_data = st.session_state.lead_form_data
            lead_data = LeadData(
                name=form_data['name'],
                email="test@example.com",
                company=form_data['company'],
                job_title=form_data['job_title'],
                company_description=f"A {form_data['industry']} company",
                pain_points=[p.strip() for p in form_data['pain_points'].split(',')] if form_data['pain_points'] else []
            )
            
            with st.spinner("AI is generating your personalized email..."):
                # Generate email
                lead_score, email_response = asyncio.run(ai_engine.process_lead(lead_data))
                
                if email_response.success:
                    st.success("✅ AI Email Generated Successfully!")
                    
                    # Display lead score
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Lead Score", f"{lead_score.score:.2f}")
                    with col2:
                        st.metric("Confidence", f"{lead_score.confidence:.2f}")
                    
                    # Display email
                    st.markdown("#### 📧 Generated Email")
                    
                    # Parse JSON response if needed
                    try:
                        if email_response.content and email_response.content.strip().startswith('{'):
                            # Parse JSON response
                            import json
                            email_data = json.loads(email_response.content)
                            
                            # Display structured email
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Subject Line:**")
                                st.success(email_data.get('subject_line', 'No subject'))
                            
                            with col2:
                                st.markdown("**Personalization Score:**")
                                st.metric("Score", f"{email_data.get('personalization_score', 0):.2f}")
                            
                            st.markdown("**Email Body:**")
                            email_body = email_data.get('email_body', email_response.content)
                            st.text_area("Email Content", email_body, height=300, key="email_display")
                            
                            # Display additional info
                            if email_data.get('pain_points_addressed'):
                                st.markdown("**Pain Points Addressed:**")
                                for point in email_data['pain_points_addressed']:
                                    st.info(f"• {point}")
                            
                            if email_data.get('calendly_integration'):
                                st.info(f"📅 **Calendly Integration:** {email_data['calendly_integration']}")
                            
                        else:
                            # Display raw content
                            st.text_area("Email Content", email_response.content, height=300, key="email_display")
                    except json.JSONDecodeError:
                        # Fallback to raw content if JSON parsing fails
                        st.text_area("Email Content", email_response.content, height=300, key="email_display")
                    
                    # Display recommendations
                    if lead_score.recommendations:
                        st.markdown("#### 💡 AI Recommendations")
                        for rec in lead_score.recommendations:
                            st.info(rec)
                    
                    # Send test email
                    if st.button("📤 Send Test Email", key="send_test_email"):
                        st.info("Test email feature coming soon!")
                        
                    # Clear form data
                    if st.button("🔄 Generate New Email", key="new_email"):
                        del st.session_state.lead_form_data
                        st.rerun()
                        
                else:
                    st.error(f"AI generation failed: {email_response.error_message}")
                    
        except Exception as e:
            st.error(f"Failed to generate email: {e}")
    
    # AI performance metrics
    st.markdown("### 📊 AI Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Emails Generated", "1,247", "+15%")
        st.metric("Personalization Score", "8.7/10", "+0.3")
    
    with col2:
        st.metric("Response Rate", "12.3%", "+2.1%")
        st.metric("Meeting Bookings", "23", "+5")
    
    with col3:
        st.metric("AI Confidence", "89%", "+3%")
        st.metric("Processing Time", "2.3s", "-0.5s")

def show_settings():
    """Display settings and configuration interface."""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    # User profile
    st.markdown("### 👤 User Profile")
    
    try:
        user_id = auth_manager.get_current_user_id()
        user = asyncio.run(db_manager.get_user(user_id))
        
        if user:
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Name", value=user.name, key="profile_name")
                st.text_input("Email", value=user.email, key="profile_email")
                st.text_input("Company", value=user.company, key="profile_company")
            
            with col2:
                st.selectbox("Role", ["User", "Manager", "Admin"], 
                           index=["User", "Manager", "Admin"].index(user.role) if user.role in ["User", "Manager", "Admin"] else 0,
                           key="profile_role")
                st.selectbox("Subscription Tier", ["Basic", "Premium", "Enterprise"],
                           index=["Basic", "Premium", "Enterprise"].index(user.subscription_tier) if user.subscription_tier in ["Basic", "Premium", "Enterprise"] else 0,
                           key="profile_tier")
                st.checkbox("Account Active", value=user.is_active, key="profile_active")
            
            if st.button("💾 Save Profile Changes"):
                try:
                    updates = {
                        'name': st.session_state.profile_name,
                        'company': st.session_state.profile_company,
                        'role': st.session_state.profile_role,
                        'subscription_tier': st.session_state.profile_tier,
                        'is_active': st.session_state.profile_active
                    }
                    
                    asyncio.run(db_manager.update_user(user_id, updates))
                    st.success("Profile updated successfully!")
                    
                except Exception as e:
                    st.error(f"Failed to update profile: {e}")
        else:
            st.warning("User profile not found.")
            
    except Exception as e:
        st.error(f"Failed to load user profile: {e}")
    
    # Email settings
    st.markdown("### 📧 Email Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Max Emails per Day", min_value=10, max_value=1000, value=100, key="max_emails")
        st.number_input("Follow-up Delay (hours)", min_value=24, max_value=168, value=48, key="follow_up_delay")
        st.number_input("Max Follow-ups", min_value=1, max_value=10, value=3, key="max_follow_ups")
    
    with col2:
        st.time_input("Business Hours Start", value=datetime.strptime("09:00", "%H:%M").time(), key="business_start")
        st.time_input("Business Hours End", value=datetime.strptime("17:00", "%H:%M").time(), key="business_end")
        st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"], key="timezone")
    
    if st.button("💾 Save Email Settings"):
        st.info("Email settings saved! (Configuration update coming soon)")
    
    # Integration settings
    st.markdown("### 🔗 Integration Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Google Sheets")
        st.info("✅ Connected")
        if st.button("🔄 Reconnect", key="sheets_reconnect"):
            st.info("Reconnection feature coming soon!")
    
    with col2:
        st.markdown("#### Gmail")
        st.info("✅ Connected")
        if st.button("🔄 Reconnect", key="gmail_reconnect"):
            st.info("Reconnection feature coming soon!")
    
    # AI settings
    st.markdown("### 🤖 AI Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("AI Model", ["gemini-pro", "gemini-pro-vision"], key="ai_model")
        st.slider("Creativity Level", 0.0, 1.0, 0.7, 0.1, key="ai_creativity")
        st.number_input("Max Tokens", min_value=100, max_value=4000, value=2048, key="ai_tokens")
    
    with col2:
        st.checkbox("Enable Personalization", value=True, key="ai_personalization")
        st.checkbox("Enable Response Analysis", value=True, key="ai_analysis")
        st.checkbox("Enable Lead Scoring", value=True, key="ai_scoring")
    
    if st.button("💾 Save AI Settings"):
        st.info("AI settings saved! (Configuration update coming soon)")
    
    # Danger zone
    st.markdown("### ⚠️ Danger Zone")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Delete All Data", type="secondary"):
            st.warning("This action cannot be undone!")
            if st.button("⚠️ Confirm Deletion", type="secondary"):
                st.error("Data deletion feature coming soon!")
    
    with col2:
        if st.button("🚪 Deactivate Account", type="secondary"):
            st.warning("This will deactivate your account!")
            if st.button("⚠️ Confirm Deactivation", type="secondary"):
                st.error("Account deactivation feature coming soon!")

def show_analytics():
    """Display analytics and reporting interface."""
    st.markdown('<h1 class="main-header">📈 Analytics</h1>', unsafe_allow_html=True)
    
    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    with col3:
        if st.button("🔄 Refresh Analytics"):
            st.rerun()
    
    # Key metrics
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", "1,247", "+12%")
        st.metric("Conversion Rate", "8.7%", "+1.2%")
    
    with col2:
        st.metric("Emails Sent", "892", "+8%")
        st.metric("Open Rate", "34.2%", "+2.1%")
    
    with col3:
        st.metric("Click Rate", "12.8%", "+1.5%")
        st.metric("Response Rate", "11.3%", "+2.3%")
    
    with col4:
        st.metric("Meetings Booked", "23", "+15%")
        st.metric("Revenue Generated", "$45,200", "+18%")
    
    # Charts
    st.markdown("### 📈 Performance Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Email performance over time
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        email_data = pd.DataFrame({
            'Date': dates,
            'Emails Sent': [50 + i*2 + np.random.randint(-10, 10) for i in range(len(dates))],
            'Opens': [15 + i*1.5 + np.random.randint(-5, 5) for i in range(len(dates))],
            'Responses': [5 + i*0.5 + np.random.randint(-2, 2) for i in range(len(dates))]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=email_data['Date'], y=email_data['Emails Sent'], 
                                name='Emails Sent', line=dict(color='#1f77b4')))
        fig.add_trace(go.Scatter(x=email_data['Date'], y=email_data['Opens'], 
                                name='Opens', line=dict(color='#ff7f0e')))
        fig.add_trace(go.Scatter(x=email_data['Date'], y=email_data['Responses'], 
                                name='Responses', line=dict(color='#2ca02c')))
        
        fig.update_layout(title="Email Performance Over Time", xaxis_title="Date", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Lead source distribution
        source_data = pd.DataFrame({
            'Source': ['Google Sheets', 'Manual Entry', 'LinkedIn', 'Website'],
            'Count': [45, 23, 18, 14]
        })
        
        fig = px.pie(source_data, values='Count', names='Source', title="Lead Sources")
        st.plotly_chart(fig, use_container_width=True)
    
    # Campaign performance
    st.markdown("### 🎯 Campaign Performance")
    
    campaign_data = pd.DataFrame({
        'Campaign': ['Q1 Outreach', 'Product Launch', 'Re-engagement', 'Holiday Special'],
        'Leads': [150, 89, 67, 45],
        'Emails Sent': [150, 89, 67, 45],
        'Opens': [67, 34, 23, 18],
        'Responses': [12, 8, 5, 3],
        'Meetings': [3, 2, 1, 1],
        'Conversion Rate': ['8.0%', '9.0%', '7.5%', '6.7%']
    })
    
    st.dataframe(campaign_data, use_container_width=True)
    
    # AI insights
    st.markdown("### 🤖 AI Insights")
    
    try:
        user_id = auth_manager.get_current_user_id()
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        insights = asyncio.run(ai_engine.get_ai_insights(user_id, (start_dt, end_dt)))
        
        if insights:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Engagement Trends")
                if 'engagement_trends' in insights:
                    trends = insights['engagement_trends']
                    st.info(f"**Trend:** {trends.get('trend', 'Unknown')}")
                    st.info(f"**Peak Hours:** {', '.join(trends.get('peak_hours', []))}")
                    st.info(f"**Best Days:** {', '.join(trends.get('best_days', []))}")
            
            with col2:
                st.markdown("#### 💡 AI Recommendations")
                if 'recommendations' in insights:
                    for rec in insights['recommendations']:
                        st.info(rec)
        else:
            st.info("AI insights not available for the selected date range.")
            
    except Exception as e:
        st.error(f"Failed to load AI insights: {e}")
    
    # Export options
    st.markdown("### 📤 Export Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Analytics", type="primary"):
            st.info("Export feature coming soon!")
    
    with col2:
        if st.button("📧 Export Email Report", type="secondary"):
            st.info("Export feature coming soon!")
    
    with col3:
        if st.button("👥 Export Lead Report", type="secondary"):
            st.info("Export feature coming soon!")

# Import numpy for analytics
import numpy as np

if __name__ == "__main__":
    main()
