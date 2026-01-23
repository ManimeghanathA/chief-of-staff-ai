# Infrastructure as Code - Chief of Staff AI

This directory contains Terraform scripts to provision AWS infrastructure for the Chief of Staff AI application.

## Architecture

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

## Prerequisites

1. **AWS CLI** installed and configured
   ```bash
   aws configure
   ```

2. **Terraform** installed (>= 1.0)
   ```bash
   terraform version
   ```

3. **AWS Account** with appropriate permissions:
   - VPC, EC2, ECS, ECR, RDS, S3, CloudFront, IAM, ALB

## Setup Instructions

### 1. Configure Variables

Copy the example variables file:
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:
- `db_password`: Strong password for RDS
- `google_client_id`: Your Google OAuth Client ID
- `google_client_secret`: Your Google OAuth Client Secret
- `google_api_key`: Your Google API Key

### 2. Initialize Terraform

```bash
cd infra
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

This will show you what resources will be created.

### 4. Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will create:
- VPC with public/private subnets
- RDS PostgreSQL database
- ECR repository for backend
- ECS cluster and service
- Application Load Balancer
- S3 bucket for frontend
- CloudFront distribution

**Note**: This will take 10-15 minutes, especially for RDS.

### 5. Get Outputs

After deployment, get important URLs:
```bash
terraform output
```

Key outputs:
- `backend_url`: Your backend API URL
- `frontend_cloudfront_url`: Your frontend URL
- `ecr_repository_url`: ECR URL for pushing images

### 6. Update Environment Variables

After RDS is created, update your backend environment variables:
1. Get RDS endpoint: `terraform output rds_endpoint`
2. Update `DATABASE_URL` in your CI/CD secrets or ECS task definition

## CI/CD Integration

The infrastructure outputs are used by GitHub Actions:
- `ECR_REPOSITORY_URL`: From `terraform output ecr_repository_url`
- `ECS_CLUSTER_NAME`: From `terraform output ecs_cluster_name`
- `ECS_SERVICE_NAME`: From `terraform output ecs_service_name`
- `ALB_DNS_NAME`: From `terraform output alb_dns_name`

## Cost Estimation

**Free Tier Eligible** (first 12 months):
- RDS: db.t3.micro (750 hours/month free)
- ECS Fargate: 20 GB-hours/month free
- S3: 5 GB storage free
- CloudFront: 50 GB data transfer free

**Estimated Monthly Cost** (after free tier):
- RDS db.t3.micro: ~$15/month
- ECS Fargate (0.5 vCPU, 1GB): ~$15/month
- ALB: ~$16/month
- S3 + CloudFront: ~$1-5/month
- **Total: ~$50/month** (can be reduced with reserved instances)

## Updating Infrastructure

To update infrastructure:
```bash
terraform plan
terraform apply
```

## Destroying Infrastructure

⚠️ **Warning**: This will delete ALL resources including the database!

```bash
terraform destroy
```

## Troubleshooting

### RDS Connection Issues
- Check security groups allow traffic from ECS tasks
- Verify database credentials
- Check RDS is in private subnet

### ECS Tasks Not Starting
- Check CloudWatch logs: `/ecs/chief-of-staff-ai`
- Verify ECR image exists and is tagged correctly
- Check task definition environment variables

### Frontend Not Loading
- Verify S3 bucket has files uploaded
- Check CloudFront distribution status
- Verify S3 bucket policy allows CloudFront access

## Next Steps

1. **Deploy Backend**: Use CI/CD pipeline to push Docker image to ECR
2. **Deploy Frontend**: Upload frontend files to S3 bucket
3. **Update OAuth Redirect URIs**: Add ALB URL to Google Cloud Console
4. **Set up HTTPS**: Add ACM certificate and update ALB listener

## Security Notes

- RDS is in private subnet (not publicly accessible)
- ECS tasks are in private subnet
- ALB is in public subnet (only entry point)
- Use AWS Secrets Manager for sensitive values in production
- Enable RDS encryption at rest
- Enable CloudFront HTTPS only
