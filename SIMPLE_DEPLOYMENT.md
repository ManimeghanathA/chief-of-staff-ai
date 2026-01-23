# 🚀 Simple AWS Deployment Guide (No Terraform Needed)

This guide will get you a live AWS URL in the simplest way possible.

## What You'll Get
- ✅ Live Backend URL: `http://your-alb-url.region.elb.amazonaws.com`
- ✅ Live Frontend URL: `https://your-cloudfront-url.cloudfront.net`
- ✅ Everything running on AWS

## Prerequisites (5 minutes setup)

1. **AWS Account** - Sign up at https://aws.amazon.com (free tier available)
2. **AWS CLI** - Install from https://aws.amazon.com/cli/
3. **Docker** - You already have this! ✅

### Setup AWS CLI
```bash
aws configure
```
Enter:
- AWS Access Key ID: (Get from AWS Console → IAM → Users → Your User → Security Credentials)
- AWS Secret Access Key: (Same place)
- Default region: `us-east-1`
- Default output format: `json`

## Step 1: Create ECR Repository (Docker Registry on AWS)

```bash
aws ecr create-repository --repository-name chief-of-staff-backend --region us-east-1
```

**Save the output!** You'll see something like:
```
"repositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/chief-of-staff-backend"
```

## Step 2: Build and Push Docker Image

```bash
# Navigate to backend folder
cd backend

# Login to ECR (replace 123456789012 with your AWS account ID)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build your Docker image
docker build -t chief-of-staff-backend .

# Tag it for ECR (replace 123456789012 with your AWS account ID)
docker tag chief-of-staff-backend:latest 634541169535.dkr.ecr.us-east-1.amazonaws.com/chief-of-staff-backend:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/chief-of-staff-backend:latest
```

✅ **Your Docker image is now on AWS!**

## Step 3: Create RDS Database (PostgreSQL)

### Option A: Using AWS Console (Easiest)

1. Go to https://console.aws.amazon.com/rds
2. Click "Create database"
3. Choose:
   - **Engine**: PostgreSQL
   - **Version**: PostgreSQL 15.4
   - **Template**: Free tier
   - **DB instance identifier**: `chief-of-staff-db`
   - **Master username**: `admin`
   - **Master password**: `YourSecurePassword123!` (SAVE THIS!)
   - **DB instance class**: `db.t3.micro` (Free tier)
   - **Storage**: 20 GB
   - **VPC**: Default VPC
   - **Public access**: Yes (for now, easier to connect)
   - **Database name**: `chiefofstaff`
4. Click "Create database"
5. **Wait 5-10 minutes** for it to be ready
6. **Save the endpoint!** It looks like: `chief-of-staff-db.xxxxx.us-east-1.rds.amazonaws.com:5432`

### Option B: Using AWS CLI

```bash
aws rds create-db-instance \
  --db-instance-identifier chief-of-staff-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YourSecurePassword123! \
  --allocated-storage 20 \
  --publicly-accessible \
  --db-name chiefofstaff
```

## Step 4: Create ECS Cluster and Service (Using AWS Console)

### 4.1 Create ECS Cluster

1. Go to https://console.aws.amazon.com/ecs
2. Click "Create Cluster"
3. Choose:
   - **Cluster name**: `chief-of-staff-cluster`
   - **Infrastructure**: AWS Fargate (Serverless)
4. Click "Create"

### 4.2 Create Task Definition

1. In ECS Console, click "Task Definitions" → "Create new Task Definition"
2. Choose:
   - **Task definition family**: `chief-of-staff-backend`
   - **Launch type**: Fargate
   - **Task size**:
     - CPU: 0.5 vCPU (512)
     - Memory: 1 GB (1024)
3. Click "Add container":
   - **Container name**: `backend`
   - **Image URI**: `123456789012.dkr.ecr.us-east-1.amazonaws.com/chief-of-staff-backend:latest` (your ECR URI)
   - **Port mappings**: `8000`
   - **Environment variables** (Add these):
     ```
     APP_NAME = ChiefOfStaffBackend
     DATABASE_URL = postgresql://admin:YourSecurePassword123!@chief-of-staff-db.xxxxx.us-east-1.rds.amazonaws.com:5432/chiefofstaff
     GOOGLE_CLIENT_ID = YOUR_GOOGLE_CLIENT_ID
     GOOGLE_CLIENT_SECRET = YOUR_GOOGLE_CLIENT_SECRET
     GOOGLE_REDIRECT_URI = http://YOUR_ALB_URL/auth/google/callback
     GOOGLE_API_KEY = YOUR_GOOGLE_API_KEY
     FRONTEND_URL = https://YOUR_CLOUDFRONT_URL
     ```
4. Click "Create"

### 4.3 Create Service

