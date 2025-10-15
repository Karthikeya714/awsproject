#!/bin/bash
# EC2 Deployment Script
# Run this script on your EC2 instance

set -e

echo "🚀 Starting Streamlit App Deployment on EC2..."

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3-pip python3-venv git

# Create project directory
echo "📁 Creating project directory..."
cd ~
mkdir -p streamlit-app
cd streamlit-app

# Clone repository (modify with your repo URL)
echo "📥 Cloning repository..."
# git clone https://github.com/JAYASHISH05/Pulse-point.git .
# OR copy files manually

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install streamlit transformers torch pillow boto3 accelerate

# Configure AWS credentials (if not using IAM role)
echo "🔑 Configuring AWS credentials..."
if [ ! -f ~/.aws/credentials ]; then
    echo "Setting up AWS credentials..."
    aws configure
else
    echo "AWS credentials already configured"
fi

# Test the application
echo "🧪 Testing application..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 10
if curl -f http://localhost:8501/_stcore/health; then
    echo "✅ Application is healthy!"
    kill %1
else
    echo "❌ Application health check failed"
    kill %1
    exit 1
fi

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<EOF
[Unit]
Description=Streamlit Caption Generator App
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/streamlit-app
Environment="PATH=$HOME/streamlit-app/venv/bin"
ExecStart=$HOME/streamlit-app/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Starting Streamlit service..."
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit

# Check status
echo "📊 Checking service status..."
sudo systemctl status streamlit --no-pager

# Get public IP
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)

echo ""
echo "✅ Deployment complete!"
echo "🌐 Access your app at: http://$PUBLIC_IP:8501"
echo ""
echo "📝 Useful commands:"
echo "  - Check status: sudo systemctl status streamlit"
echo "  - View logs: sudo journalctl -u streamlit -f"
echo "  - Restart: sudo systemctl restart streamlit"
echo "  - Stop: sudo systemctl stop streamlit"
