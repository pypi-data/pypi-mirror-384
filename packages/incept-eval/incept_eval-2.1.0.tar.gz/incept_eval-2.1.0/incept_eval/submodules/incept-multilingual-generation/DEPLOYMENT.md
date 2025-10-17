# Deployment Guide

## Prerequisites

Install dependencies:
```bash
brew install awscli terraform
aws configure  # Use your AWS access key/secret
```

## Quick Setup

1. **Create S3 bucket for Terraform state:**
   ```bash
   aws s3 mb s3://incept-terraform-state --region us-east-1
   ```

2. **Deploy infrastructure:**
   ```bash
   cd infrastructure
   terraform init
   terraform apply
   ```

3. **Setup secrets:**
   ```bash
   ./setup-secrets.sh  # Will read from .env file
   ```

4. **Configure GitHub secrets:**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

5. **Deploy app:**
   ```bash
   git push origin main
   ```

## Access

- **API**: Use ALB DNS from `terraform output alb_dns_name`
- **Logs**: `aws logs tail /ecs/incept-ml-gen --follow --region us-east-1`
- **Health**: `curl https://<alb-dns>/health`

## Custom Domain (Optional)

1. Add DNS records from `terraform output domain_validation_records`
2. Point domain to ALB: `terraform output alb_dns_name`

## Troubleshooting

- **Tasks restarting**: Check logs for startup errors
- **Environment vars missing**: Verify secrets in AWS Secrets Manager
- **Deploy fails**: Check GitHub Actions logs and AWS permissions