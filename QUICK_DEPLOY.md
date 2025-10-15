# 🚀 Quick Start Deployment Guide

## Choose Your Deployment Method

### 🟢 **Option 1: EC2 (Easiest for Beginners) - 15 minutes**

**Step-by-Step:**

1. **Launch EC2 Instance**
   - Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2)
   - Click "Launch Instance"
   - Choose "Ubuntu Server 22.04 LTS"
   - Instance type: `t2.small` (or `t2.micro` for free tier)
   - Click "Launch"

2. **Configure Security Group**
   - Add these inbound rules:
     - Port 22 (SSH) - Your IP
     - Port 8501 (Streamlit) - 0.0.0.0/0
   - Save

3. **Connect to EC2**
   ```bash
   ssh -i YourKey.pem ubuntu@<EC2-PUBLIC-IP>
   ```

4. **Run Deployment Script**
   ```bash
   # Upload your project files or clone from git
   cd ~
   # Copy the deploy_ec2.sh script
   chmod +x deploy_ec2.sh
   ./deploy_ec2.sh
   ```

5. **Access Your App**
   - Open: `http://<EC2-PUBLIC-IP>:8501`
   - Done! 🎉

**Cost:** ~$10-20/month (Free tier: $0 first year)

---

### 🐳 **Option 2: Docker + ECS (Production) - 30 minutes**

**Prerequisites:**
- Docker installed on your computer
- AWS CLI configured

**Steps:**

1. **Run Deployment Script** (on your local machine)
   ```bash
   chmod +x deploy_ecs.sh
   ./deploy_ecs.sh
   ```

2. **Wait for Deployment** (~5 minutes)

3. **Access Your App**
   - Script will show you the public IP
   - Open: `http://<PUBLIC-IP>:8501`

**Cost:** ~$30-40/month

---

### 🎈 **Option 3: Elastic Beanstalk (Fastest) - 10 minutes**

**Steps:**

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize and Deploy**
   ```bash
   cd awsproject-main
   eb init -p python-3.10 streamlit-app --region eu-north-1
   eb create streamlit-env --instance-type t2.small
   ```

3. **Open Your App**
   ```bash
   eb open
   ```

**Cost:** ~$15-25/month

---

## 🔑 Prerequisites (All Options)

