@echo off
rem One-time setup on a new PC: creates the Python environment and downloads the AI model (~1 GB).
rem Needs Python 3.12 installed (https://www.python.org or: winget install Python.Python.3.12).
setlocal
cd /d "%~dp0"

rem Find a working Python 3.12 (the Microsoft Store "python" shortcut doesn't count).
set "PY="
py -3.12 -c "import sys" >nul 2>nul && set "PY=py -3.12"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe""
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY="%ProgramFiles%\Python312\python.exe""
if not defined PY python -c "import sys; assert sys.version_info[:2] == (3, 12)" >nul 2>nul && set "PY=python"
if not defined PY (
    echo Python 3.12 was not found. Install it first, for example:
    echo     winget install Python.Python.3.12
    goto :error
)
echo Using Python: %PY%

echo Creating Python environment...
%PY% -m venv .venv || goto :error
.venv\Scripts\python.exe -m pip install --upgrade pip || goto :error
echo Installing libraries...
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto :error
echo Downloading the AI model (about 1 GB, one time only)...
.venv\Scripts\python.exe -c "from core.cutout import load_model; load_model()" || goto :error

echo.
echo Setup complete.
pause
exit /b 0

:error
echo.
echo Setup failed - see the messages above.
pause
exit /b 1
