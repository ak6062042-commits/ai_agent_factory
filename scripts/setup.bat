@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "VENV_PATH=%PROJECT_ROOT%\.venv"

cd /d "%PROJECT_ROOT%" || exit /b 1

if not exist "%VENV_PATH%\Scripts\python.exe" (
    py -3 -m venv "%VENV_PATH%"
    if errorlevel 1 exit /b 1
)

"%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%VENV_PATH%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo Setup complete. Activate the environment with: .venv\Scripts\activate
endlocal
