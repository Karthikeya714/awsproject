# AWS Setup Script for Image Caption Generator
# Run this after configuring AWS CLI with: aws configure

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS Setup for Image Caption Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$BUCKET_NAME = "image-caption-bucket-karthik"
$REGION = "eu-north-1"
$TABLE_NAME = "image_captions"

# Check if AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Yellow
$awsConfigured = $false
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        $awsConfigured = $true
        Write-Host "✅ AWS CLI is configured" -ForegroundColor Green
        $identity | ConvertFrom-Json | Format-List
    }
} catch {
    Write-Host "❌ AWS CLI is not configured" -ForegroundColor Red
}

if (-not $awsConfigured) {
    Write-Host ""
    Write-Host "Please configure AWS CLI first:" -ForegroundColor Yellow
    Write-Host "  aws configure" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You will need:" -ForegroundColor Yellow
    Write-Host "  - AWS Access Key ID" -ForegroundColor White
    Write-Host "  - AWS Secret Access Key" -ForegroundColor White
    Write-Host "  - Default region: $REGION" -ForegroundColor White
    Write-Host "  - Default output format: json" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Creating S3 Bucket" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if bucket exists
$bucketExists = $false
try {
    aws s3 ls "s3://$BUCKET_NAME" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $bucketExists = $true
        Write-Host "✅ Bucket '$BUCKET_NAME' already exists" -ForegroundColor Green
    }
} catch {}

if (-not $bucketExists) {
    Write-Host "Creating S3 bucket: $BUCKET_NAME..." -ForegroundColor Yellow
    
    # Create bucket with location constraint for eu-north-1
    aws s3api create-bucket `
        --bucket $BUCKET_NAME `
        --region $REGION `
        --create-bucket-configuration LocationConstraint=$REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Bucket created successfully!" -ForegroundColor Green
        
        # Disable block public access (needed for public-read ACL)
        Write-Host "Configuring bucket for public uploads..." -ForegroundColor Yellow
        aws s3api put-public-access-block `
            --bucket $BUCKET_NAME `
            --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
        
        # Add bucket policy to allow public read
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
        aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json
        Remove-Item "bucket-policy.json"
        
        Write-Host "✅ Bucket configured for public uploads" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create bucket" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Creating DynamoDB Table" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if table exists
$tableExists = $false
try {
    aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $tableExists = $true
        Write-Host "✅ Table '$TABLE_NAME' already exists" -ForegroundColor Green
    }
} catch {}

if (-not $tableExists) {
    Write-Host "Creating DynamoDB table: $TABLE_NAME..." -ForegroundColor Yellow
    
    aws dynamodb create-table `
        --table-name $TABLE_NAME `
        --attribute-definitions AttributeName=image_id,AttributeType=S `
        --key-schema AttributeName=image_id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Table created successfully!" -ForegroundColor Green
        Write-Host "Waiting for table to be active..." -ForegroundColor Yellow
        aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION
        Write-Host "✅ Table is now active" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create table" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ AWS Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Resources created:" -ForegroundColor Yellow
Write-Host "  📦 S3 Bucket: $BUCKET_NAME" -ForegroundColor White
Write-Host "  💾 DynamoDB Table: $TABLE_NAME" -ForegroundColor White
Write-Host "  🌍 Region: $REGION" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Update app.py with your bucket name if different" -ForegroundColor White
Write-Host "  2. Run: streamlit run app.py" -ForegroundColor Cyan
Write-Host "  3. Upload an image and test S3 + DynamoDB integration" -ForegroundColor White
Write-Host ""
