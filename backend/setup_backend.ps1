# Support Copilot - Backend Setup Script
# Run this from the /backend directory

Write-Host "🚀 Starting Support Copilot Backend Setup..." -ForegroundColor Cyan

# 1. Create Virtual Environment if it doesn't exist
if (-Not (Test-Path ".venv")) {
    Write-Host "📁 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "✅ Virtual environment already exists." -ForegroundColor Green
}

# 2. Upgrade pip
Write-Host "🆙 Upgrading pip..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install --upgrade pip

# 3. Install Requirements (this includes the greenlet fix)
Write-Host "📦 Installing dependencies (this may take a minute)..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Check for .env file
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file missing! Creating a template..." -ForegroundColor Magenta
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "📝 Created .env from .env.example. Please update your API keys!" -ForegroundColor Cyan
    } else {
        New-Item ".env" -ItemType File
        Write-Host "📝 Created blank .env file. Please add your GEMINI_API_KEY!" -ForegroundColor Cyan
    }
}

Write-Host "✨ Setup Complete! To start the server, run:" -ForegroundColor Green
Write-Host "   .\.venv\Scripts\python.exe main.py" -ForegroundColor White
