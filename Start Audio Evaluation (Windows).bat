@echo off
rem Double-click to start the TTS A/B audio evaluation tool.
rem First run: installs everything into .venv-audio (a few minutes). Later runs start in seconds.
setlocal
cd /d "%~dp0"
title Audio evaluation

rem --- find Python 3.9+ -------------------------------------------------------
set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>nul && set "PY=python"
if not defined PY goto nopython

rem --- one-time setup (re-runs quickly if already installed) ------------------
if not exist ".venv-audio\Scripts\python.exe" (
    echo Setting up for the first time - this takes a few minutes...
    %PY% -m venv .venv-audio || goto fail
)
echo Checking the required packages...
".venv-audio\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r audio_eval\requirements.txt || goto fail

rem --- start the app and open the browser ------------------------------------
echo.
echo  The app is opening in your browser at http://localhost:8501
echo  Keep this window open while you use it. Close it to stop the app.
echo.
start "" cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:8501"
".venv-audio\Scripts\python.exe" -m streamlit run audio_eval\app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
goto end

:nopython
echo Python 3.9 or newer is not installed.
where winget >nul 2>nul
if %errorlevel%==0 (
    echo Installing Python now...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    echo.
    echo Python is installed. Close this window and double-click this file again.
) else (
    echo Opening the Python download page. Install it ^(tick "Add python.exe to PATH"^),
    echo then double-click this file again.
    start "" https://www.python.org/downloads/
)
pause
goto end

:fail
echo.
echo Something went wrong during setup - see the messages above.
echo Check your internet connection and try again.
pause

:end
endlocal
