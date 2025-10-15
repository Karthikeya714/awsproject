#!/bin/bash
# Docker + ECS Deployment Script
# Run this on your local machine

set -e

# Configuration
AWS_REGION="eu-north-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="streamlit-caption-app"
ECS_CLUSTER_NAME="streamlit-cluster"
ECS_SERVICE_NAME="streamlit-service"
TASK_FAMILY="streamlit-app-task"

echo "🚀 Starting Docker + ECS Deployment..."
echo "📍 AWS Account: $AWS_ACCOUNT_ID"
echo "🌍 Region: $AWS_REGION"

# Step 1: Create ECR repository
echo ""
echo "📦 Step 1: Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"
echo "✅ ECR Repository: $ECR_URI"

# Step 2: Build Docker image
echo ""
echo "🐳 Step 2: Building Docker image..."
docker build -t $ECR_REPO_NAME:latest .
docker tag $ECR_REPO_NAME:latest $ECR_URI:latest

# Step 3: Login to ECR
echo ""
echo "🔑 Step 3: Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Step 4: Push image to ECR
echo ""
echo "📤 Step 4: Pushing image to ECR..."
docker push $ECR_URI:latest
echo "✅ Image pushed successfully!"

# Step 5: Create ECS cluster
echo ""
echo "🏗️ Step 5: Creating ECS cluster..."
aws ecs describe-clusters --clusters $ECS_CLUSTER_NAME --region $AWS_REGION 2>/dev/null || \
aws ecs create-cluster --cluster-name $ECS_CLUSTER_NAME --region $AWS_REGION
echo "✅ ECS Cluster created/verified"

# Step 6: Create CloudWatch Log Group
echo ""
echo "📝 Step 6: Creating CloudWatch log group..."
aws logs create-log-group --log-group-name /ecs/$TASK_FAMILY --region $AWS_REGION 2>/dev/null || echo "Log group already exists"

# Step 7: Register task definition
echo ""
echo "📋 Step 7: Registering ECS task definition..."
cat > task-definition.json <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "streamlit-container",
      "image": "$ECR_URI:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$TASK_FAMILY",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "AWS_DEFAULT_REGION",
          "value": "$AWS_REGION"
        }
      ]
    }
  ]
}
EOF

aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION
echo "✅ Task definition registered"

# Step 8: Create or update service
echo ""
echo "🚀 Step 8: Creating/Updating ECS service..."

# Get default VPC and subnets
DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWS_REGION)
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DEFAULT_VPC" --query "Subnets[*].SubnetId" --output text --region $AWS_REGION | tr '\t' ',')
SECURITY_GROUP=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$DEFAULT_VPC" "Name=group-name,Values=default" --query "SecurityGroups[0].GroupId" --output text --region $AWS_REGION)

echo "VPC: $DEFAULT_VPC"
echo "Subnets: $SUBNETS"
echo "Security Group: $SECURITY_GROUP"

# Check if service exists
if aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $ECS_SERVICE_NAME --region $AWS_REGION 2>/dev/null | grep -q "ACTIVE"; then
    echo "Updating existing service..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER_NAME \
        --service $ECS_SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --region $AWS_REGION
else
    echo "Creating new service..."
    aws ecs create-service \
        --cluster $ECS_CLUSTER_NAME \
        --service-name $ECS_SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" \
        --region $AWS_REGION
fi

echo "✅ Service created/updated"

# Step 9: Get service info
echo ""
echo "📊 Step 9: Getting service information..."
sleep 5

TASK_ARN=$(aws ecs list-tasks --cluster $ECS_CLUSTER_NAME --service-name $ECS_SERVICE_NAME --region $AWS_REGION --query "taskArns[0]" --output text)
if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
    ENI_ID=$(aws ecs describe-tasks --cluster $ECS_CLUSTER_NAME --tasks $TASK_ARN --region $AWS_REGION --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text)
    PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region $AWS_REGION --query "NetworkInterfaces[0].Association.PublicIp" --output text)
    
    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 Access your app at: http://$PUBLIC_IP:8501"
    echo ""
    echo "📝 Note: It may take 1-2 minutes for the app to start"
else
    echo "⏳ Task is starting... Run this command to get the public IP:"
    echo "aws ecs list-tasks --cluster $ECS_CLUSTER_NAME --service-name $ECS_SERVICE_NAME --region $AWS_REGION"
fi

echo ""
echo "📋 Useful commands:"
echo "  - View tasks: aws ecs list-tasks --cluster $ECS_CLUSTER_NAME --region $AWS_REGION"
echo "  - View logs: aws logs tail /ecs/$TASK_FAMILY --follow --region $AWS_REGION"
echo "  - Scale service: aws ecs update-service --cluster $ECS_CLUSTER_NAME --service $ECS_SERVICE_NAME --desired-count 2 --region $AWS_REGION"

# Cleanup
rm -f task-definition.json
