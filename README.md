# 🚀 AI Sales Assistant - Production-Ready SaaS Platform

> **Never write another cold email. Never miss a follow-up. Turn your Google Sheet of leads into booked meetings automatically - with every email uniquely crafted by AI.**

## 🎯 Overview

The AI Sales Assistant is a comprehensive, production-ready SaaS platform that automates the entire sales outreach process using advanced AI technology. It transforms raw lead data into personalized, high-converting email campaigns with intelligent follow-up sequences and automated meeting booking.

## ✨ Key Features

- **🤖 AI-Powered Personalization**: Generate unique, personalized emails for every lead using Google Gemini AI
- **📊 Lead Management**: Import leads from Google Sheets with intelligent data validation and enrichment
- **📧 Campaign Automation**: Orchestrate multi-touch email sequences with conditional logic
- **📈 Smart Analytics**: Real-time performance tracking with AI-driven insights and recommendations
- **🔄 Automated Follow-ups**: Never miss a follow-up with intelligent scheduling and response analysis
- **📅 Meeting Booking**: Integrate with Calendly for automated meeting scheduling
- **🔒 Enterprise Security**: OAuth 2.0 authentication with comprehensive access controls
- **📱 Professional UI**: Beautiful Streamlit interface with real-time dashboard and monitoring

## 🏗️ Architecture

This platform is built with a **distributed microservice architecture** designed for enterprise-scale usage:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   External      │    │   AI Engine     │
│   (app.py)      │◄──►│   APIs          │◄──►│   (ai_engine.py)│
│                 │    │   (integrations)│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Automation    │    │   Auth &        │
│   (database.py) │    │   (automation.py)│   │   Security      │
│                 │    │                 │    │   (auth.py)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   Configuration         │
                    │   (config.py)           │
                    └─────────────────────────┘
```

## 📁 Project Structure

```
ai-sales-assistant/
├── app.py                 # 🎨 Main Streamlit UI application
├── integrations.py        # 🔗 External API integrations (Gmail, Sheets, Gemini, Calendly)
├── ai_engine.py          # 🧠 AI intelligence core (email generation, analysis, scoring)
├── automation.py          # ⚙️ Workflow orchestration and campaign automation
├── database.py            # 💾 Data persistence layer (Firebase Firestore)
├── auth.py               # 🔐 Security & session management (OAuth 2.0)
├── config.py             # ⚙️ Configuration management and constants
├── requirements.txt      # 📦 Production dependencies
└── README.md            # 📚 This documentation
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- Google Cloud Platform account
- Firebase project
- Google Gemini API key
- Calendly API key

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-sales-assistant.git
cd ai-sales-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file with your API credentials:

```bash
# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Google OAuth (Gmail)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:8501/auth/callback

# Google OAuth (Sheets)
SHEETS_CLIENT_ID=your_sheets_client_id
SHEETS_CLIENT_SECRET=your_sheets_client_secret
SHEETS_REDIRECT_URI=http://localhost:8501/auth/callback

# Calendly
CALENDLY_API_KEY=your_calendly_api_key

# Firebase
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id

# System Configuration
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 4. Run the Application

```bash
# Start the Streamlit app
streamlit run app.py

# Or run with custom configuration
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 🔧 Configuration

### Email Settings

```python
# config.py - Email Configuration
MAX_EMAILS_PER_DAY=100
FOLLOW_UP_DELAY_HOURS=48
MAX_FOLLOW_UPS=3
BUSINESS_HOURS_START=9
BUSINESS_HOURS_END=17
TIMEZONE=UTC
```

### Automation Settings

```python
# config.py - Automation Configuration
BATCH_SIZE=50
PROCESSING_INTERVAL_MINUTES=15
MAX_CONCURRENT_CAMPAIGNS=10
LEAD_SCORE_THRESHOLD=0.7
ENGAGEMENT_TIMEOUT_HOURS=168
```

### AI Model Settings

```python
# config.py - AI Configuration
GEMINI_MODEL=gemini-pro
GEMINI_MAX_TOKENS=2048
GEMINI_TEMPERATURE=0.7
```

## 📊 Usage Guide

### 1. Lead Import

