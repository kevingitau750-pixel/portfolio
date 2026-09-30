#!/bin/bash
# Double-click to start the TTS A/B audio evaluation tool.
# First run: installs everything into .venv-audio (a few minutes). Later runs start in seconds.
cd "$(dirname "$0")" || exit 1

PY=""
for cand in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
        PY="$cand"; break
    fi
done
if [ -z "$PY" ]; then
    echo "Python 3.9 or newer is not installed. Opening the download page..."
    open "https://www.python.org/downloads/"
    read -r -p "Install Python, then double-click this file again. Press Enter to close."
    exit 1
fi

if [ ! -x ".venv-audio/bin/python" ]; then
    echo "Setting up for the first time - this takes a few minutes..."
    "$PY" -m venv .venv-audio || { read -r -p "Setup failed. Press Enter to close."; exit 1; }
fi
echo "Checking the required packages..."
.venv-audio/bin/python -m pip install --disable-pip-version-check -q -r audio_eval/requirements.txt \
    || { read -r -p "Package install failed (check your internet). Press Enter to close."; exit 1; }

echo
echo " The app is opening in your browser at http://localhost:8501"
echo " Keep this window open while you use it. Close it to stop the app."
echo
(sleep 6 && open "http://localhost:8501") &
exec .venv-audio/bin/python -m streamlit run audio_eval/app.py \
    --server.headless true --server.port 8501 --browser.gatherUsageStats false
