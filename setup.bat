@echo off
chcp 65001 > nul  :: Imposta la codifica UTF-8 per evitare caratteri errati
cls

:: Verifica se Python e' installato
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python non è installato. Scarico l'installer...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe
    echo Installazione di Python in corso...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    echo Python installato con successo!
) else (
    echo Python e' già installato.
)

:: Aggiorna pip e installa le librerie
echo Installa/aggiorna pip e le librerie...
python -m pip install --upgrade pip --no-warn-script-location > nul 2>&1
pip install spotipy ytmusicapi --no-warn-script-location > nul 2>&1

@echo off
echo ======================================================
echo       Spotify API Setup Instructions
echo ======================================================
echo.
echo 1. Go to the following URL and ensure you are logged in:
echo    https://developer.spotify.com/dashboard/applications/
echo.
echo 2. Create a new application with any name and description.
echo.
echo 3. In your app settings, add the following Redirect URI:
echo    http://localhost:8888/callback
echo.
echo 4. Select "Web API" and "Web Playback SDK" under "Which API/SDKs are you planning to use?", accept the Terms of Service and save.
echo.
echo 5. Go to settings (top right), copy yout Client ID, click "View Client Secret" and copy that as well.
echo.
pause

:: Prompt user for input
set /p client_id="Enter your Spotify Client ID: "
set /p client_secret="Enter your Spotify Client Secret: "

:: Create the config directory if it doesn't exist
if not exist config (
    mkdir config
)

:: Create the spotify_auth.json file in the config directory
(
echo {
echo     "client_id": "%client_id%",
echo     "client_secret": "%client_secret%"
echo }
) > config\spotify_auth.json

echo.
echo spotify_auth.json has been created in the config directory.


:: YTMusic Setup
cls
echo ======================================================
echo       YouTube Music API Setup Instructions
echo ======================================================
echo.
echo 1. Go to: https://console.cloud.google.com/ and ensure you're logged in with your Google account
echo.
echo 2. Click the project selector dropdown (top-left)
echo    - Create a New Project with any name
echo.
echo 3. Enable YouTube Data API v3:
echo    - Left menu > APIs & Services > Library
echo    - Search "YouTube Data API v3" > ENABLE
echo.
echo 4. Configure OAuth Consent Screen:
echo    - Left menu > APIs & Services > OAuth consent screen
echo    - If the Auth Platform isn't configured yet, press Start and select as follows:
echo        - App name: Any name | User support email: Your email
echo        - User Type: External > Create
echo        - Developer contact email: Your email > Save and Continue
echo    - Left menu > Public > scroll until you see 'Test Users' and add your email then save
echo    
echo 5. Create OAuth Credentials:
echo    - Left menu > Credentials > Create Credentials > OAuth client ID
echo    - Application type: TVs and Limited Input
echo    - Name: Any name > Create
echo    - Click "DOWNLOAD JSON" and save as "ytmusic_auth.json in the 'config' folder"
pause

:: Verify YTMusic credentials
if not exist "config\ytmusic_auth.json" (
    echo Error: ytmusic_auth.json not found in config folder!
    echo Please repeat the Google Cloud steps correctly.
    pause
    exit /b 1
)

echo Starting YouTube Music authentication...
ytmusicapi oauth --file config\oauth.json

echo YouTube Music setup completed!
python musicMigrator.py
pause