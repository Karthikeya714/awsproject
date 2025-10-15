# Quick AWS LocalStack Setup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AWS LOCALSTACK SETUP" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop from:" -ForegroundColor Yellow
    Write-Host "https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "After installing Docker:" -ForegroundColor Yellow
    Write-Host "1. Restart your computer" -ForegroundColor White
    Write-Host "2. Launch Docker Desktop" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Starting LocalStack..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Waiting for LocalStack to initialize (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "Installing AWS CLI tools..." -ForegroundColor Yellow
pip install awscli-local

Write-Host ""
Write-Host "Creating DynamoDB tables..." -ForegroundColor Yellow

# Create Users table
Write-Host "Creating Users table..." -ForegroundColor Cyan
awslocal dynamodb create-table `
    --table-name local-caption-metadata-users `
    --attribute-definitions `
        AttributeName=user_id,AttributeType=S `
        AttributeName=email,AttributeType=S `
    --key-schema `
        AttributeName=user_id,KeyType=HASH `
    --global-secondary-indexes `
        '[{"IndexName":"email-index","KeySchema":[{"AttributeName":"email","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":5,"WriteCapacityUnits":5}}]' `
    --provisioned-throughput `
        ReadCapacityUnits=5,WriteCapacityUnits=5 `
    --region us-east-1

Write-Host "✅ Users table created" -ForegroundColor Green

# Create Sessions table
Write-Host "Creating Sessions table..." -ForegroundColor Cyan
awslocal dynamodb create-table `
    --table-name local-caption-metadata-sessions `
    --attribute-definitions `
        AttributeName=session_id,AttributeType=S `
    --key-schema `
        AttributeName=session_id,KeyType=HASH `
    --provisioned-throughput `
        ReadCapacityUnits=5,WriteCapacityUnits=5 `
    --region us-east-1

Write-Host "✅ Sessions table created" -ForegroundColor Green

# Create Captions table
Write-Host "Creating Captions table..." -ForegroundColor Cyan
awslocal dynamodb create-table `
    --table-name local-caption-metadata `
    --attribute-definitions `
        AttributeName=PK,AttributeType=S `
        AttributeName=SK,AttributeType=S `
        AttributeName=user_id,AttributeType=S `
    --key-schema `
        AttributeName=PK,KeyType=HASH `
        AttributeName=SK,KeyType=RANGE `
    --global-secondary-indexes `
        '[{"IndexName":"user-index","KeySchema":[{"AttributeName":"user_id","KeyType":"HASH"},{"AttributeName":"SK","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":5,"WriteCapacityUnits":5}}]' `
    --provisioned-throughput `
        ReadCapacityUnits=5,WriteCapacityUnits=5 `
    --region us-east-1

Write-Host "✅ Captions table created" -ForegroundColor Green

Write-Host ""
Write-Host "Verifying tables..." -ForegroundColor Yellow
awslocal dynamodb list-tables --region us-east-1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ LocalStack is running on port 4566" -ForegroundColor Green
Write-Host "✅ DynamoDB tables created" -ForegroundColor Green
Write-Host ""
Write-Host "To run your app with DynamoDB:" -ForegroundColor Yellow
Write-Host "  python -m streamlit run app\streamlit_app_auth.py" -ForegroundColor White
Write-Host ""
Write-Host "To stop LocalStack:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
