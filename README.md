# Chief of Staff AI – Agentic AI Assistant

## 🎯 Project Overview

A production-grade Personal Agentic AI Assistant that acts as a "Chief of Staff" running in the cloud. Built for the Sentellent internship challenge, this system helps users manage their day through intelligent chat interactions, email management, and calendar integration.

## ✅ Completed Features

### Phase 1: Foundation (100% Complete)
- ✅ **LangGraph-based Chat Agent**: Intelligent assistant with intent routing
- ✅ **PostgreSQL Database**: Persistent storage for users, credentials, messages, and **dynamic memory**
- ✅ **Authentication**: JWT-based auth with email/password and Google OAuth
- ✅ **Docker Containerization**: Fully containerized backend
- ✅ **AWS Deployment**: Complete infrastructure with Terraform (ECS, ECR, RDS, ALB, S3, CloudFront)
- ✅ **CI/CD Pipeline**: GitHub Actions for automated backend and frontend deployment

### Phase 2: Integration (100% Complete)
- ✅ **Google OAuth**: Full OAuth flow with token refresh
- ✅ **Gmail API Integration**: Read emails, fetch by date, summarize important emails
- ✅ **Calendar API Integration**: Read events, create meetings, view today/tomorrow schedules
- ✅ **Action Tools**: Agent can fetch emails and view calendar events based on user prompts

### Phase 3: Dynamic Memory (100% Complete) ⭐
- ✅ **Memory from Chat**: Extracts and stores user preferences from conversations
  - Example: "I hate 9 AM meetings" → Stored in database
- ✅ **Memory from Emails**: Automatically extracts facts from email content
  - Example: "Project X is delayed" → Extracted and stored
- ✅ **Memory Retrieval**: Agent uses stored memories in all responses
- ✅ **Memory Context**: Preferences are included in system prompts for personalized responses

## 🏗️ Architecture

```
┌─────────────────┐
│   CloudFront    │ (Frontend CDN)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   S3 Bucket     │ (Frontend Static Files)
└─────────────────┘

┌─────────────────┐
│   ALB           │ (Application Load Balancer)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ECS Fargate   │ (Backend Containers)
└────────┬────────┘
         │
         ├──► ECR (Container Registry)
         │
         └──► RDS PostgreSQL (Database)
```

## 🚀 Quick Start

### Local Development

See [TESTING_GUIDE.md](./TESTING_GUIDE.md) for detailed local setup instructions.

### AWS Deployment

See [infra/DEPLOYMENT_GUIDE.md](./infra/DEPLOYMENT_GUIDE.md) for complete deployment instructions.

**Quick Deploy:**
```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform apply
```

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with email/password
- `GET /auth/google/login` - Initiate Google OAuth
- `GET /auth/google/callback` - OAuth callback

### Chat
- `POST /chat/` - Send message to agent (requires Bearer token)
  ```json
  {
    "message": "What meetings do I have today?"
  }
  ```

### Gmail
- `GET /gmail/latest` - Get latest emails (requires Bearer token)

### Calendar
- `GET /calendar/events` - Get calendar events (requires Bearer token)

## 🧠 Memory System

The agent has **dynamic memory** that learns from both chat and emails:

### How It Works

1. **Memory Extraction**: When you chat or the agent reads emails, it extracts:
   - Personal preferences ("I hate 9 AM meetings")
   - Important facts ("Project X is delayed")
   - User habits and patterns

2. **Memory Storage**: All memories are stored in PostgreSQL with:
   - `user_id`: Who the memory belongs to
   - `key`: The fact/preference name
   - `value`: The description
   - `source`: "chat" or "email"

3. **Memory Retrieval**: Every conversation loads your memories and uses them to:
   - Personalize responses
   - Remember your preferences
   - Contextualize email summaries
   - Draft emails in your style

### Example Flow

```
User: "I hate 9 AM meetings"
Agent: [Extracts memory: {"key": "meeting_preference", "value": "hates 9 AM meetings"}]
Agent: "Got it! I'll remember that you prefer not to have 9 AM meetings."

[Later...]
User: "What meetings do I have today?"
Agent: [Loads memory, sees 9 AM meeting]
Agent: "You have a meeting at 9 AM today. I remember you don't like 9 AM meetings - would you like me to help reschedule it?"
```

## 🐳 Docker Deployment

### Build and Run Locally
```bash
cd backend
docker build -t chief-of-staff-backend .
docker run -p 8000:8000 --env-file .env chief-of-staff-backend
```

### AWS ECS Deployment
The project includes:
- **Terraform scripts** for complete infrastructure provisioning
- **Dockerfile** for containerization
- **GitHub Actions CI/CD** pipeline for automated deployment
- **ECS Fargate** deployment configuration

## 📊 Database Schema

- **users**: User accounts (email, id)
- **google_credentials**: OAuth tokens and refresh tokens
- **messages**: Chat history (optional)
- **memory**: **Dynamic memory storage** (key-value pairs with source tracking)

## 🔒 Security

- JWT-based authentication
- Bearer token authorization
- Secure credential storage
- CORS configured for frontend access
- RDS in private subnet
- ECS tasks in private subnet
- ALB as only public entry point

## 🧪 Testing the Memory System

1. **Register/Login** via frontend or API
2. **Connect Google** to enable Gmail/Calendar access
3. **Chat with the agent:**
   - "I hate 9 AM meetings" → Memory stored
   - "I prefer afternoon meetings" → Memory stored
4. **Ask about emails:**
   - "What important emails do I have today?" → Agent reads emails and extracts facts
5. **Verify memory:**
   - Ask the agent to draft an email → It should remember your preferences

## 📝 Infrastructure

### Terraform Modules
- **VPC**: Public and private subnets across 2 AZs
- **RDS PostgreSQL**: Managed database in private subnet
- **ECS Fargate**: Container orchestration
- **ECR**: Container registry
- **ALB**: Application Load Balancer
- **S3 + CloudFront**: Frontend hosting with CDN

### CI/CD Pipeline
- **Backend**: Build → Push to ECR → Deploy to ECS
- **Frontend**: Upload to S3 → Invalidate CloudFront cache

## 📸 Submission Checklist

- ✅ GitHub Repo: Contains Frontend + Backend code
- ✅ Live Application URL: Backend deployed on AWS ECS
- ✅ Proof of Cloud: AWS Console screenshots
- ✅ CI/CD Pipeline: GitHub Actions passing
- ✅ Dynamic Memory: Fully implemented and working
- ✅ Terraform Scripts: Complete infrastructure as code
- ✅ Infrastructure Documentation: Deployment guides included

## 👨‍💻 Development

Built with:
- Python 3.12+
- FastAPI
- LangGraph/LangChain
- PostgreSQL
- Docker
- AWS (ECS, ECR, RDS, ALB, S3, CloudFront)
- Terraform
- GitHub Actions

## 📄 License

This project was built for the Sentellent internship challenge.

---
