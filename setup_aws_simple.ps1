# Simple AWS Setup Script for Image Caption Generator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS Setup for Image Caption Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$BUCKET_NAME = "image-caption-bucket-karthik"
$REGION = "eu-north-1"
$TABLE_NAME = "image_captions"
$AWS_CLI = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"

# Check if AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Yellow
try {
    $identity = & $AWS_CLI sts get-caller-identity 2>&1 | ConvertFrom-Json
    Write-Host "SUCCESS: AWS CLI is configured" -ForegroundColor Green
    Write-Host "Account: $($identity.Account)" -ForegroundColor White
    Write-Host "User ARN: $($identity.Arn)" -ForegroundColor White
} catch {
    Write-Host "ERROR: AWS CLI is not configured properly" -ForegroundColor Red
    Write-Host "Please run: aws configure" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Creating S3 Bucket" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if bucket exists
try {
    & $AWS_CLI s3 ls "s3://$BUCKET_NAME" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Bucket '$BUCKET_NAME' already exists" -ForegroundColor Green
    }
} catch {
    Write-Host "Creating S3 bucket: $BUCKET_NAME..." -ForegroundColor Yellow
    
    # Create bucket
    & $AWS_CLI s3api create-bucket `
        --bucket $BUCKET_NAME `
        --region $REGION `
        --create-bucket-configuration LocationConstraint=$REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Bucket created!" -ForegroundColor Green
        
        # Configure public access
        Write-Host "Configuring bucket for public uploads..." -ForegroundColor Yellow
        & $AWS_CLI s3api put-public-access-block `
            --bucket $BUCKET_NAME `
            --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
        
        # Add bucket policy
        $policy = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/uploads/*"
        }
    ]
}
"@
        
        $policy | Out-File -FilePath "bucket-policy.json" -Encoding utf8
        & $AWS_CLI s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json
        Remove-Item "bucket-policy.json"
        
        Write-Host "SUCCESS: Bucket configured!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create bucket" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Creating DynamoDB Table" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if table exists
try {
    & $AWS_CLI dynamodb describe-table --table-name $TABLE_NAME --region $REGION 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Table '$TABLE_NAME' already exists" -ForegroundColor Green
    }
} catch {
    Write-Host "Creating DynamoDB table: $TABLE_NAME..." -ForegroundColor Yellow
    
    & $AWS_CLI dynamodb create-table `
        --table-name $TABLE_NAME `
        --attribute-definitions AttributeName=image_id,AttributeType=S `
        --key-schema AttributeName=image_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Table created!" -ForegroundColor Green
        Write-Host "Waiting for table to be active..." -ForegroundColor Yellow
        & $AWS_CLI dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION
        Write-Host "SUCCESS: Table is now active" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create table" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SUCCESS: AWS Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resources created:" -ForegroundColor Yellow
Write-Host "  S3 Bucket: $BUCKET_NAME" -ForegroundColor White
Write-Host "  DynamoDB Table: $TABLE_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your Streamlit app" -ForegroundColor White
Write-Host "  2. Upload an image and generate a caption" -ForegroundColor White
Write-Host "  3. Click 'Upload to S3' button" -ForegroundColor White
Write-Host "  4. Click 'Save to DynamoDB' button" -ForegroundColor White
Write-Host ""
