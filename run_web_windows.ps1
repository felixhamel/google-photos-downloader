# ABOUTME: PowerShell script to launch Google Photos Downloader web app  
# ABOUTME: Modern Windows script with better error handling and Chrome auto-launch

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "🚀 Google Photos Downloader - Web Version v2.0.0" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location -Path $PSScriptRoot

# Check for credentials.json
if (-not (Test-Path "credentials.json")) {
    Write-Host "❌ ERROR: credentials.json not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Please download OAuth2 credentials from Google Cloud Console" -ForegroundColor Yellow
    Write-Host "📖 See OAUTH_GUIDE.md for detailed instructions" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Found credentials.json" -ForegroundColor Green
Write-Host ""

# Check for Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python not found!" -ForegroundColor Red
    Write-Host "📥 Please install Python from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Install dependencies
Write-Host "🔍 Checking and installing dependencies..." -ForegroundColor Yellow
Write-Host ""

try {
    if (Test-Path "requirements-web.txt") {
        Write-Host "📦 Installing from requirements-web.txt..." -ForegroundColor Cyan
        python -m pip install -r requirements-web.txt
    } else {
        Write-Host "⚡ Installing individual packages..." -ForegroundColor Cyan
        $packages = @(
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0", 
            "pydantic>=2.0.0",
            "python-multipart",
            "websockets",
            "google-auth-oauthlib>=1.0.0",
            "google-auth-httplib2>=0.2.0",
            "google-api-python-client>=2.0.0",
            "requests>=2.31.0",
            "python-dotenv"
        )
        
        foreach ($package in $packages) {
            Write-Host "Installing $package..." -ForegroundColor Gray
            python -m pip install $package
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to install $package"
            }
        }
    }
    
    Write-Host ""
    Write-Host "✅ All dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Function to open Chrome
function Open-Chrome {
    param([string]$Url)
    
    $chromePaths = @(
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
    )
    
    foreach ($chromePath in $chromePaths) {
        if (Test-Path $chromePath) {
            Write-Host "🌐 Opening Chrome at $Url..." -ForegroundColor Cyan
            Start-Process -FilePath $chromePath -ArgumentList $Url
            return $true
        }
    }
    
    # Fallback to default browser
    Write-Host "⚠️  Chrome not found, opening default browser..." -ForegroundColor Yellow
    Start-Process $Url
    return $false
}

# Start server with auto-launch
Write-Host "🌐 Starting web server..." -ForegroundColor Green
Write-Host "📱 The app will open automatically in your browser" -ForegroundColor Cyan
Write-Host "🔗 Server URL: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "⏹️  Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Gray
Write-Host ""

# Launch Chrome after a short delay
$job = Start-Job -ScriptBlock {
    Start-Sleep 3
    return "ready"
}

# Start the web application
try {
    # Start server in background job to allow Chrome launch
    $serverJob = Start-Job -ScriptBlock {
        Set-Location $using:PSScriptRoot
        python -c @"
import uvicorn
import sys

try:
    print('🚀 Server starting...')
    uvicorn.run(
        'app.main:app',
        host='127.0.0.1',
        port=8000,
        reload=True,
        log_level='info'
    )
except KeyboardInterrupt:
    print('\n🛑 Server stopped by user')
    sys.exit(0)
except Exception as e:
    print(f'❌ Error starting server: {e}')
    sys.exit(1)
"@
    }
    
    # Wait for server to initialize
    Start-Sleep 2
    
    # Open browser
    Open-Chrome "http://127.0.0.1:8000"
    
    # Wait for server job to complete (or Ctrl+C)
    Write-Host "Server is running. Press Ctrl+C to stop..." -ForegroundColor Green
    Wait-Job $serverJob | Out-Null
    
} catch {
    Write-Host "❌ Error starting server: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
} finally {
    # Cleanup jobs
    Get-Job | Stop-Job -PassThru | Remove-Job
    Write-Host ""
    Write-Host "👋 Thanks for using Google Photos Downloader!" -ForegroundColor Green
}