# 🚀 Complete Deployment Guide

This guide walks you through deploying the Chief of Staff AI application to AWS using Terraform and CI/CD.

## Prerequisites Checklist

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Terraform installed (>= 1.0)
- [ ] GitHub repository with Actions enabled
- [ ] Google Cloud Console credentials ready

## Step 1: Infrastructure Setup (Terraform)

### 1.1 Configure Terraform Variables

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
aws_region = "us-east-1"
project_name = "chief-of-staff-ai"

db_name = "chiefofstaff"
db_username = "admin"
db_password = "YOUR_SECURE_PASSWORD_HERE"  # ⚠️ Use a strong password!

rds_instance_class = "db.t3.micro"

ecs_cpu = 512
ecs_memory = 1024
ecs_desired_count = 1

google_client_id = "YOUR_GOOGLE_CLIENT_ID"
google_client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
google_api_key = "YOUR_GOOGLE_API_KEY"
```

### 1.2 Initialize and Deploy

```bash
terraform init
terraform plan  # Review what will be created
terraform apply  # Type 'yes' to confirm
```

**This takes ~15 minutes**. Wait for:
- ✅ VPC and networking
- ✅ RDS PostgreSQL database
- ✅ ECR repository
- ✅ ECS cluster
- ✅ Application Load Balancer
- ✅ S3 bucket and CloudFront

### 1.3 Save Outputs

```bash
terraform output > ../terraform-outputs.txt
```

Important outputs:
- `backend_url`: Your backend API URL
- `frontend_cloudfront_url`: Your frontend URL
- `ecr_repository_url`: ECR URL for Docker images
- `rds_endpoint`: Database endpoint

## Step 2: Configure GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions

Add these secrets:

### AWS Credentials
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### Infrastructure Outputs (from Terraform)
- `ECR_REPOSITORY`: `chief-of-staff-ai-backend`
- `ECS_CLUSTER`: `chief-of-staff-ai-cluster`
- `ECS_SERVICE`: `chief-of-staff-ai-backend-service`
- `S3_BUCKET_NAME`: From `terraform output frontend_s3_bucket`
- `CLOUDFRONT_DISTRIBUTION_ID`: From CloudFront console
- `CLOUDFRONT_DOMAIN`: From `terraform output frontend_cloudfront_url`
- `BACKEND_URL`: From `terraform output backend_url`

### Application Secrets
- `DATABASE_URL`: `postgresql://admin:PASSWORD@RDS_ENDPOINT/chiefofstaff`
- `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret
- `GOOGLE_API_KEY`: Your Google API Key

## Step 3: Update ECS Task Definition

### Option A: Use Environment Variables (Simpler)

The CI/CD pipeline will automatically update the task definition. Just ensure:
1. ECR repository exists (from Terraform)
2. ECS cluster and service exist (from Terraform)
3. IAM roles have correct permissions

### Option B: Use AWS Secrets Manager (Recommended for Production)

1. Create secrets in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name chief-of-staff-ai/database-url \
  --secret-string "postgresql://admin:PASSWORD@RDS_ENDPOINT/chiefofstaff"

aws secretsmanager create-secret \
  --name chief-of-staff-ai/google-client-id \
  --secret-string "YOUR_CLIENT_ID"

aws secretsmanager create-secret \
  --name chief-of-staff-ai/google-client-secret \
  --secret-string "YOUR_CLIENT_SECRET"

aws secretsmanager create-secret \
  --name chief-of-staff-ai/google-api-key \
  --secret-string "YOUR_API_KEY"
```

2. Update `.github/ecs-task-definition.json` with your account ID and region
3. Grant ECS task execution role permission to read secrets

## Step 4: Update Google OAuth Redirect URIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services → Credentials
3. Edit your OAuth 2.0 Client
4. Add authorized redirect URI:
   - `http://YOUR_ALB_DNS_NAME/auth/google/callback`
   - `https://YOUR_CLOUDFRONT_DOMAIN/auth/google/callback` (if using HTTPS)

## Step 5: Deploy Backend

