@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [Humanize Lab] First-time setup: creating virtual environment and downloading local AI detector models...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup.ps1"
  if errorlevel 1 (
    echo [Humanize Lab] Setup failed. Please check Python and internet connection.
    pause
    exit /b 1
  )
)
if not exist "models\holdout\model.safetensors" (
  echo [Humanize Lab] Downloading local AI detector models...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup.ps1"
  if errorlevel 1 (
    echo [Humanize Lab] Model download failed.
    pause
    exit /b 1
  )
)
".venv\Scripts\python.exe" -X utf8 "%~dp0app.py" --open
pause
