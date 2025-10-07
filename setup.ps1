# Set console encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Clear-Host

# ===================================
# Helper function for skip prompt
# ===================================
function Wait-ForStep($description) {
    Write-Host ""
    Write-Host ">>> $description"
    Write-Host "Press ESC to skip this step, or any other key to continue..."
    $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    if ($key.VirtualKeyCode -eq 27) {  # 27 = ESC
        Write-Host "Step skipped."
        return $false
    }
    else {
        return $true
    }
}

Write-Host "Welcome to the setup routine for Magician's Music (name may vary)." 
Write-Host "There are 7 step you can skip if not needed, some taks a while to start, so if you press any key to continue, don't click more than once."
# ===================================
# Step 1: Python installation
# ===================================
if (Wait-ForStep "Step 1: Check if Python is installed, install or update if needed.") {
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
        $pyVersion = python --version
        Write-Host "Python is already installed: $pyVersion" -ForegroundColor Green
    }
}

# ===================================
# Step 2: Upgrade pip
# ===================================
if (Wait-ForStep "Step 2: Check if pip is installed, install or update if needed.") {
    try {
        python -m pip install --upgrade pip
        Write-Host "pip upgraded successfully." -ForegroundColor Green
    }
    catch {
        Write-Host "pip not found. Bootstrapping with ensurepip..." -ForegroundColor Yellow
        python -m ensurepip --upgrade
        python -m pip install --upgrade pip
    }
}

# ===================================
# Step 3: Install or update yt-dlp
# ===================================
if (Wait-ForStep "Step 3: Install or update yt-dlp (YouTube downloader).") {
    python -m pip install -U yt-dlp
    Write-Host "yt-dlp installed/updated successfully." -ForegroundColor Green
}

# ========================================
# FFmpeg Setup
# ========================================
if (Wait-ForStep "Step 4: FFmpeg setup") { 
    try {
        ffmpeg -version | Out-Null
        Write-Host "FFmpeg is already installed." -ForegroundColor Green
    } catch {
        Write-Host "FFmpeg not found. Installing..." -ForegroundColor Yellow

        # Check if choco is available
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            choco install ffmpeg -y
        }
        # If winget is available, use it
        elseif (Get-Command winget -ErrorAction SilentlyContinue) {
            winget install ffmpeg -y
        }
        # Otherwise install Chocolatey, then ffmpeg
        else {
            Write-Host "Neither Chocolatey nor winget found. Installing Chocolatey first..." -ForegroundColor Yellow
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = `
                [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

            choco install ffmpeg -y
        }

        Write-Host "FFmpeg installation completed." -ForegroundColor Green
    }
}

# ===================================
# Step 5: Install browser-cookie3
# ===================================
if (Wait-ForStep "Step 5: Install or update browser-cookie3 (for automatic cookie extraction).") {
    python -m pip install -U browser-cookie3
    Write-Host "browser-cookie3 installed/updated successfully." -ForegroundColor Green
}

# ========================================
# Step 6: Spotify API Setup Instructions
# ========================================

if (Wait-ForStep "Step 6: Spotify API setup") {
    Write-Host ""
    Write-Host "1. Go to the following URL and ensure you are logged in:"
    Write-Host "   https://developer.spotify.com/dashboard/applications/"
    Write-Host ""
    Write-Host "2. Create a new application with any name and description."
    Write-Host ""
    Write-Host "3. In your app settings, add the following Redirect URI:"
    Write-Host "   http://127.0.0.1:8888/callback"
    Write-Host ""
    Write-Host "4. Under 'Which API/SDKs are you planning to use?' select 'Web API' and 'Web Playback SDK',"
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

    try {
        python -m pip install --upgrade spotipy
    } catch {
        Write-Host "Error installing Spotipy. Ensure Python and pip are correctly installed."
    }

    try {
        python -c "import spotipy; from spotipy.oauth2 import SpotifyOAuth; print('Spotify API setup successful.')"
    } catch {
        Write-Host "Spotify API test failed. Check your credentials and installation."
    }
}

Write-Host "Spotify API setup step completed (or skipped)."

# ===============================
# Step 7: YouTube Music API Setup
# ===============================

if (Wait-ForStep "Step 7: YouTube Music API setup") {
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
    Write-Host ""

    # Install ytmusicapi
    try {
        python -m pip install --upgrade ytmusicapi
    } catch {
        Write-Host "Error installing ytmusicapi. Ensure Python and pip are correctly installed."
    }

    # Verify that the ytmusic_auth.json file exists
    if (-not (Test-Path \"$configDir\\ytmusic_auth.json\")) {
        Write-Host "Error: ytmusic_auth.json not found in config folder." -ForegroundColor Red
        Write-Host "Please restart setup and ensure you correctly follow the Google Cloud steps."
        pause
        exit 1
    }

    # Start YouTube Music authentication
    Write-Host "Starting YouTube Music authentication..."
    & ytmusicapi oauth --file "$configDir\oauth.json"

    Write-Host "YouTube Music setup completed." -ForegroundColor Green
}

# ===================================
# Done with setup
# ===================================
Write-Host ""
Write-Host ">>> Setup completed. All dependencies are ready." -ForegroundColor Green

# -------------------------------
# Start the musicMigrator.py script
# -------------------------------
& python "Magician's_music.py"

Pause