### Manual Deployment (First Time)

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_REPO_URL

# Build and push
cd backend
docker build -t chief-of-staff-ai-backend .
docker tag chief-of-staff-ai-backend:latest YOUR_ECR_REPO_URL:latest
docker push YOUR_ECR_REPO_URL:latest

# Update ECS service (force new deployment)
aws ecs update-service \
  --cluster chief-of-staff-ai-cluster \
  --service chief-of-staff-ai-backend-service \
  --force-new-deployment
```

### Automatic Deployment (CI/CD)

1. Push to `main` branch:
```bash
git add .
git commit -m "Deploy backend"
git push origin main
```

2. GitHub Actions will:
   - Build Docker image
   - Push to ECR
   - Update ECS service
   - Deploy new task

3. Monitor deployment:
   - GitHub Actions tab → View workflow run
   - AWS ECS Console → Check service status

## Step 6: Deploy Frontend

### Manual Deployment (First Time)

```bash
# Update app.js with backend URL
cd frontend
# Edit app.js: Replace YOUR_BACKEND_URL_HERE with your ALB DNS name

# Upload to S3
aws s3 sync . s3://YOUR_S3_BUCKET_NAME --delete --exclude "*.bat"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### Automatic Deployment (CI/CD)

1. Push frontend changes to `main`:
```bash
git add frontend/
git commit -m "Update frontend"
git push origin main
```

2. GitHub Actions will:
   - Update API URL in app.js
   - Upload files to S3
   - Invalidate CloudFront cache

## Step 7: Verify Deployment

### Backend Health Check
```bash
curl http://YOUR_ALB_DNS_NAME/health
```

Expected: `{"status":"ok","app":"ChiefOfStaffBackend"}`

### Frontend Access
Open: `https://YOUR_CLOUDFRONT_DOMAIN`

### Test Full Flow
1. Open frontend URL
2. Click "🔗 Connect Google"
3. Complete OAuth flow
4. Send a test message: "What meetings do I have today?"

## Troubleshooting

### Backend Not Responding
1. Check ECS service status:
   ```bash
   aws ecs describe-services \
     --cluster chief-of-staff-ai-cluster \
     --services chief-of-staff-ai-backend-service
   ```

2. Check CloudWatch logs:
   ```bash
   aws logs tail /ecs/chief-of-staff-ai --follow
   ```

3. Check ALB target health:
   - AWS Console → EC2 → Load Balancers → Target Groups

### Database Connection Issues
1. Verify RDS is running:
   ```bash
   aws rds describe-db-instances --db-instance-identifier chief-of-staff-ai-db
   ```

2. Check security groups allow traffic from ECS tasks
3. Verify DATABASE_URL is correct

### Frontend Not Loading
1. Check S3 bucket has files:
   ```bash
   aws s3 ls s3://YOUR_S3_BUCKET_NAME
   ```

2. Check CloudFront distribution status
3. Verify S3 bucket policy allows CloudFront

### CI/CD Pipeline Failing
1. Check GitHub Actions logs
2. Verify AWS credentials in GitHub Secrets
3. Check IAM permissions for GitHub Actions user
4. Verify ECR repository and ECS cluster names match

## Cost Optimization

### Free Tier (First 12 Months)
- RDS db.t3.micro: 750 hours/month free
- ECS Fargate: 20 GB-hours/month free
- S3: 5 GB storage free
- CloudFront: 50 GB data transfer free

### After Free Tier
- **Estimated: ~$50/month**
- Can reduce by:
  - Using Reserved Instances for RDS
  - Reducing ECS task count when not in use
  - Using S3 Intelligent-Tiering

## Next Steps

1. ✅ Set up HTTPS with ACM certificate
2. ✅ Enable CloudWatch alarms
3. ✅ Set up auto-scaling for ECS
4. ✅ Configure backup strategy for RDS
5. ✅ Add monitoring and alerting

## Support

For issues:
1. Check CloudWatch logs
2. Review GitHub Actions logs
3. Verify Terraform outputs
4. Check AWS service health dashboards
