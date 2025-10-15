# 🚀 AWS Deployment Guide - Host Your Streamlit App

## 📋 Table of Contents
1. [Deployment Options](#deployment-options)
2. [Option 1: EC2 (Recommended for Beginners)](#option-1-ec2-recommended)
3. [Option 2: ECS with Fargate (Serverless)](#option-2-ecs-fargate)
4. [Option 3: Elastic Beanstalk (Easiest)](#option-3-elastic-beanstalk)
5. [Setup Steps](#setup-steps)
6. [Cost Estimates](#cost-estimates)

---

## 🎯 Deployment Options Comparison

| Option | Difficulty | Cost/Month | Best For | Scalability |
|--------|-----------|------------|----------|-------------|
| **EC2** | Easy | $10-20 | Learning, small apps | Manual |
| **ECS Fargate** | Medium | $15-30 | Production, auto-scale | Automatic |
| **Elastic Beanstalk** | Easiest | $10-25 | Quick deployment | Automatic |
| **App Runner** | Easy | $5-15 | Minimal config | Automatic |

**Recommendation:** Start with **EC2** for learning, then move to **ECS Fargate** for production.

---

## 🖥️ Option 1: EC2 (Recommended for Beginners)

### **What is EC2?**
Virtual server in the cloud - like renting a computer that runs 24/7.

### **Steps:**

#### **Step 1: Launch EC2 Instance**

```bash
# Using AWS CLI (or use AWS Console)
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t2.micro \
    --key-name YourKeyPair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=StreamlitApp}]'
```

**Or using AWS Console:**
1. Go to EC2 Dashboard → Launch Instance
2. Choose **Ubuntu Server 22.04 LTS**
3. Instance type: **t2.small** (free tier: t2.micro)
4. Configure Security Group (see below)
5. Create/select Key Pair
6. Launch!

#### **Step 2: Configure Security Group**

**Inbound Rules:**
```
Port 22   (SSH)      - Your IP (for access)
Port 8501 (Streamlit) - 0.0.0.0/0 (public access)
Port 80   (HTTP)     - 0.0.0.0/0 (optional)
Port 443  (HTTPS)    - 0.0.0.0/0 (optional)
```

**AWS Console Steps:**
1. EC2 → Security Groups → Create Security Group
2. Add inbound rules above
3. Attach to your EC2 instance

#### **Step 3: Connect to EC2**

```bash
# Download your .pem key file, then:
chmod 400 YourKeyPair.pem
ssh -i YourKeyPair.pem ubuntu@<EC2-PUBLIC-IP>
```

**Or use EC2 Instance Connect** (browser-based SSH)

#### **Step 4: Install Dependencies on EC2**

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3-pip python3-venv -y

# Install Git
sudo apt install git -y

# Clone your repository (or upload files)
git clone https://github.com/JAYASHISH05/Pulse-point.git
cd Pulse-point

# Or upload via SCP from your local machine:
# scp -i YourKeyPair.pem -r awsproject-main ubuntu@<EC2-IP>:~/
```

#### **Step 5: Setup Python Environment**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install streamlit transformers torch pillow boto3 accelerate

# Or if you have requirements.txt:
pip install -r requirements.txt
```

#### **Step 6: Configure AWS Credentials on EC2**

**Option A: IAM Role (Recommended)**
1. Go to IAM → Roles → Create Role
2. Select "AWS Service" → "EC2"
3. Add policies:
   - `AmazonS3FullAccess`
   - `AmazonDynamoDBFullAccess`
4. Attach role to EC2 instance

**Option B: Configure credentials manually**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Region: eu-north-1
# Output format: json
```

#### **Step 7: Test the App**

```bash
cd awsproject-main
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

**Access:** `http://<EC2-PUBLIC-IP>:8501`

#### **Step 8: Run App as Background Service**

Create systemd service for auto-restart:

```bash
sudo nano /etc/systemd/system/streamlit.service
```

**Paste this:**
```ini
[Unit]
Description=Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/awsproject-main
Environment="PATH=/home/ubuntu/venv/bin"
ExecStart=/home/ubuntu/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
sudo systemctl status streamlit
```

**Your app is now running 24/7!** 🎉

#### **Step 9: (Optional) Setup Domain & HTTPS**

**Get a domain:** (e.g., from Route 53, Namecheap, etc.)

**Install Nginx as reverse proxy:**
```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/streamlit
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/streamlit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Install SSL certificate (free with Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

**Now access at:** `https://your-domain.com` 🔒

---

## 🐳 Option 2: ECS with Fargate (Production-Ready)

### **What is ECS Fargate?**
Serverless container service - no server management needed.

### **Prerequisites:**
1. Docker installed locally
2. AWS CLI configured
3. ECR repository created

### **Step 1: Create Dockerfile**

Create `Dockerfile` in your project root:

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **Step 2: Create requirements.txt**

```txt
streamlit>=1.28.0
transformers>=4.30.0
torch>=2.0.0
pillow>=9.5.0
boto3>=1.28.0
accelerate>=0.20.0
```

### **Step 3: Build and Test Docker Image**

```bash
# Build image
docker build -t streamlit-caption-app .

# Test locally
docker run -p 8501:8501 streamlit-caption-app

# Access: http://localhost:8501
```

### **Step 4: Push to Amazon ECR**

```bash
# Create ECR repository
aws ecr create-repository --repository-name streamlit-caption-app --region eu-north-1

# Get login token
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin <YOUR-AWS-ACCOUNT-ID>.dkr.ecr.eu-north-1.amazonaws.com

# Tag image
docker tag streamlit-caption-app:latest <YOUR-AWS-ACCOUNT-ID>.dkr.ecr.eu-north-1.amazonaws.com/streamlit-caption-app:latest

# Push to ECR
docker push <YOUR-AWS-ACCOUNT-ID>.dkr.ecr.eu-north-1.amazonaws.com/streamlit-caption-app:latest
```

### **Step 5: Create ECS Cluster**

```bash
# Create cluster
aws ecs create-cluster --cluster-name streamlit-cluster --region eu-north-1
```

**Or use AWS Console:**
1. ECS → Clusters → Create Cluster
2. Choose "Networking only" (Fargate)
3. Name: `streamlit-cluster`

### **Step 6: Create Task Definition**

Create `task-definition.json`:

```json
{
  "family": "streamlit-app-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<ACCOUNT-ID>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<ACCOUNT-ID>:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "streamlit-container",
      "image": "<ACCOUNT-ID>.dkr.ecr.eu-north-1.amazonaws.com/streamlit-caption-app:latest",
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
          "awslogs-group": "/ecs/streamlit-app",
          "awslogs-region": "eu-north-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Register task:**
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### **Step 7: Create ECS Service with Load Balancer**

```bash
# Create Application Load Balancer (ALB)
aws elbv2 create-load-balancer \
    --name streamlit-alb \
    --subnets subnet-xxxxx subnet-yyyyy \
    --security-groups sg-xxxxxxxx

# Create target group
aws elbv2 create-target-group \
    --name streamlit-target-group \
    --protocol HTTP \
    --port 8501 \
    --vpc-id vpc-xxxxxxxx \
    --target-type ip \
    --health-check-path /_stcore/health

# Create ECS Service
aws ecs create-service \
    --cluster streamlit-cluster \
    --service-name streamlit-service \
    --task-definition streamlit-app-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxxxxx],assignPublicIp=ENABLED}" \
    --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=streamlit-container,containerPort=8501
```

**Access via ALB DNS:** `http://<ALB-DNS-NAME>`

---

## 🎈 Option 3: Elastic Beanstalk (Easiest!)

### **What is Elastic Beanstalk?**
Platform-as-a-Service (PaaS) - upload code, AWS handles the rest.

### **Step 1: Install EB CLI**

```bash
pip install awsebcli
```

### **Step 2: Initialize Elastic Beanstalk**

```bash
cd awsproject-main
eb init -p python-3.10 streamlit-caption-app --region eu-north-1
```

### **Step 3: Create Procfile**

Create `Procfile` in project root:

```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### **Step 4: Create .ebextensions config**

Create `.ebextensions/python.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:application
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: static
```

### **Step 5: Deploy**

```bash
# Create environment and deploy
eb create streamlit-env --instance-type t2.small

# Deploy updates later:
eb deploy

# Open app in browser:
eb open
```

**That's it!** 🎉 Elastic Beanstalk handles everything.

---

## 📦 Option 4: AWS App Runner (Simplest!)

### **What is App Runner?**
Fully managed service - just point to code, it deploys automatically.

### **Step 1: Create apprunner.yaml**

```yaml
version: 1.0
runtime: python3
build:
  commands:
    pre-build:
      - pip install --upgrade pip
    build:
      - pip install -r requirements.txt
run:
  command: streamlit run app.py --server.port=8080 --server.address=0.0.0.0
  network:
    port: 8080
```

### **Step 2: Deploy via Console**

1. Go to AWS App Runner
2. Create Service
3. Source: ECR or GitHub
4. Select your repository
5. Deploy!

**Cost:** Starting at ~$5/month

---

## 💰 Cost Estimates (Monthly)

### **EC2 Deployment:**
```
t2.micro (free tier):  $0 (first year)
t2.small:              $17
Elastic IP:            $3.60
Data Transfer (10GB):  $0.90
Total:                 ~$10-22/month
```

### **ECS Fargate:**
```
Fargate vCPU (0.5):    $14.70
Fargate Memory (2GB):  $3.22
ALB:                   $16.20
Data Transfer:         $0.90
Total:                 ~$35/month
```

### **Elastic Beanstalk:**
```
t2.small instance:     $17
Load Balancer:         $16.20 (optional)
Data Transfer:         $0.90
Total:                 ~$17-35/month
```

### **App Runner:**
```
Active time:           $5-15
Build time:            $1-3
Total:                 ~$6-18/month
```

**Free Tier Benefits:**
- EC2: 750 hours/month free (first year)
- S3: 5GB storage free
- DynamoDB: 25GB storage free

---

## 🔧 Setup Scripts

I'll create automated setup scripts for you:
