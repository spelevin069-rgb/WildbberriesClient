@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist run-client.bat (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%~dp0ClientPayload.zip' -DestinationPath '%~dp0' -Force"
)
py -m pip install -r requirements.txt
py -m src.main
pause
