@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "PYTHON_BIN=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "LOG_FILE=%PROJECT_ROOT%\tests\test_log.txt"

if not exist "%PYTHON_BIN%" set "PYTHON_BIN=py -3"

cd /d "%PROJECT_ROOT%" || exit /b 1
call %PYTHON_BIN% -m pytest tests -v -p no:cacheprovider > "%LOG_FILE%" 2>&1
set "TEST_STATUS=%ERRORLEVEL%"
type "%LOG_FILE%"
exit /b %TEST_STATUS%
