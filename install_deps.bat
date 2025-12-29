@echo off
echo ==========================================
echo       NXZ NLU Service - Environment Setup
echo ==========================================

echo [1/3] Upgrading pip...
python -m pip install --upgrade pip

echo [2/3] Installing PyTorch (CPU Version)...
echo Note: Installing CPU version to save space and avoid CUDA errors.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo [3/3] Installing other requirements...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ==========================================
echo       Installation Complete!
echo ==========================================
pause