1. Go back to your cluster → Click "Create Service"
2. Choose:
   - **Launch type**: Fargate
   - **Task definition**: `chief-of-staff-backend`
   - **Service name**: `backend-service`
   - **Number of tasks**: 1
   - **VPC**: Default VPC
   - **Subnets**: Select all available
   - **Security group**: Create new (allow port 8000 from anywhere)
   - **Load balancer**: Create new Application Load Balancer
     - **Load balancer name**: `chief-of-staff-alb`
     - **Listener**: HTTP, Port 80
     - **Target group**: Create new
       - **Target group name**: `backend-tg`
       - **Port**: 8000
       - **Health check path**: `/health`
3. Click "Create"

**Wait 5-10 minutes** for the service to start.

4. **Get your ALB URL**:
   - Go to EC2 Console → Load Balancers
   - Find `chief-of-staff-alb`
   - Copy the DNS name (looks like: `chief-of-staff-alb-1234567890.us-east-1.elb.amazonaws.com`)

✅ **Your backend is live!** Test it: `http://YOUR-ALB-URL/health`

## Step 5: Deploy Frontend to S3 + CloudFront

### 5.1 Create S3 Bucket

```bash
# Create bucket (replace YOUR-UNIQUE-NAME with something unique)
aws s3 mb s3://chief-of-staff-frontend-YOUR-UNIQUE-NAME --region us-east-1

# Enable static website hosting
aws s3 website s3://chief-of-staff-frontend-YOUR-UNIQUE-NAME \
  --index-document index.html \
  --error-document index.html
```

### 5.2 Upload Frontend Files

```bash
cd frontend

# Update app.js with your backend URL
# Edit app.js and replace YOUR_BACKEND_URL_HERE with your ALB URL

# Upload files
aws s3 sync . s3://chief-of-staff-frontend-YOUR-UNIQUE-NAME \
  --exclude "*.bat" \
  --exclude ".git/*"
```

### 5.3 Create CloudFront Distribution (Using Console)

1. Go to https://console.aws.amazon.com/cloudfront
2. Click "Create Distribution"
3. Choose:
   - **Origin domain**: Select your S3 bucket
   - **Origin access**: Public
   - **Viewer protocol policy**: Redirect HTTP to HTTPS
   - **Default root object**: `index.html`
   - **Error pages**: 
     - 404 → 200 → `/index.html`
     - 403 → 200 → `/index.html`
4. Click "Create Distribution"
5. **Wait 10-15 minutes** for deployment
6. **Copy the CloudFront URL** (looks like: `d1234567890abc.cloudfront.net`)

✅ **Your frontend is live!** Open: `https://YOUR-CLOUDFRONT-URL`

## Step 6: Update Environment Variables

1. Go back to ECS → Task Definitions → `chief-of-staff-backend` → Create new revision
2. Update environment variables:
   - `GOOGLE_REDIRECT_URI`: `http://YOUR-ALB-URL/auth/google/callback`
   - `FRONTEND_URL`: `https://YOUR-CLOUDFRONT-URL`
3. Update service to use new task definition

## Step 7: Update Google OAuth Redirect URIs

1. Go to https://console.cloud.google.com
2. APIs & Services → Credentials
3. Edit your OAuth 2.0 Client
4. Add authorized redirect URI:
   - `http://YOUR-ALB-URL/auth/google/callback`

## ✅ You're Done!

### Your Live URLs:
- **Backend**: `http://YOUR-ALB-URL`
- **Frontend**: `https://YOUR-CLOUDFRONT-URL`

### Test It:
1. Open frontend URL
2. Click "Connect Google"
3. Login and test!

## Troubleshooting

### Backend not responding?
1. Check ECS service: ECS Console → Clusters → Your cluster → Services
2. Check logs: ECS Console → Your service → Logs tab
3. Check ALB: EC2 Console → Load Balancers → Check target health

### Database connection error?
1. Check RDS is running: RDS Console
2. Check security group allows port 5432 from ECS tasks
3. Verify DATABASE_URL is correct

### Frontend not loading?
1. Check S3 bucket has files: `aws s3 ls s3://your-bucket-name`
2. Check CloudFront status: CloudFront Console
3. Wait 15 minutes for CloudFront to deploy

## Quick Commands Reference

```bash
# Check ECS service status
aws ecs describe-services --cluster chief-of-staff-cluster --services backend-service

# View logs
aws logs tail /ecs/chief-of-staff-backend --follow

# Check RDS status
aws rds describe-db-instances --db-instance-identifier chief-of-staff-db

# Update ECS service (force new deployment)
aws ecs update-service --cluster chief-of-staff-cluster --service backend-service --force-new-deployment
```

## For Submission

Take screenshots of:
1. ✅ ECS Console showing running service
2. ✅ RDS Console showing database
3. ✅ ALB showing healthy targets
4. ✅ CloudFront distribution
5. ✅ S3 bucket with files
6. ✅ Your live frontend URL working
7. ✅ Your live backend `/health` endpoint

**That's it!** You now have a live AWS deployment! 🎉
