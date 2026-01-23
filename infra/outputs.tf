output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "ecr_repository_url" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.backend.name
}

output "frontend_s3_bucket" {
  description = "Frontend S3 bucket name"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_cloudfront_url" {
  description = "Frontend CloudFront distribution URL"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${aws_lb.main.dns_name}"
}
