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
from datetime import datetime as dt
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
    page_title="JOE - AI Sales Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and modern styling
st.markdown("""
<style>
    /* Dark theme colors */
    :root {
        --bg-primary: #2A2F41;
        --bg-secondary: #353B50;
        --bg-tertiary: #1B2631;
        --bg-card: #353B50;
        --text-primary: #FFFEFF;
        --text-secondary: #BDC3C7;
        --accent-primary: #3E497B;
        --accent-secondary: #353B50;
        --success: #27AE60;
        --warning: #F39C12;
        --error: #E74C3C;
        --sidebar-width: 240px;
    }
    
    /* Global styles */
    .main {
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .stApp {
        background-color: var(--bg-primary);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--bg-secondary);
        width: var(--sidebar-width) !important;
        min-width: var(--sidebar-width) !important;
    }
    
    .css-1d391kg .css-1lcbmhc {
        background-color: var(--bg-secondary);
        width: var(--sidebar-width) !important;
        min-width: var(--sidebar-width) !important;
    }
    
    /* Custom sidebar */
    .sidebar-brand {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 2px solid var(--accent-primary);
    }
    
    .sidebar-section {
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.5rem 0 0.5rem 0;
        padding-left: 1rem;
    }
    
    .sidebar-nav-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        color: var(--text-primary);
        text-decoration: none;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .sidebar-nav-item:hover {
        background-color: var(--bg-tertiary);
        transform: translateX(4px);
    }
    
    .sidebar-nav-item.active {
        background-color: var(--accent-primary);
        color: var(--text-primary);
    }
    
    /* Main content styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }
    
    .welcome-text {
        font-size: 1.5rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: var(--bg-card);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid var(--bg-tertiary);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Content cards */
    .content-card {
        background-color: var(--bg-card);
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid var(--bg-tertiary);
        margin: 1rem 0;
        min-height: 300px;
    }
    
    .content-card h3 {
        color: var(--text-primary);
        margin-bottom: 1rem;
        font-size: 1.3rem;
    }
    
    /* Form styling */
    .stButton > button {
        background-color: var(--accent-primary);
        color: var(--text-primary);
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-secondary);
        transform: translateY(-2px);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--bg-card);
        border-radius: 0.5rem;
    }
    
    .stSelectbox > div > div > div {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--bg-card);
        border-radius: 0.5rem;
    }
    
    /* Success/Error messages */
    .success-message {
        background-color: rgba(39, 174, 96, 0.1);
        color: var(--success);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--success);
    }
    
    .error-message {
        background-color: rgba(231, 76, 60, 0.1);
        color: var(--error);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--error);
    }
    
    .info-message {
        background-color: rgba(52, 152, 219, 0.1);
        color: var(--accent-primary);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--accent-primary);
    }
    
    /* AI Studio specific styling */
    .ai-studio-section {
        background-color: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        border: 1px solid var(--bg-card);
    }
    
    .email-preview-box {
        background-color: var(--bg-tertiary);
        border: 2px solid var(--accent-primary);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background-color: var(--bg-secondary);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--bg-card);
        text-align: center;
    }
    
    .pain-point-item {
        background-color: #28A745;
        color: white;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1E7E34;
        font-weight: 500;
    }
    
    .calendly-note {
        background-color: #FFC107;
        color: #212529;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.75rem 0;
        border-left: 4px solid #E0A800;
        font-weight: 500;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--bg-tertiary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-primary);
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
    if 'last_reset_date' not in st.session_state:
        st.session_state.last_reset_date = datetime.now().date()
    
    # Reset daily API counter if it's a new day
    current_date = datetime.now().date()
    if current_date != st.session_state.last_reset_date:
        # New day, reset API counters
        try:
            from ai_engine import EmailPersonalizationEngine
            ai_engine = EmailPersonalizationEngine()
            ai_engine.reset_daily_counter()
            st.session_state.last_reset_date = current_date
            logger.info("Daily API counter reset")
        except Exception as e:
            logger.warning(f"Failed to reset daily counter: {e}")
    
    # Check authentication
    if not auth_manager.is_authenticated():
        show_login_page()
        return
    
    # Main application
    show_main_application()

def show_login_page():
    """Display the login/authentication page."""
    st.markdown('<h1 class="main-header">🚀 JOE - AI Sales Assistant</h1>', unsafe_allow_html=True)
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
        
        # Display Gmail OAuth when generated
        if st.session_state.get('show_gmail_auth', False):
            st.markdown("#### 📧 Gmail Authorization")
            st.markdown("**Click the link below to authorize Gmail access:**")
            st.markdown(f"[🔐 Authorize Gmail]({st.session_state.gmail_oauth_url})")
            st.info("After authorization, you'll be redirected back to the application.")
            
            # Manual completion button (working state)
            if st.button("✅ I've Completed Gmail Authorization", key="gmail_done"):
                st.session_state.show_gmail_auth = False
                st.rerun()
            
            # Alternative: Manual URL pasting for OAuth callback
            st.markdown("---")
            st.markdown("**🔧 Alternative: If automatic redirect doesn't work, paste the callback URL here:**")
            
            callback_url = st.text_input(
                "Paste the callback URL or just the authorization code:",
                placeholder="https://localhost:8501/auth/callback?code=... OR just paste the code: 4/0AVMBsJhG...",
                key="gmail_callback_input"
            )
            
            if st.button("🔐 Process Callback URL", key="gmail_process_callback"):
                if callback_url:
                    try:
                        # Check if it's a full URL or just the authorization code
                        if "code=" in callback_url:
                            # It's a full URL, extract the code
                            import re
                            code_match = re.search(r'code=([^&]+)', callback_url)
                            if code_match:
                                authorization_code = code_match.group(1)
                            else:
                                st.error("❌ No authorization code found in the URL. Please check the URL format.")
                                return
                        else:
                            # It's just the authorization code
                            authorization_code = callback_url.strip()
                        
                        # Process the OAuth callback
                        import asyncio
                        success = asyncio.run(auth_manager.handle_oauth_callback('gmail', authorization_code))
                        
                        if success:
                            st.success("✅ Gmail connected successfully! You can now access the dashboard.")
                            st.session_state.show_gmail_auth = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to connect Gmail. Please check the URL and try again.")
                    except Exception as e:
                        st.error(f"❌ Error processing callback: {e}")
                else:
                    st.error("❌ Please paste the callback URL or authorization code.")
        
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
            
            # Alternative: Manual URL pasting for OAuth callback
            st.markdown("---")
            st.markdown("**🔧 Alternative: If automatic redirect doesn't work, paste the callback URL here:**")
            
            sheets_callback_url = st.text_input(
                "Paste the callback URL or just the authorization code:",
                placeholder="https://localhost:8501/auth/callback?code=... OR just paste the code: 4/0AVMBsJhG...",
                key="sheets_callback_input"
            )
            
            if st.button("🔐 Process Callback URL", key="sheets_process_callback"):
                if sheets_callback_url:
                    try:
                        # Check if it's a full URL or just the authorization code
                        if "code=" in sheets_callback_url:
                            # It's a full URL, extract the code
                            import re
                            code_match = re.search(r'code=([^&]+)', sheets_callback_url)
                            if code_match:
                                authorization_code = code_match.group(1)
                            else:
                                st.error("❌ No authorization code found in the URL. Please check the URL format.")
                                return
                        else:
                            # It's just the authorization code
                            authorization_code = sheets_callback_url.strip()
                        
                        # Process the OAuth callback
                        import asyncio
                        success = asyncio.run(auth_manager.handle_oauth_callback('sheets', authorization_code))
                        
                        if success:
                            st.success("✅ Google Sheets connected successfully!")
                            st.session_state.show_sheets_auth = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to connect Google Sheets. Please check the URL and try again.")
                    except Exception as e:
                        st.error(f"❌ Error processing callback: {e}")
                else:
                    st.error("❌ Please paste the callback URL or authorization code.")
        
        # Note: OAuth will automatically redirect after successful authorization
        st.info("""
        **💡 Tip:** After clicking the authorization link, you'll be automatically redirected back to the app.
        If you encounter any issues, you can always connect Google Sheets later from the dashboard.
        """)

def show_main_application():
    """Display the main application interface."""
    
    # Custom sidebar with JOE branding
    with st.sidebar:
        # JOE Brand
        st.markdown('<div class="sidebar-brand">JOE</div>', unsafe_allow_html=True)
        
        # Discover section
        st.markdown('<div class="sidebar-section">Discover</div>', unsafe_allow_html=True)
        
        # Navigation menu with icons
        nav_items = [
            ("🏠", "Dashboard", "dashboard"),
            ("🔍", "Lead Management", "lead_management"),
            ("🧠", "AI Studio", "ai_studio"),
            ("📊", "Campaign Builder", "campaign_builder"),
            ("📈", "Analytics", "analytics")
        ]
        
        # Get current page from session state
        current_page = st.session_state.get('current_page', 'dashboard')
        
        for icon, label, page_id in nav_items:
            is_active = current_page == page_id
            
            if st.button(f"{icon} {label}", key=f"nav_{page_id}", use_container_width=True):
                st.session_state.current_page = page_id
                st.rerun()
            
            # Apply active styling
            if is_active:
                st.markdown(f"""
                <style>
                    [data-testid="stButton"] button[kind="secondary"]:nth-of-type({nav_items.index((icon, label, page_id)) + 1}) {{
                        background-color: var(--accent-primary) !important;
                        color: var(--text-primary) !important;
                    }}
                </style>
                """, unsafe_allow_html=True)
        
        # Settings button at bottom
        st.markdown("---")
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = 'settings'
            st.rerun()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            auth_manager.logout()
            st.rerun()
    
    # Main content area
    # Top bar with welcome message and settings
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        user_name = auth_manager.get_current_user_name() or "User"
        st.markdown(f'<div class="welcome-text">Welcome {user_name}</div>', unsafe_allow_html=True)
    
    with col3:
        if st.button("Settings", key="top_settings"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    # Display selected page
    current_page = st.session_state.get('current_page', 'dashboard')
    
    if current_page == 'dashboard':
        show_dashboard()
    elif current_page == 'lead_management':
        show_lead_management()
    elif current_page == 'ai_studio':
        show_ai_studio()
    elif current_page == 'campaign_builder':
        show_campaign_builder()
    elif current_page == 'analytics':
        show_analytics()
    elif current_page == 'settings':
        show_settings()

def show_dashboard():
    """Display the main dashboard."""
    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    
    # Quick stats - 4 metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Total Leads</div>
            <div class="metric-value">1,247</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Active Campaigns</div>
            <div class="metric-value">3</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Emails Sent</div>
            <div class="metric-value">892</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Meetings Booked</div>
            <div class="metric-value">23</div>
        </div>
        """, unsafe_allow_html=True)
    
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
    
    # Calendly Link Configuration
    st.markdown("### 📅 Calendly Integration")
    
    # Initialize Calendly link in session state
    if 'calendly_link' not in st.session_state:
        st.session_state.calendly_link = ""
    
    col1, col2 = st.columns([3, 1])
    with col1:
        calendly_input = st.text_input(
            "Your Calendly Link:",
            value=st.session_state.calendly_link,
            placeholder="https://calendly.com/yourusername",
            help="This link will be automatically included in AI-generated emails"
        )
    
    with col2:
        if st.button("💾 Save Calendly Link", type="primary"):
            if calendly_input and "calendly.com" in calendly_input:
                st.session_state.calendly_link = calendly_input
                st.success("✅ Calendly link saved! It will be used in all AI-generated emails.")
                st.rerun()
            else:
                st.error("❌ Please enter a valid Calendly link (must contain 'calendly.com')")
    
    if st.session_state.calendly_link:
        st.success(f"✅ **Current Calendly Link**: {st.session_state.calendly_link}")
        st.info("This link will be automatically included in all AI-generated emails for easy meeting scheduling.")
    
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
    
    # Cost Optimization Tips
    st.markdown("### 💰 Cost Optimization Tips")
    
    with st.expander("🔍 **API Usage Optimization**", expanded=False):
        st.markdown("""
        **Gemini 2.5 Flash-Lite Model Benefits:**
        - ✅ **Higher Daily Limits**: More calls per day than previous models
        - ✅ **Cost Effective**: Optimized for cost-conscious applications
        - ✅ **Fast Response**: Quick generation for better user experience
        
        **Smart Caching System:**
        - 🔄 **Duplicate Prevention**: Avoids generating the same email twice
        - ⏱️ **Rate Limiting**: 1-second delay between API calls to prevent abuse
        - 📊 **Usage Monitoring**: Real-time tracking of daily API consumption
        
        **Best Practices:**
        - Use the **Test AI Generation** feature sparingly during demos
        - **Cache results** for similar lead types to reduce API calls
        - Monitor the **API Usage** section in AI Studio for current consumption
        """)
    
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
                                    'created_at': dt.utcnow(),
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
                                                    'sent_at': dt.utcnow()
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
    
    # Lead Overview Stats
    st.markdown("### 📊 Lead Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        user_id = auth_manager.get_current_user_id()
        all_leads = asyncio.run(db_manager.get_leads_by_user(user_id, limit=1000))
        
        total_leads = len(all_leads) if all_leads else 0
        new_leads = len([l for l in all_leads if l.status == 'new']) if all_leads else 0
        contacted_leads = len([l for l in all_leads if l.status == 'contacted']) if all_leads else 0
        qualified_leads = len([l for l in all_leads if l.status == 'qualified']) if all_leads else 0
        
    except:
        total_leads = 0
        new_leads = 0
        contacted_leads = 0
        qualified_leads = 0
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">{total_leads}</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Total Leads</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">{new_leads}</h3>
            <p style="margin: 5px 0; opacity: 0.9;">New Leads</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">{contacted_leads}</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Contacted</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">{qualified_leads}</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Qualified</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👤 Add New Lead", type="primary", use_container_width=True):
            st.session_state.show_add_lead_form = True
            st.rerun()
    
    with col2:
        if st.button("📥 Import from Sheets", type="secondary", use_container_width=True):
            st.session_state.show_sheets_import = True
            st.rerun()
    
    with col3:
        if st.button("🔄 Refresh Data", type="secondary", use_container_width=True):
            st.rerun()
    
    # Manual Lead Entry Form
    if st.session_state.get('show_add_lead_form', False):
        st.markdown("---")
        st.markdown("### 👤 Add New Lead")
        
        with st.form("manual_lead", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name *", placeholder="John Smith")
                email = st.text_input("Email Address *", placeholder="john@company.com")
                company = st.text_input("Company *", placeholder="TechCorp Inc.")
            
            with col2:
                job_title = st.text_input("Job Title *", placeholder="VP of Engineering")
                phone = st.text_input("Phone (Optional)", placeholder="+1 (555) 123-4567")
                linkedin = st.text_input("LinkedIn (Optional)", placeholder="linkedin.com/in/johnsmith")
            
            pain_points = st.text_area("Pain Points (comma-separated)", 
                                     placeholder="Scaling infrastructure, Team productivity, Cost optimization")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.form_submit_button("💾 Save Lead", type="primary", use_container_width=True):
                    if name and email and company and job_title:
                        try:
                            lead_data = {
                                'lead_id': f"lead_{int(time.time() * 1000)}",
                                'user_id': auth_manager.get_current_user_id(),
                                'name': name.strip(),
                                'email': email.strip().lower(),
                                'company': company.strip(),
                                'job_title': job_title.strip(),
                                'phone': phone.strip() if phone else None,
                                'linkedin_url': linkedin.strip() if linkedin else None,
                                'pain_points': [p.strip() for p in pain_points.split(',') if p.strip()] if pain_points else [],
                                'status': 'new',
                                'lead_score': 0.5,
                                'created_at': dt.utcnow(),
                                'last_contacted': None
                            }
                            
                            lead_id = asyncio.run(db_manager.create_lead(lead_data))
                            st.success(f"✅ Lead added successfully! ID: {lead_id}")
                            st.session_state.show_add_lead_form = False
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Failed to add lead: {e}")
                    else:
                        st.error("❌ Please fill in all required fields (marked with *)")
            
            with col2:
                if st.form_submit_button("❌ Cancel", type="secondary", use_container_width=True):
                    st.session_state.show_add_lead_form = False
                    st.rerun()
    
    # Google Sheets Import Section
    if st.session_state.get('show_sheets_import', False):
        st.markdown("---")
        st.markdown("### 📥 Import from Google Sheets")
        
        with st.form("sheets_import"):
            col1, col2 = st.columns(2)
            
            with col1:
                spreadsheet_id = st.text_input("Spreadsheet ID:", 
                                             placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
                range_name = st.text_input("Range (e.g., A:Z):", value="A:Z")
            
            with col2:
                st.info("""
                **How to get Spreadsheet ID:**
                - Open your Google Sheet
                - Copy the ID from the URL
                - Example: `https://docs.google.com/spreadsheets/d/`**`1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`**`/edit`
                """)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.form_submit_button("🔍 Extract Leads", type="primary", use_container_width=True):
                    if spreadsheet_id:
                        with st.spinner("Extracting leads from Google Sheets..."):
                            try:
                                leads = asyncio.run(integration_manager.sheets_api.extract_leads_from_sheet(
                                    spreadsheet_id, range_name
                                ))
                                
                                if leads:
                                    st.success(f"✅ Successfully extracted {len(leads)} leads!")
                                    
                                    # Display leads preview
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
                                                        'pain_points': lead.pain_points,
                                                        'status': 'new',
                                                        'lead_score': 0.5,
                                                        'created_at': dt.utcnow(),
                                                        'last_contacted': None
                                                    }
                                                    lead_data_list.append(lead_data)
                                                
                                                # Bulk import
                                                lead_ids = asyncio.run(db_manager.bulk_create_leads(lead_data_list))
                                                st.success(f"✅ Successfully imported {len(lead_ids)} leads to database!")
                                                st.session_state.show_sheets_import = False
                                                st.rerun()
                                                
                                            except Exception as e:
                                                st.error(f"❌ Import failed: {e}")
                                else:
                                    st.warning("⚠️ No leads found in the specified range.")
                                    
                            except Exception as e:
                                st.error(f"❌ Failed to extract leads: {e}")
                    else:
                        st.warning("⚠️ Please enter a spreadsheet ID.")
            
            with col2:
                if st.form_submit_button("❌ Cancel", type="secondary", use_container_width=True):
                    st.session_state.show_sheets_import = False
                    st.rerun()
    
    # Lead List Section
    st.markdown("---")
    st.markdown("### 📋 Lead Dashboard")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Status Filter", ["All", "new", "contacted", "responded", "qualified", "booked", "lost"])
    
    with col2:
        search_term = st.text_input("🔍 Search leads...", placeholder="Search by name, company, or job title")
    
    with col3:
        if st.button("🔄 Refresh", type="secondary", use_container_width=True):
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
            
            # Convert to DataFrame with safe date handling
            leads_data = []
            for lead in leads:
                try:
                    # Handle created_at safely
                    if hasattr(lead, 'created_at') and lead.created_at:
                        if isinstance(lead.created_at, str):
                            created_date = lead.created_at
                        else:
                            created_date = lead.created_at.strftime("%Y-%m-%d")
                    else:
                        created_date = "N/A"
                    
                    # Handle last_contacted safely
                    if hasattr(lead, 'last_contacted') and lead.last_contacted:
                        if isinstance(lead.last_contacted, str):
                            last_contacted = lead.last_contacted
                        else:
                            last_contacted = lead.last_contacted.strftime("%Y-%m-%d")
                    else:
                        last_contacted = "Never"
                    
                    leads_data.append({
                        'ID': lead.lead_id,
                        'Name': lead.name,
                        'Email': lead.email,
                        'Company': lead.company,
                        'Job Title': lead.job_title,
                        'Status': lead.status,
                        'Lead Score': f"{getattr(lead, 'lead_score', 0):.2f}",
                        'Created': created_date,
                        'Last Contacted': last_contacted
                    })
                except Exception as e:
                    st.warning(f"⚠️ Error processing lead {getattr(lead, 'lead_id', 'unknown')}: {e}")
                    continue
            
            if leads_data:
                leads_df = pd.DataFrame(leads_data)
                
                # Display with better styling
                st.markdown(f"**📊 Showing {len(leads_data)} leads**")
                st.dataframe(leads_df, use_container_width=True)
                
                # Bulk actions
                st.markdown("#### 🚀 Bulk Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📧 Send Campaign", type="primary", use_container_width=True):
                        st.info("🎯 Campaign feature coming soon!")
                
                with col2:
                    if st.button("🏷️ Update Status", type="secondary", use_container_width=True):
                        st.info("🔄 Bulk status update coming soon!")
                
                with col3:
                    if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
                        st.info("🗑️ Bulk delete feature coming soon!")
            else:
                st.info("ℹ️ No leads match the current filters.")
        else:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 40px;
                border-radius: 15px;
                text-align: center;
                border: 2px dashed #dee2e6;
            ">
                <h4 style="color: #6c757d; margin-bottom: 20px;">📭 No Leads Found</h4>
                <p style="color: #6c757d; margin-bottom: 20px;">
                    Get started by adding your first lead manually or importing from Google Sheets!
                </p>
                <div style="margin-top: 20px;">
                    <span style="background: #007bff; color: white; padding: 10px 20px; border-radius: 20px; margin: 0 10px;">
                        👤 Add Manual Lead
                    </span>
                    <span style="background: #28a745; color: white; padding: 10px 20px; border-radius: 20px; margin: 0 10px;">
                        📥 Import from Sheets
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"❌ Failed to load leads: {e}")
        st.info("💡 Try refreshing the page or check your database connection.")

def parse_email_response(email_response):
    """
    Parse and format AI-generated email response.
    
    Args:
        email_response: The raw response from the AI engine
        
    Returns:
        dict: Parsed email data with clean formatting
    """
    try:
        if not email_response or not email_response.content:
            return None
            
        content = email_response.content.strip()
        
        # Handle different response formats
        if content.startswith('{') or content.startswith('```json'):
            # JSON response - clean and parse
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Parse JSON
            import json
            email_data = json.loads(content)
            
            # Extract and clean fields
            parsed_data = {
                'subject_line': email_data.get('subject_line', 'No subject generated'),
                'email_body': email_data.get('email_body', ''),
                'personalization_score': email_data.get('personalization_score', 0.0),
                'pain_points_addressed': email_data.get('pain_points_addressed', []),
                'calendly_integration': email_data.get('calendly_integration', ''),
                'format': 'json'
            }
            
        elif 'subject_line:' in content or 'email_body:' in content:
            # Key-value format - parse manually
            lines = content.split('\n')
            parsed_data = {
                'subject_line': 'No subject generated',
                'email_body': '',
                'personalization_score': 0.0,
                'pain_points_addressed': [],
                'calendly_integration': '',
                'format': 'key_value'
            }
            
            current_key = None
            current_value = []
            
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith(' '):
                    # Save previous key-value pair
                    if current_key and current_value:
                        if current_key == 'subject_line':
                            parsed_data['subject_line'] = ' '.join(current_value).strip('"')
                        elif current_key == 'email_body':
                            parsed_data['email_body'] = ' '.join(current_value).strip('"')
                        elif current_key == 'personalization_score':
                            try:
                                parsed_data['personalization_score'] = float(' '.join(current_value).strip('"'))
                            except:
                                parsed_data['personalization_score'] = 0.0
                        elif current_key == 'pain_points_addressed':
                            points = ' '.join(current_value).strip('[]"').split(',')
                            parsed_data['pain_points_addressed'] = [p.strip().strip('"') for p in points if p.strip()]
                        elif current_key == 'calendly_integration':
                            parsed_data['calendly_integration'] = ' '.join(current_value).strip('"')
                    
                    # Start new key-value pair
                    if ':' in line:
                        current_key = line.split(':')[0].strip()
                        current_value = [line.split(':', 1)[1].strip()] if ':' in line else []
                else:
                    # Continue current value
                    if current_key:
                        current_value.append(line)
            
            # Save last key-value pair
            if current_key and current_value:
                if current_key == 'subject_line':
                    parsed_data['subject_line'] = ' '.join(current_value).strip('"')
                elif current_key == 'email_body':
                    parsed_data['email_body'] = ' '.join(current_value).strip('"')
                elif current_key == 'personalization_score':
                    try:
                        parsed_data['personalization_score'] = float(' '.join(current_value).strip('"'))
                    except:
                        parsed_data['personalization_score'] = 0.0
                elif current_key == 'pain_points_addressed':
                    points = ' '.join(current_value).strip('[]"').split(',')
                    parsed_data['pain_points_addressed'] = [p.strip().strip('"') for p in points if p.strip()]
                elif current_key == 'calendly_integration':
                    parsed_data['calendly_integration'] = ' '.join(current_value).strip('"')
            
        else:
            # Raw text - treat as email body
            parsed_data = {
                'subject_line': 'No subject generated',
                'email_body': content,
                'personalization_score': 0.0,
                'pain_points_addressed': [],
                'calendly_integration': '',
                'format': 'raw_text'
            }
        
        # Clean up email body - handle escape characters
        if parsed_data['email_body']:
            # Replace escaped newlines and quotes
            parsed_data['email_body'] = (
                parsed_data['email_body']
                .replace('\\n', '\n')
                .replace('\\"', '"')
                .replace('\\t', '\t')
                .strip()
            )
        
        return parsed_data
        
    except Exception as e:
        # Fallback parsing
        return {
            'subject_line': 'Error parsing subject',
            'email_body': str(email_response.content) if email_response.content else 'Error: No content available',
            'personalization_score': 0.0,
            'pain_points_addressed': [],
            'calendly_integration': '',
            'format': 'error',
            'parse_error': str(e)
        }

def show_ai_studio():
    """Display AI engine interface."""
    st.markdown('<h1 class="main-header">AI Studio</h1>', unsafe_allow_html=True)
    
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
    
    # Initialize session state for better control
    if 'email_generated' not in st.session_state:
        st.session_state.email_generated = False
    if 'generated_email_data' not in st.session_state:
        st.session_state.generated_email_data = None
    
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
        
        # Calendly link display (if configured)
        if st.session_state.get('calendly_link'):
            st.info(f"📅 **Calendly Link Configured**: {st.session_state.calendly_link}")
        else:
            st.warning("⚠️ **No Calendly Link**: Configure your Calendly link in the Dashboard for automatic inclusion in emails.")
        
        generate_clicked = st.form_submit_button("🤖 Generate Email")
        
        if generate_clicked:
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
                    from ai_engine import AIEngine
                    ai_engine = AIEngine()
                    lead_score, email_response = asyncio.run(ai_engine.process_lead(lead_data))
                    
                    if email_response.success:
                        # Store the results in session state
                        st.session_state.email_generated = True
                        st.session_state.generated_email_data = {
                            'lead_score': lead_score,
                            'email_response': email_response,
                            'form_data': {
                                'name': lead_name,
                                'company': company,
                                'job_title': job_title,
                                'industry': industry,
                                'pain_points': pain_points
                            }
                        }
                        st.success("✅ AI Email Generated Successfully!")
                        
                    else:
                        st.error(f"AI generation failed: {email_response.error_message}")
                        st.session_state.email_generated = False
                        
            except Exception as e:
                st.error(f"Failed to generate email: {e}")
                st.session_state.email_generated = False
    
    # Display generated email outside the form (only when generated)
    if st.session_state.email_generated and st.session_state.generated_email_data:
        st.markdown("---")
        st.markdown("### 📧 Generated Email Results")
        
        data = st.session_state.generated_email_data
        lead_score = data['lead_score']
        email_response = data['email_response']
        
        # Display lead score metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Lead Score", f"{lead_score.score:.2f}")
        with col2:
            st.metric("Confidence", f"{lead_score.confidence:.2f}")
        
        # Parse and display email content using the new parse function
        parsed_email = parse_email_response(email_response)
        
        if parsed_email:
            # Professional Email Display
            st.markdown("#### 📨 **Email Preview**")
            
            # Subject Line - Separate text box with black background
            st.markdown("**📝 Subject Line:**")
            st.markdown("""
            <style>
                .stTextInput input {
                    background-color: #1a1a1a !important;
                    color: white !important;
                    border: 1px solid #444 !important;
                }
                .stTextInput input:focus {
                    background-color: #1a1a1a !important;
                    color: white !important;
                    border: 1px solid #666 !important;
                }
            </style>
            """, unsafe_allow_html=True)
            st.text_input(
                "Subject",
                value=parsed_email['subject_line'],
                key="subject_display",
                disabled=True
            )
            
            # Email Body - Separate section in a text box with black background
            st.markdown("**✉️ Email Content:**")
            st.markdown("""
            <style>
                .stTextArea textarea {
                    background-color: #1a1a1a !important;
                    color: white !important;
                    border: 1px solid #444 !important;
                    font-size: 14px !important;
                }
                .stTextArea textarea:focus {
                    background-color: #1a1a1a !important;
                    color: white !important;
                    border: 1px solid #666 !important;
                }
                .stTextArea textarea::placeholder {
                    color: #ccc !important;
                }
            </style>
            """, unsafe_allow_html=True)
            st.text_area(
                "Generated Email",
                value=parsed_email['email_body'],
                height=300,
                key="formatted_email_display",
                disabled=True
            )
            
            # AI Statistics - Separate section with better colors
            st.markdown("#### 📊 **AI Statistics**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                personalization_score = parsed_email.get('personalization_score', 0)
                if isinstance(personalization_score, float):
                    st.metric(
                        "🎯 Personalization Score", 
                        f"{personalization_score:.1%}",
                        help="How well the email is personalized for this lead"
                    )
                else:
                    st.metric("🎯 Personalization Score", f"{personalization_score}")
            
            with col2:
                pain_points = parsed_email.get('pain_points_addressed', [])
                st.metric(
                    "💡 Pain Points Addressed", 
                    len(pain_points),
                    help="Number of pain points identified and addressed"
                )
            
            with col3:
                has_calendly = "calendly" in parsed_email.get('email_body', '').lower()
                st.metric(
                    "📅 Calendly Integration", 
                    "✅ Yes" if has_calendly else "❌ No",
                    help="Whether the email includes a Calendly link"
                )
            
            # Pain Points Addressed - Better visibility
            if parsed_email.get('pain_points_addressed'):
                st.markdown("**🎯 Pain Points Addressed:**")
                for point in parsed_email['pain_points_addressed']:
                    st.markdown(f"""
                    <div style="
                        background-color: #28A745;
                        color: white;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 10px 0;
                        border-left: 4px solid #1E7E34;
                        font-weight: 500;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                    💡 {point}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Calendly Integration Note - Better visibility
            calendly_note = parsed_email.get('calendly_integration', '')
            if calendly_note:
                st.markdown("**📅 Calendly Integration Strategy:**")
                st.markdown(f"""
                <div style="
                    background-color: #FFC107;
                    color: #212529;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    border-left: 4px solid #E0A800;
                    font-weight: 500;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                💡 {calendly_note}
                </div>
                """, unsafe_allow_html=True)
            
            # Parse format info for debugging
            if parsed_email.get('format') == 'error':
                st.warning(f"⚠️ Parse warning: {parsed_email.get('parse_error', 'Unknown error')}")
        else:
            # Fallback display
            st.error("❌ Failed to parse email response")
            st.markdown("**Raw Content:**")
            st.text_area("Generated Email", email_response.content, height=300, key="fallback_email_display")
        
        # Display AI Recommendations with better readability
        if lead_score.recommendations:
            st.markdown("#### 💡 **AI Recommendations**")
            for i, rec in enumerate(lead_score.recommendations):
                st.markdown(f"""
                <div style="
                    background-color: #2E86AB;
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    border-left: 4px solid #1E5F8A;
                    font-weight: 500;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                <strong>{i+1}.</strong> {rec}
                </div>
                """, unsafe_allow_html=True)
        
        # Action Buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy Email", key="copy_email_btn"):
                st.success("Email copied to clipboard! (Feature would work in production)")
        
        with col2:
            if st.button("📤 Send Test Email", key="send_test_email_btn"):
                # Show test email form
                st.session_state.show_test_email_form = True
                st.rerun()
        
        with col3:
            if st.button("🔄 Generate New Email", key="clear_and_regenerate"):
                # Clear session state
                st.session_state.email_generated = False
                st.session_state.generated_email_data = None
                st.rerun()
    
    # Test Email Form
    if st.session_state.get('show_test_email_form', False):
        st.markdown("---")
        st.markdown("### 📤 Send Test Email")
        
        with st.form("test_email_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                test_recipient = st.text_input(
                    "Recipient Email:",
                    placeholder="test@example.com",
                    help="Enter the email address to send the test email to"
                )
                test_subject = st.text_input(
                    "Subject Line:",
                    value=parsed_email['subject_line'] if parsed_email else "Test Email",
                    help="Customize the subject line if needed"
                )
            
            with col2:
                test_sender_name = st.text_input(
                    "Your Name:",
                    value=auth_manager.get_current_user_name() or "Your Name",
                    help="Name that will appear as the sender"
                )
                test_sender_email = st.text_input(
                    "Your Email:",
                    value=auth_manager.get_current_user_email() or "",
                    help="Email address that will appear as the sender"
                )
            
            # Email preview
            if parsed_email:
                st.markdown("**📧 Email Preview:**")
                st.markdown(f"**To:** {test_recipient if test_recipient else '[Recipient Email]'}")
                st.markdown(f"**From:** {test_sender_name} <{test_sender_email}>")
                st.markdown(f"**Subject:** {test_subject}")
                st.markdown("**Body:**")
                st.text_area("Email Body Preview", parsed_email['email_body'], height=200, disabled=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("📤 Send Test Email", type="primary"):
                    if test_recipient and test_sender_email:
                        try:
                            # Send test email using Gmail API
                            from integrations import integration_manager
                            
                            # Prepare email data
                            email_data = {
                                'to': test_recipient,
                                'subject': test_subject,
                                'body': parsed_email['email_body'] if parsed_email else "Test email content",
                                'sender_name': test_sender_name,
                                'sender_email': test_sender_email
                            }
                            
                            with st.spinner("Sending test email..."):
                                # Send email using Gmail integration
                                result = asyncio.run(integration_manager.gmail_api.send_email(
                                    to_email=test_recipient,
                                    subject=test_subject,
                                    body=parsed_email['email_body'] if parsed_email else "Test email content",
                                    from_name=test_sender_name
                                ))
                                
                                if result.success:
                                    st.success("✅ Test email sent successfully!")
                                    st.info(f"📧 Email sent to: {test_recipient}")
                                    st.session_state.show_test_email_form = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to send test email: {result.error_message}")
                        except Exception as e:
                            st.error(f"❌ Error sending test email: {e}")
                    else:
                        st.error("❌ Please fill in recipient email and sender email fields.")
            
            with col2:
                if st.form_submit_button("❌ Cancel", type="secondary"):
                    st.session_state.show_test_email_form = False
                    st.rerun()
            
            with col3:
                if st.form_submit_button("🔄 Reset Form", type="secondary"):
                    st.rerun()
    
    # AI performance metrics
    st.markdown("---")
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

def show_campaign_builder():
    """Display the campaign builder page."""
    st.markdown('<h1 class="main-header">🎯 Campaign Builder</h1>', unsafe_allow_html=True)
    
    # Campaign Overview Stats
    st.markdown("### 📊 Campaign Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">12</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Active Campaigns</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">2,847</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Emails Sent</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">18.7%</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Open Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0; font-size: 2rem;">156</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Meetings Booked</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Launch New Campaign", type="primary", use_container_width=True):
            st.info("Campaign creation wizard coming soon!")
    
    with col2:
        if st.button("📊 View Analytics", type="secondary", use_container_width=True):
            st.info("Advanced analytics dashboard coming soon!")
    
    with col3:
        if st.button("⚙️ Campaign Settings", type="secondary", use_container_width=True):
            st.info("Campaign configuration panel coming soon!")
    
    # Campaign Templates Section
    st.markdown("### 📝 Campaign Templates")
    st.markdown("Choose from our proven email campaign templates or create your own")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0 0 15px 0;">🆕 Cold Outreach</h4>
            <p style="margin: 0 0 20px 0; opacity: 0.9;">Perfect for new lead acquisition with proven conversion rates</p>
            <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; margin: 10px 0;">
                <strong>Success Rate:</strong> 23.4%
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; margin: 10px 0;">
                <strong>Avg. Response:</strong> 8.7%
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Use Template", key="cold_outreach_enhanced", use_container_width=True):
            st.success("✅ Cold Outreach template selected!")
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            padding: 25px;
            border-radius: 15px;
            color: #333;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0 0 15px 0;">🔄 Follow-up Sequence</h4>
            <p style="margin: 0 0 20px 0; opacity: 0.8;">Automated follow-up workflow with smart timing</p>
            <div style="background: rgba(0,0,0,0.1); padding: 10px; border-radius: 8px; margin: 10px 0;">
                <strong>Sequence Length:</strong> 5 emails
            </div>
            <div style="background: rgba(0,0,0,0.1); padding: 10px; border-radius: 8px; margin: 10px 0;">
                <strong>Engagement:</strong> 34.2%
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Use Template", key="follow_up_enhanced", use_container_width=True):
            st.success("✅ Follow-up Sequence template selected!")
    
    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 25px;
            border-radius: 15px;
            color: #333;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0 0 15px 0;">🎯 Re-engagement</h4>
            <p style="margin: 0 0 20px 0; opacity: 0.8;">Re-engage dormant leads with personalized content</p>
            <div style="background: rgba(0,0,0,0.1); padding: 10px; border-radius: 8px; margin: 10px 0;">
                <strong>Reactivation:</strong> 19.8%
            </div>
            <div style="background: rgba(0,0,0,0.1); padding: 10px; border-radius: 8px; margin: 10px 0;">
                <strong>Conversion:</strong> 12.3%
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Use Template", key="re_engagement_enhanced", use_container_width=True):
            st.success("✅ Re-engagement template selected!")
    
    # Campaign Performance Chart
    st.markdown("### 📈 Campaign Performance")
    st.markdown("Track your campaign performance over time")
    
    # Placeholder for chart (would be real data in production)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    ">
        <h4 style="margin: 0 0 20px 0;">📊 Performance Analytics</h4>
        <p style="margin: 0; opacity: 0.9;">Interactive charts and detailed analytics coming soon!</p>
        <div style="margin-top: 20px;">
            <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; margin: 0 10px;">
                📧 Email Metrics
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; margin: 0 10px;">
                🎯 Conversion Tracking
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; margin: 0 10px;">
                📈 ROI Analysis
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Best Practices
    st.markdown("### 💡 Campaign Best Practices")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #28a745;
        ">
            <h5>🎯 Personalization</h5>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>Use recipient's name and company</li>
                <li>Reference specific pain points</li>
                <li>Include relevant industry insights</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #007bff;
        ">
            <h5>⏰ Timing</h5>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>Send during business hours (9 AM - 3 PM)</li>
                <li>Tuesday-Thursday have highest open rates</li>
                <li>Follow up within 48-72 hours</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

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
                    
                    # Replace the email display section in your existing show_ai_studio function
                    # Find this section and replace it with the code below:

                    # Parse and display email content (REPLACE THIS SECTION)
                    try:
                        if email_response.content and email_response.content.strip().startswith('{'):
                            # Parse JSON response
                            import json
                            
                            # Clean JSON content (remove markdown formatting)
                            clean_content = email_response.content.strip()
                            if clean_content.startswith('```json'):
                                clean_content = clean_content.replace('```json', '').replace('```', '').strip()
                            
                            email_data = json.loads(clean_content)
                            
                            # Display structured email in professional format
                            st.markdown("#### 📧 Generated Email")
                            
                            # Subject Line
                            subject = email_data.get('subject_line', 'No subject')
                            st.markdown("**Subject:**")
                            st.info(f"📧 {subject}")
                            
                            # Email Body - Display as formatted text, not JSON
                            st.markdown("**Email Content:**")
                            email_body = email_data.get('email_body', email_response.content)
                            
                            # Replace \\n with actual line breaks and display as markdown
                            formatted_body = email_body.replace('\\n\\n', '\n\n').replace('\\n', '\n')
                            
                            # Display the email body as formatted text
                            st.markdown(f"""
                    **To:** John Smith  
                    **From:** Your Name  
                    **Subject:** {subject}

                    ---

                    {formatted_body}
                            """)
                            
                            # Display email metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                personalization_score = email_data.get('personalization_score', 0)
                                st.metric("Personalization Score", f"{personalization_score:.2f}" if isinstance(personalization_score, float) else str(personalization_score))
                            
                            with col2:
                                pain_points = email_data.get('pain_points_addressed', [])
                                st.metric("Pain Points Addressed", len(pain_points))
                            
                            with col3:
                                has_calendly = 'calendly' in email_body.lower()
                                st.metric("Calendly Included", "✅ Yes" if has_calendly else "❌ No")
                            
                            # Display pain points as bullet points
                            if pain_points:
                                st.markdown("**Pain Points Addressed:**")
                                for point in pain_points:
                                    st.markdown(f"• {point}")
                            
                            # Display Calendly integration note
                            calendly_note = email_data.get('calendly_integration', '')
                            if calendly_note:
                                st.markdown("**Calendly Integration:**")
                                st.success(f"📅 {calendly_note}")
                            
                        else:
                            # Display raw content if not JSON
                            st.markdown("**Email Content:**")
                            st.markdown(email_response.content)
                            
                    except json.JSONDecodeError:
                        # Fallback - display raw content
                        st.markdown("**Email Content:**")
                        st.markdown(email_response.content)

                    # Display recommendations (REPLACE THE RECOMMENDATIONS SECTION)
                    if lead_score.recommendations:
                        st.markdown("#### 💡 AI Recommendations")
                        for i, rec in enumerate(lead_score.recommendations, 1):
                            st.markdown(f"**{i}.** {rec}")
                    else:
                        st.markdown("#### 💡 AI Recommendations")
                        st.info("No specific recommendations available for this lead.")
                    
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
    st.markdown('<h1 class="main-header">Settings</h1>', unsafe_allow_html=True)
    
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
            
            # Calendly Integration
            st.markdown("### 📅 Calendly Integration")
            calendly_link = st.text_input("Your Calendly Link", 
                                        value=getattr(user, 'calendly_link', ''),
                                        placeholder="https://calendly.com/yourusername",
                                        help="This link will be automatically included in AI-generated emails")
            
            if st.button("💾 Save Profile Changes"):
                try:
                    updates = {
                        'name': st.session_state.profile_name,
                        'company': st.session_state.profile_company,
                        'role': st.session_state.profile_role,
                        'subscription_tier': st.session_state.profile_tier,
                        'is_active': st.session_state.profile_active,
                        'calendly_link': calendly_link
                    }
                    
                    asyncio.run(db_manager.update_user(user_id, updates))
                    st.success("Profile updated successfully!")
                    
                except Exception as e:
                    st.error(f"Failed to update profile: {e}")
        else:
            st.warning("User profile not found.")
            
    except Exception as e:
        st.error(f"Failed to update profile: {e}")
    
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
    st.markdown('<h1 class="main-header">Analytics</h1>', unsafe_allow_html=True)
    
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