### 1. **AWS Account**
- Sign up at [aws.amazon.com](https://aws.amazon.com)
- Free tier includes 750 hours/month of EC2 t2.micro

### 2. **AWS CLI Configured**
```bash
# Install AWS CLI
# Windows:
# Download from: https://aws.amazon.com/cli/

# Mac/Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure
aws configure
# Enter: Access Key ID
# Enter: Secret Access Key
# Region: eu-north-1
# Output: json
```

### 3. **IAM Permissions**
Your AWS user/role needs:
- `AmazonEC2FullAccess` (for EC2)
- `AmazonECS_FullAccess` (for ECS)
- `AmazonS3FullAccess` (for S3 access)
- `AmazonDynamoDBFullAccess` (for DynamoDB)
- `ElasticBeanstalkFullAccess` (for EB)

---

## 📋 Step-by-Step: EC2 Deployment (Most Popular)

### **Part 1: Create EC2 Instance**

1. Go to AWS Console → EC2
2. Click "Launch Instance"
3. **Name:** `streamlit-caption-app`
4. **AMI:** Ubuntu Server 22.04 LTS
5. **Instance Type:** t2.small (1 vCPU, 2GB RAM)
6. **Key Pair:** Create new or select existing
7. **Network Settings:**
   - Create security group
   - Add rules:
     ```
     SSH (22)      - My IP
     Custom TCP (8501) - Anywhere (0.0.0.0/0)
     ```
8. **Storage:** 8-16 GB gp3
9. Click "Launch Instance"

### **Part 2: Connect to EC2**

**Option A: EC2 Instance Connect (Browser)**
1. Select your instance
2. Click "Connect"
3. Choose "EC2 Instance Connect"
4. Click "Connect"

**Option B: SSH (Terminal)**
```bash
chmod 400 YourKey.pem
ssh -i YourKey.pem ubuntu@<PUBLIC-IP>
```

### **Part 3: Install Application**

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python and tools
sudo apt install python3-pip python3-venv git -y

# 3. Create project directory
mkdir -p ~/streamlit-app
cd ~/streamlit-app

# 4. Upload your files (choose one method):

# Method A: Using SCP from local machine
# scp -i YourKey.pem -r awsproject-main ubuntu@<EC2-IP>:~/streamlit-app/

# Method B: Git clone
# git clone <your-repo-url> .

# Method C: Manual upload via AWS Console (slow)

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install --upgrade pip
pip install streamlit transformers torch pillow boto3 accelerate

# 7. Configure AWS (skip if using IAM role)
aws configure
# Enter your credentials

# 8. Test the app
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### **Part 4: Make it Run 24/7**

```bash
# Stop test (Ctrl+C)

# Create systemd service
sudo nano /etc/systemd/system/streamlit.service
```

**Paste this:**
```ini
[Unit]
Description=Streamlit Caption App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/streamlit-app
Environment="PATH=/home/ubuntu/streamlit-app/venv/bin"
ExecStart=/home/ubuntu/streamlit-app/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
sudo systemctl status streamlit
```

### **Part 5: Access Your App**

```bash
# Get your public IP
curl http://checkip.amazonaws.com
```

**Open in browser:** `http://<PUBLIC-IP>:8501`

**Done!** 🎉

---

## 🛠️ Useful Commands

### **EC2 Management:**
```bash
# Check app status
sudo systemctl status streamlit

# View logs
sudo journalctl -u streamlit -f

# Restart app
sudo systemctl restart streamlit

# Stop app
sudo systemctl stop streamlit

# Update app
cd ~/streamlit-app
git pull  # or upload new files
sudo systemctl restart streamlit
```

### **ECS Management:**
```bash
# List tasks
aws ecs list-tasks --cluster streamlit-cluster

# View logs
aws logs tail /ecs/streamlit-app-task --follow

# Scale up
aws ecs update-service --cluster streamlit-cluster --service streamlit-service --desired-count 2

# Stop service
aws ecs update-service --cluster streamlit-cluster --service streamlit-service --desired-count 0
```

### **Elastic Beanstalk:**
```bash
# Deploy updates
eb deploy

# Check status
eb status

# View logs
eb logs

# SSH into instance
eb ssh

# Terminate environment
eb terminate streamlit-env
```

---

## 🔒 Security Best Practices

### 1. **Use IAM Roles (Recommended)**
Instead of storing AWS credentials on EC2:
1. Create IAM role with S3 and DynamoDB permissions
2. Attach to EC2 instance
3. No need for `aws configure`

### 2. **Restrict Security Group**
- Only allow port 8501 from necessary IPs
- Use VPN or bastion host for SSH

### 3. **Enable HTTPS**
```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Get SSL certificate (requires domain)
sudo certbot --nginx -d yourdomain.com
```

### 4. **Environment Variables**
Store secrets in environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

---

## 💰 Cost Breakdown

### **EC2 Deployment:**
```
Instance (t2.small):      $17/month
Storage (16GB):           $1.60/month
Data Transfer (10GB):     $0.90/month
Elastic IP:               $3.60/month (if stopped)
--------------------------------
Total:                    ~$20/month

Free Tier (first year):   $0 (with t2.micro)
```

### **ECS Fargate:**
```
CPU (0.5 vCPU):          $14.70/month
Memory (2GB):            $3.22/month
Load Balancer:           $16.20/month
Data Transfer:           $0.90/month
--------------------------------
Total:                   ~$35/month
```

### **Elastic Beanstalk:**
```
EC2 instance:            $17/month
Load Balancer:           $16.20/month (optional)
Data Transfer:           $0.90/month
--------------------------------
Total:                   ~$18-35/month
```

---

## 🐛 Troubleshooting

### **App not loading:**
```bash
# Check if app is running
sudo systemctl status streamlit

# Check logs
sudo journalctl -u streamlit -n 50

# Check port
sudo netstat -tulpn | grep 8501

# Test locally
curl http://localhost:8501/_stcore/health
```

### **Cannot connect:**
- Check Security Group allows port 8501
- Check firewall: `sudo ufw status`
- Verify public IP is correct

### **AWS credentials error:**
```bash
# Verify credentials
aws sts get-caller-identity

# Reconfigure
aws configure
```

### **Out of memory:**
```bash
# Check memory
free -h

# Upgrade to larger instance type (t2.medium)
```

---

## 📞 Support

### **AWS Resources:**
- [EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Elastic Beanstalk Guide](https://docs.aws.amazon.com/elasticbeanstalk/)

### **Community:**
- [Streamlit Forum](https://discuss.streamlit.io/)
- [AWS Forums](https://forums.aws.amazon.com/)

---

## ✅ Checklist

Before deploying:
- [ ] AWS account created
- [ ] AWS CLI installed and configured
- [ ] IAM permissions set up
- [ ] S3 bucket created
- [ ] DynamoDB table created (or app will create)
- [ ] Code tested locally
- [ ] requirements.txt updated

After deploying:
- [ ] App accessible via public URL
- [ ] Can upload images successfully
- [ ] S3 upload works
- [ ] DynamoDB save works
- [ ] App restarts automatically

---

## 🎉 Success!

Your app is now live on AWS!

**Next Steps:**
1. Set up custom domain
2. Enable HTTPS with SSL
3. Set up monitoring and alerts
4. Configure auto-scaling
5. Set up CI/CD pipeline

---

**Need help?** Check [AWS_DEPLOYMENT_GUIDE.md](AWS_DEPLOYMENT_GUIDE.md) for detailed information!
