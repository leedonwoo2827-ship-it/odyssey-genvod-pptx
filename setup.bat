@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "LOG=%~dp0setup_log.txt"
echo setup start > "%LOG%"

echo ============================================================
echo   VOD Studio - setup
echo ============================================================
echo.

REM 1) Python (prefer py -3, else python)
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto NOPY
echo [OK] Python: %PY%

REM 2) virtual env
if not exist "venv\Scripts\python.exe" (
  echo [1/6] creating venv...
  %PY% -m venv venv
) else (
  echo [1/6] venv exists - skipping
)
set "VPY=%~dp0venv\Scripts\python.exe"
if not exist "%VPY%" goto VENVFAIL

REM 3) libraries (local TTS, embeddings, etc.)
echo [2/6] installing libraries... (first run takes a few minutes)
"%VPY%" -m pip install --upgrade pip
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto PIPFAIL
echo step:pip-ok >> "%LOG%"

REM notebooklm-mcp-cli pulls urllib3-future which shadows the real urllib3 and
REM breaks fastembed/requests. Restore standard urllib3.
echo [3/6] restoring urllib3 (protects fastembed/requests)...
"%VPY%" -m pip install --force-reinstall --no-deps "urllib3==2.7.0"
echo step:urllib3-ok >> "%LOG%"

REM (This product is Codex-only - Gemini/agy install step removed.)

REM 4) OpenAI Codex CLI (codex) - ChatGPT login (needs Node)
echo [4/6] checking codex (OpenAI/ChatGPT)...
where codex >nul 2>nul || call :INSTALL_CODEX
where codex >nul 2>nul && (echo       [OK] codex installed) || (echo       [note] codex missing - if Node was just installed, run setup.bat once more)
echo step:codex-done >> "%LOG%"

REM 5) local TTS model download (HuggingFace, ~380MB) - only if missing
echo [5/7] checking TTS model (assets\onnx)...
if exist "assets\onnx\vocoder.onnx" (
  echo       [OK] TTS model present
) else (
  echo       model missing - downloading from HuggingFace ^(~380MB, takes a while^)...
  powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\setup_assets.ps1"
)
echo step:models-done >> "%LOG%"

REM 6) mp4maker probe, prepare .env  (mp4maker is vendored in this repo - no clone)
echo [6/7] mp4maker probe...
if not exist .env copy .env.example .env >nul
pushd mp4maker
"%VPY%" -m mp4maker --probe
popd
echo step:mp4maker-done >> "%LOG%"

REM 7) install PPTX fonts (Black Han Sans / Do Hyeon) for current user - no admin
echo [7/7] installing PPTX fonts (assets\fonts)...
"%VPY%" scripts\install_fonts.py
echo step:fonts-done >> "%LOG%"

echo.
echo ============================================================
echo   Setup complete!  Next: double-click run.bat
echo   In the app, click [Login (terminal)] and sign in:
echo     - ChatGPT : codex login    (no API key, uses your account quota)
echo ============================================================
echo setup end >> "%LOG%"
echo.
pause
exit /b 0

:INSTALL_CODEX
where npm >nul 2>nul || call :INSTALL_NODE
where npm >nul 2>nul && (echo       installing codex (npm i -g @openai/codex)... & cmd /c npm i -g @openai/codex)
goto :eof

:INSTALL_NODE
echo       Node.js missing - trying winget install (a UAC prompt may appear)...
where winget >nul 2>nul && winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
if exist "%ProgramFiles%\nodejs\npm.cmd" set "PATH=%PATH%;%ProgramFiles%\nodejs"
goto :eof

:NOPY
echo [ERROR] Python 3.11+ required. https://www.python.org/downloads/
echo         Check "Add Python to PATH" during install, then re-run.
echo python-missing >> "%LOG%"
pause
exit /b 1

:VENVFAIL
echo [ERROR] venv creation failed. Reinstall Python and try again.
pause
exit /b 1

:PIPFAIL
echo [ERROR] pip install failed. Check the red messages above.
pause
exit /b 1
