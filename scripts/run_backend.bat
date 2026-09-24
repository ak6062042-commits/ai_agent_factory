@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "PYTHON_BIN=%PROJECT_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON_BIN%" set "PYTHON_BIN=py -3"

cd /d "%PROJECT_ROOT%" || exit /b 1
call %PYTHON_BIN% -m uvicorn backend.app.main:app --reload --port 8001
exit /b %ERRORLEVEL%
