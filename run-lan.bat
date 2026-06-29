@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

REM LAN mode: bind to all interfaces so teammates on the same Wi-Fi/LAN can open it
REM for internal UX feedback. Not for public/GitHub use.
set "PORT=7000"

if not exist venv\Scripts\python.exe goto NOVENV
if exist "%ProgramFiles%\nodejs\npm.cmd" set "PATH=%PATH%;%ProgramFiles%\nodejs"

REM No forced login so teammates can open the UI directly for feedback.
if "%AUTH_ENABLED%"=="" set AUTH_ENABLED=false

REM Best-effort: detect this PC's LAN IPv4 (takes the last IPv4 line from ipconfig).
set "IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do set "IP=%%a"
set "IP=%IP: =%"
if "%IP%"=="" set "IP=<this-PC-IP>"

echo ============================================================
echo   VOD Studio - LAN mode (internal UX feedback)
echo.
echo   This PC:    http://127.0.0.1:%PORT%/vodstudio
echo   Teammates:  http://%IP%:%PORT%/vodstudio
echo.
echo   - Same Wi-Fi/LAN only.
echo   - Windows Firewall may prompt on first run -> Allow access.
echo   - Closing this window stops the server.
echo ============================================================
echo.

start "" /b cmd /c "timeout /t 4 >nul & start http://127.0.0.1:%PORT%/vodstudio"

venv\Scripts\python -m uvicorn app:app --host 0.0.0.0 --port %PORT%

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
