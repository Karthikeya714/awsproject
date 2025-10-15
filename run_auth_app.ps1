# Run the Image Caption Generator with Authentication
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IMAGE CAPTION GENERATOR - AUTH APP" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting application with LOGIN/SIGNUP pages..." -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ You will see: SIGNIN page first" -ForegroundColor Green
Write-Host "✅ Click 'Create Account' to see SIGNUP page" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the app" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
Set-Location d:\genaiproject

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the auth app
streamlit run app\streamlit_app_auth.py
