@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM Port for this instance. Change here if it conflicts with another app.
set "PORT=7000"

if not exist venv\Scripts\python.exe goto NOVENV

REM Make codex visible if Node was installed to a common location (PATH may be stale).
if exist "%ProgramFiles%\nodejs\npm.cmd" set "PATH=%PATH%;%ProgramFiles%\nodejs"

REM Local single-user: do not force login at start (Google login optional in the gear menu).
if "%AUTH_ENABLED%"=="" set AUTH_ENABLED=false

echo ============================================================
echo   VOD Studio - starting
echo   URL: http://127.0.0.1:%PORT%/vodstudio
echo   (closing this window stops the server)
echo ============================================================
echo.

start "" /b cmd /c "timeout /t 4 >nul & start http://127.0.0.1:%PORT%/vodstudio"

venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port %PORT%

echo.
echo Server stopped.
pause
exit /b 0

:NOVENV
echo.
echo [ERROR] venv not found. Run setup.bat first.
echo.
pause
exit /b 1
