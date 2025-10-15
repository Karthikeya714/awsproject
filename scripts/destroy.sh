#!/bin/bash
# Destroy infrastructure for Image Caption Generator
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}
PROJECT_NAME="image-caption-gen"

echo -e "${RED}================================================${NC}"
echo -e "${RED}WARNING: This will destroy all infrastructure!${NC}"
echo -e "${RED}================================================${NC}"
echo -e "Environment: ${ENVIRONMENT}"
echo -e "Region: ${AWS_REGION}"
echo ""

# Confirmation
read -p "Type 'DESTROY' to confirm: " -r
if [[ ! $REPLY == "DESTROY" ]]; then
    echo -e "${YELLOW}Destruction cancelled${NC}"
    exit 0
fi

# Additional confirmation for production
if [[ "$ENVIRONMENT" == "prod" ]]; then
    echo -e "${RED}This is PRODUCTION environment!${NC}"
    read -p "Type 'DESTROY PRODUCTION' to confirm: " -r
    if [[ ! $REPLY == "DESTROY PRODUCTION" ]]; then
        echo -e "${YELLOW}Destruction cancelled${NC}"
        exit 0
    fi
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Step 1: Empty S3 bucket
echo -e "${YELLOW}Emptying S3 bucket...${NC}"
S3_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-images"
aws s3 rm s3://${S3_BUCKET} --recursive --region ${AWS_REGION} || true

# Step 2: Delete ECR images
echo -e "${YELLOW}Deleting ECR images...${NC}"
ECR_REPO="${PROJECT_NAME}-${ENVIRONMENT}"
aws ecr batch-delete-image \
    --repository-name ${ECR_REPO} \
    --image-ids "$(aws ecr list-images --repository-name ${ECR_REPO} --query 'imageIds[*]' --output json)" \
    --region ${AWS_REGION} || true

# Step 3: Delete CloudWatch log groups
echo -e "${YELLOW}Deleting CloudWatch log groups...${NC}"
LOG_GROUP="/ecs/${PROJECT_NAME}-${ENVIRONMENT}"
aws logs delete-log-group --log-group-name ${LOG_GROUP} --region ${AWS_REGION} || true

# Step 4: Destroy Terraform infrastructure
echo -e "${YELLOW}Destroying Terraform infrastructure...${NC}"
cd infra/terraform

terraform destroy \
    -var="environment=${ENVIRONMENT}" \
    -var="aws_region=${AWS_REGION}" \
    -auto-approve

cd ../..

echo ""
echo -e "${GREEN}===============================${NC}"
echo -e "${GREEN}Infrastructure destroyed successfully!${NC}"
echo -e "${GREEN}===============================${NC}"
echo ""
echo -e "${YELLOW}Manual cleanup required:${NC}"
echo -e "1. Verify S3 bucket is deleted"
echo -e "2. Check for any remaining CloudWatch alarms"
echo -e "3. Review IAM roles if needed"
echo ""
