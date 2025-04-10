# Set console encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Clear-Host

# ===============================
# Check if Python is installed
# ===============================
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Write-Host "Python is not installed. Downloading the installer..." -ForegroundColor Yellow
    $installerUrl = "https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe"
    $installerPath = "python_installer.exe"
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
    Write-Host "Installing Python..." -ForegroundColor Yellow
    Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    Remove-Item $installerPath
    Write-Host "Python installed successfully." -ForegroundColor Green
} else {
    Write-Host "Python is already installed." -ForegroundColor Green
}

# =============================================================
# Upgrade pip and install required libraries (spotipy, ytmusicapi)
# =============================================================
Write-Host "Installing/upgrading pip and required libraries..."
& python -m pip install --upgrade pip --no-warn-script-location | Out-Null
& pip install spotipy ytmusicapi --no-warn-script-location | Out-Null

# ========================================
# Spotify API Setup Instructions
# ========================================
Write-Host "======================================================"
Write-Host "      Spotify API Setup Instructions"
Write-Host "======================================================"
Write-Host ""
Write-Host "1. Go to the following URL and ensure you are logged in:"
Write-Host "   https://developer.spotify.com/dashboard/applications/"
Write-Host ""
Write-Host "2. Create a new application with any name and description."
Write-Host ""
Write-Host "3. In your app settings, add the following Redirect URI:"
Write-Host "   http://127.0.0.1:8888/callback"
Write-Host ""
Write-Host "4. Select 'Web API' and 'Web Playback SDK' under 'Which API/SDKs are you planning to use?',"
Write-Host "   accept the Terms of Service, and save."
Write-Host ""
Write-Host "5. Go to settings (top right), copy your Client ID, click 'View Client Secret', and copy that as well."
Write-Host ""
Pause

# --------------------------
# Prompt user for input
# --------------------------
$client_id = Read-Host "Enter your Spotify Client ID"
$client_secret = Read-Host "Enter your Spotify Client Secret"

# ---------------------------------------
# Create the "config" directory if it doesn't exist
# ---------------------------------------
$configDir = "config"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
}

# --------------------------------------------------
# Create the spotify_auth.json file in the config directory
# (Utilizes PowerShell's native JSON support)
# --------------------------------------------------
$spotifyAuth = @{
    client_id     = $client_id
    client_secret = $client_secret
}
$spotifyAuth | ConvertTo-Json -Depth 3 | Out-File -Encoding UTF8 "$configDir\spotify_auth.json"

Write-Host ""
Write-Host "spotify_auth.json has been created in the config directory." -ForegroundColor Green

# ===============================
# YouTube Music API Setup
# ===============================
Clear-Host
Write-Host "======================================================"
Write-Host "      YouTube Music API Setup Instructions"
Write-Host "======================================================"
Write-Host ""
Write-Host "1. Go to: https://console.cloud.google.com/ and ensure you're logged in with your Google account."
Write-Host ""
Write-Host "2. Click the project selector dropdown (top-left)"
Write-Host "   - Create a New Project with any name."
Write-Host ""
Write-Host "3. Enable YouTube Data API v3:"
Write-Host "   - Left menu > APIs & Services > Library"
Write-Host "   - Search 'YouTube Data API v3' > ENABLE"
Write-Host ""
Write-Host "4. Configure OAuth Consent Screen:"
Write-Host "   - Left menu > APIs & Services > OAuth consent screen"
Write-Host "   - If the Auth Platform isn't configured yet, press Start and select as follows:"
Write-Host "       - App name: Any name | User support email: Your email"
Write-Host "       - User Type: External > Create"
Write-Host "       - Developer contact email: Your email > Save and Continue"
Write-Host "   - Left menu > Public > scroll until you see 'Test Users' and add your email, then save."
Write-Host ""
Write-Host "5. Create OAuth Credentials:"
Write-Host "   - Left menu > Credentials > Create Credentials > OAuth client ID"
Write-Host "   - Application type: TVs and Limited Input"
Write-Host "   - Name: Any name > Create"
Write-Host "   - Click 'DOWNLOAD JSON' and save as 'ytmusic_auth.json' in the 'config' folder."
Pause

# -------------------------------------------------
# Verify that the ytmusic_auth.json file exists
# -------------------------------------------------
if (-not (Test-Path "$configDir\ytmusic_auth.json")) {
    Write-Host "Error: ytmusic_auth.json not found in config folder." -ForegroundColor Red
    Write-Host "Please ensure you have correctly followed the Google Cloud steps."
    Pause
    exit 1
}

# ------------------------------------------
# Start YouTube Music authentication
# ------------------------------------------
Write-Host "Starting YouTube Music authentication..."
& ytmusicapi oauth --file "$configDir\oauth.json"

Write-Host "YouTube Music setup completed." -ForegroundColor Green

# -------------------------------
# Start the musicMigrator.py script
# -------------------------------
& python musicMigrator.py

Pause
