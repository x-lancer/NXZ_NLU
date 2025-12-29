@echo off
echo ==========================================
echo       NXZ NLU Service - Environment Setup
echo ==========================================

echo [1/2] Upgrading pip...
python -m pip install --upgrade pip

echo [2/2] Installing requirements...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ==========================================
echo       Installation Complete!
echo ==========================================
pause

