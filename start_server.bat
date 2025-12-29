@echo off
echo ==========================================
echo       Starting NXZ NLU Service
echo ==========================================

:: Set PYTHONPATH to current directory to ensure imports work
set PYTHONPATH=%~dp0

:: Run the server with HuggingFace mirror for China
python run.py --hf-mirror https://hf-mirror.com

pause

