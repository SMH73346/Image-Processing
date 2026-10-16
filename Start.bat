@echo off
rem Opens Product Image Studio in your browser. Close this window to stop the app.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo The app isn't set up yet. Run Setup.bat first.
    pause
    exit /b 1
)
title Product Image Studio
echo Starting Product Image Studio... your browser will open in a moment.
echo Keep this window open while you use the app. Close it to stop the app.
echo.
.venv\Scripts\python.exe app.py
if errorlevel 1 pause
