# Quick Real AWS Setup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  REAL AWS SETUP" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✅ AWS CLI configured" -ForegroundColor Green
    Write-Host "   Account: $($identity.Account)" -ForegroundColor Cyan
    Write-Host "   User: $($identity.Arn)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ AWS CLI not configured!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run: aws configure" -ForegroundColor Yellow
    Write-Host "Then enter your AWS credentials" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
$confirm = Read-Host "This will create AWS resources that may cost money. Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Setup cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Creating DynamoDB tables..." -ForegroundColor Yellow

# Create Users table
Write-Host "Creating Users table..." -ForegroundColor Cyan
aws dynamodb create-table `
    --table-name caption-users `
    --attribute-definitions `
        AttributeName=user_id,AttributeType=S `
        AttributeName=email,AttributeType=S `
    --key-schema `
        AttributeName=user_id,KeyType=HASH `
    --global-secondary-indexes `
        '[{"IndexName":"email-index","KeySchema":[{"AttributeName":"email","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}}]' `
    --billing-mode PAY_PER_REQUEST `
    --region us-east-1

Write-Host "✅ Users table created" -ForegroundColor Green
Start-Sleep -Seconds 5

# Create Sessions table
Write-Host "Creating Sessions table..." -ForegroundColor Cyan
aws dynamodb create-table `
    --table-name caption-sessions `
    --attribute-definitions `
        AttributeName=session_id,AttributeType=S `
    --key-schema `
        AttributeName=session_id,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST `
    --region us-east-1

Write-Host "✅ Sessions table created" -ForegroundColor Green
Start-Sleep -Seconds 5

# Create Captions table
Write-Host "Creating Captions table..." -ForegroundColor Cyan
aws dynamodb create-table `
    --table-name caption-metadata `
    --attribute-definitions `
        AttributeName=PK,AttributeType=S `
        AttributeName=SK,AttributeType=S `
        AttributeName=user_id,AttributeType=S `
    --key-schema `
        AttributeName=PK,KeyType=HASH `
        AttributeName=SK,KeyType=RANGE `
    --global-secondary-indexes `
        '[{"IndexName":"user-index","KeySchema":[{"AttributeName":"user_id","KeyType":"HASH"},{"AttributeName":"SK","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' `
    --billing-mode PAY_PER_REQUEST `
    --region us-east-1

Write-Host "✅ Captions table created" -ForegroundColor Green

Write-Host ""
Write-Host "Creating S3 bucket..." -ForegroundColor Yellow
$bucketName = Read-Host "Enter a UNIQUE bucket name (e.g., yourname-caption-images-2025)"

aws s3 mb s3://$bucketName --region us-east-1
aws s3api put-bucket-versioning --bucket $bucketName --versioning-configuration Status=Enabled
aws s3api put-public-access-block --bucket $bucketName --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

Write-Host "✅ S3 bucket created: $bucketName" -ForegroundColor Green

Write-Host ""
Write-Host "Verifying resources..." -ForegroundColor Yellow
Write-Host "DynamoDB Tables:" -ForegroundColor Cyan
aws dynamodb list-tables --region us-east-1

Write-Host ""
Write-Host "S3 Buckets:" -ForegroundColor Cyan
aws s3 ls

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ DynamoDB tables created in us-east-1" -ForegroundColor Green
Write-Host "✅ S3 bucket created: $bucketName" -ForegroundColor Green
Write-Host ""
Write-Host "Now update your .env file:" -ForegroundColor Yellow
Write-Host "  S3_BUCKET_NAME=$bucketName" -ForegroundColor White
Write-Host "  DYNAMODB_TABLE_NAME=caption-metadata" -ForegroundColor White
Write-Host "  ENVIRONMENT=production" -ForegroundColor White
Write-Host ""
Write-Host "Then run:" -ForegroundColor Yellow
Write-Host "  python -m streamlit run app\streamlit_app_auth.py" -ForegroundColor White
Write-Host ""
Write-Host "💰 Cost Estimate: ~$1-5/month for small usage" -ForegroundColor Cyan
Write-Host ""