1. **Connect Google Sheets**: Authorize access to your lead spreadsheet
2. **Configure Mapping**: Map columns to lead fields (Name, Email, Company, Job Title, etc.)
3. **Import Leads**: Bulk import leads with automatic validation and enrichment
4. **Review & Edit**: Manually review and edit lead information as needed

### 2. Campaign Creation

1. **Define Campaign**: Set campaign name, description, and target audience
2. **Configure Sequence**: Set up email sequence with timing and conditions
3. **Personalization**: Configure AI prompts and personalization rules
4. **Launch**: Start the campaign with automated execution

### 3. Email Generation

1. **AI Analysis**: System analyzes each lead using company research and pain points
2. **Content Generation**: Gemini AI generates personalized email content
3. **Quality Check**: Review generated emails before sending
4. **Automated Sending**: Emails are sent with optimal timing and tracking

### 4. Follow-up Management

1. **Response Monitoring**: Track email opens, clicks, and responses
2. **AI Analysis**: Analyze response sentiment and intent
3. **Automated Follow-ups**: Generate and send contextual follow-up emails
4. **Meeting Booking**: Automatically schedule meetings for interested leads

## 🔒 Security Features

- **OAuth 2.0 Authentication**: Secure Google API access
- **Session Management**: Secure session handling with Streamlit
- **Access Control**: Role-based permissions and user management
- **Data Encryption**: Secure storage and transmission of sensitive data
- **Rate Limiting**: API rate limiting to prevent abuse
- **Audit Logging**: Comprehensive logging for security monitoring

## 📈 Performance & Scalability

- **Async Processing**: Non-blocking I/O for high-performance operations
- **Batch Operations**: Efficient bulk processing of leads and emails
- **Caching**: Redis-based caching for improved response times
- **Horizontal Scaling**: Microservice architecture for easy scaling
- **Load Balancing**: Support for multiple application instances
- **Database Optimization**: Efficient Firestore queries and indexing

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test modules
pytest tests/test_ai_engine.py
pytest tests/test_integrations.py

# Run async tests
pytest tests/test_automation.py -v
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-sales-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-sales-assistant
  template:
    metadata:
      labels:
        app: ai-sales-assistant
    spec:
      containers:
      - name: ai-sales-assistant
        image: ai-sales-assistant:latest
        ports:
        - containerPort: 8501
        env:
        - name: ENVIRONMENT
          value: "production"
```

### Production Considerations

- **Load Balancing**: Use Nginx or HAProxy for traffic distribution
- **Monitoring**: Implement Prometheus metrics and Grafana dashboards
- **Logging**: Centralized logging with ELK stack or similar
- **Backup**: Regular database backups and disaster recovery procedures
- **SSL/TLS**: HTTPS encryption for all communications
- **CDN**: Content delivery network for static assets

## 🔧 API Reference

### Core Endpoints

```python
# Lead Management
POST /api/leads - Create new lead
GET /api/leads - List leads with filters
PUT /api/leads/{id} - Update lead
DELETE /api/leads/{id} - Delete lead

# Campaign Management
POST /api/campaigns - Create campaign
GET /api/campaigns - List campaigns
PUT /api/campaigns/{id}/status - Update campaign status
POST /api/campaigns/{id}/start - Start campaign

# Email Operations
POST /api/emails/generate - Generate AI email
POST /api/emails/send - Send email
GET /api/emails/analytics - Get email analytics

# AI Engine
POST /api/ai/analyze - Analyze response
POST /api/ai/score - Score lead
GET /api/ai/insights - Get AI insights
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run code formatting
black .
isort .

# Run linting
flake8 .
mypy .

# Run tests
pytest --cov=. --cov-report=html
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full API Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-sales-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-sales-assistant/discussions)
- **Email**: support@aisalesassistant.com

## 🙏 Acknowledgments

- **Google Gemini AI** for advanced content generation
- **Firebase** for scalable database infrastructure
- **Streamlit** for the beautiful web interface
- **Open Source Community** for the amazing libraries and tools

---

**Built with ❤️ for sales professionals who want to scale their outreach without losing the personal touch.**

*Last updated: December 2024*