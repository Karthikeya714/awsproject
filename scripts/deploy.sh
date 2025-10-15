#!/bin/bash
# Deployment script for Image Caption Generator
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

echo -e "${GREEN}Starting deployment for environment: ${ENVIRONMENT}${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Environment must be dev, staging, or prod${NC}"
    exit 1
fi

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI is required but not installed${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed${NC}"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo -e "${RED}Terraform is required but not installed${NC}"; exit 1; }

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"

# ECR repository URL
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-${ENVIRONMENT}"

# Step 1: Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Step 2: Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
IMAGE_TAG=$(git rev-parse --short HEAD)
docker build -t ${PROJECT_NAME}:${IMAGE_TAG} -t ${PROJECT_NAME}:latest .

# Step 3: Tag image
echo -e "${YELLOW}Tagging image...${NC}"
docker tag ${PROJECT_NAME}:${IMAGE_TAG} ${ECR_REPO}:${IMAGE_TAG}
docker tag ${PROJECT_NAME}:latest ${ECR_REPO}:latest

# Step 4: Push to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push ${ECR_REPO}:${IMAGE_TAG}
docker push ${ECR_REPO}:latest

# Step 5: Deploy infrastructure with Terraform
echo -e "${YELLOW}Deploying infrastructure with Terraform...${NC}"
cd infra/terraform

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo -e "${YELLOW}Initializing Terraform...${NC}"
    terraform init \
        -backend-config="bucket=${TF_STATE_BUCKET:-terraform-state-${AWS_ACCOUNT_ID}}" \
        -backend-config="key=${PROJECT_NAME}/${ENVIRONMENT}/terraform.tfstate" \
        -backend-config="region=${AWS_REGION}" \
        -backend-config="dynamodb_table=${TF_STATE_LOCK_TABLE:-terraform-state-lock}"
fi

# Plan
echo -e "${YELLOW}Running Terraform plan...${NC}"
terraform plan \
    -var="environment=${ENVIRONMENT}" \
    -var="aws_region=${AWS_REGION}" \
    -out=tfplan

# Apply
read -p "Apply Terraform changes? (yes/no): " -n 3 -r
echo
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    terraform apply tfplan
else
    echo -e "${YELLOW}Terraform apply skipped${NC}"
    exit 0
fi

cd ../..

# Step 6: Update ECS service
echo -e "${YELLOW}Updating ECS service...${NC}"
CLUSTER_NAME="${PROJECT_NAME}-cluster-${ENVIRONMENT}"
SERVICE_NAME="${PROJECT_NAME}-service-${ENVIRONMENT}"

aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --force-new-deployment \
    --region ${AWS_REGION}

# Step 7: Wait for service to stabilize
echo -e "${YELLOW}Waiting for service to stabilize...${NC}"
aws ecs wait services-stable \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --region ${AWS_REGION}

# Step 8: Get application URL
echo -e "${YELLOW}Getting application URL...${NC}"
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names "${PROJECT_NAME}-alb-${ENVIRONMENT}" \
    --query 'LoadBalancers[0].DNSName' \
    --output text \
    --region ${AWS_REGION})

# Step 9: Health check
echo -e "${YELLOW}Performing health check...${NC}"
HEALTH_URL="http://${ALB_DNS}/_stcore/health"

for i in {1..10}; do
    if curl -f -s ${HEALTH_URL} > /dev/null; then
        echo -e "${GREEN}Health check passed!${NC}"
        break
    else
        echo -e "${YELLOW}Waiting for application to be healthy... (attempt $i/10)${NC}"
        sleep 10
    fi
done

# Final output
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "Environment: ${ENVIRONMENT}"
echo -e "Image: ${ECR_REPO}:${IMAGE_TAG}"
echo -e "Application URL: http://${ALB_DNS}"
echo -e "Health Check: ${HEALTH_URL}"
echo ""
echo -e "${YELLOW}CloudWatch Dashboard:${NC}"
echo -e "https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${PROJECT_NAME}-${ENVIRONMENT}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Verify application is working: http://${ALB_DNS}"
echo -e "2. Run smoke tests: pytest tests/e2e_smoke.py"
echo -e "3. Monitor CloudWatch dashboard"
echo ""
