@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul || (echo Python 3.10+ is required.& pause& exit /b 1)
py -3 -m pip install --upgrade pip
if errorlevel 1 goto failed
py -3 -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name WildbberriesClient --icon assets\wildbberries.ico --collect-all qfluentwidgets --collect-all PyQt6 src\main.py
if errorlevel 1 goto failed
echo.
echo Launcher EXE: dist\WildbberriesClient.exe
pause
exit /b 0
:failed
echo Build failed.
pause
exit /b 1
