# PowerShell script to deploy to AWS EC2
# Run this on your LOCAL Windows machine

param(
    [Parameter(Mandatory=$true)]
    [string]$EC2_IP,
    
    [Parameter(Mandatory=$true)]
    [string]$KeyPairPath
)

Write-Host "🚀 Starting AWS EC2 Deployment..." -ForegroundColor Green

# Validate key file
if (-not (Test-Path $KeyPairPath)) {
    Write-Host "❌ Key file not found: $KeyPairPath" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Preparing deployment package..." -ForegroundColor Yellow

# Create deployment package
$tempDir = "$env:TEMP\streamlit-deploy"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy necessary files
$filesToCopy = @(
    "app.py",
    "aws_utils.py",
    "requirements.txt",
    "check_dynamodb.py"
)

foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $tempDir
        Write-Host "✅ Copied $file" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Warning: $file not found" -ForegroundColor Yellow
    }
}

# Create setup script
$setupScript = @"
#!/bin/bash
set -e

echo "🚀 Setting up Streamlit app on EC2..."

# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3-pip python3-venv git

# Create project directory
mkdir -p ~/streamlit-app
cd ~/streamlit-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install streamlit transformers torch pillow boto3 accelerate

# Create systemd service
sudo tee /etc/systemd/system/streamlit.service > /dev/null <<'EOF'
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
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit

# Get public IP
PUBLIC_IP=\`curl -s http://checkip.amazonaws.com\`

echo ""
echo "✅ Deployment complete!"
echo "🌐 Access your app at: http://\$PUBLIC_IP:8501"
"@

$setupScript | Out-File -FilePath "$tempDir\setup.sh" -Encoding UTF8

Write-Host "📤 Uploading files to EC2..." -ForegroundColor Yellow

# Upload files using SCP
$scpCommand = "scp"
$scpArgs = @(
    "-i", $KeyPairPath,
    "-o", "StrictHostKeyChecking=no",
    "-r", "$tempDir\*",
    "ubuntu@${EC2_IP}:~/streamlit-app/"
)

try {
    & $scpCommand $scpArgs
    Write-Host "✅ Files uploaded successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to upload files: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🔧 Running setup script on EC2..." -ForegroundColor Yellow

# Execute setup script via SSH
$sshCommand = "ssh"
$sshArgs = @(
    "-i", $KeyPairPath,
    "-o", "StrictHostKeyChecking=no",
    "ubuntu@${EC2_IP}",
    "chmod +x ~/streamlit-app/setup.sh && ~/streamlit-app/setup.sh"
)

try {
    & $sshCommand $sshArgs
    Write-Host "✅ Setup complete!" -ForegroundColor Green
} catch {
    Write-Host "❌ Setup failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 Deployment successful!" -ForegroundColor Green
Write-Host "🌐 Access your app at: http://${EC2_IP}:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Yellow
Write-Host "  Check status: ssh -i $KeyPairPath ubuntu@${EC2_IP} 'sudo systemctl status streamlit'" -ForegroundColor Gray
Write-Host "  View logs:    ssh -i $KeyPairPath ubuntu@${EC2_IP} 'sudo journalctl -u streamlit -f'" -ForegroundColor Gray
Write-Host "  Restart:      ssh -i $KeyPairPath ubuntu@${EC2_IP} 'sudo systemctl restart streamlit'" -ForegroundColor Gray

# Cleanup
Remove-Item $tempDir -Recurse -Force
