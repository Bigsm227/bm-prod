@echo off
cd /d "%~dp0"
echo Installation de PyInstaller...
"%LOCALAPPDATA%\Microsoft\WindowsApps\python3.13.exe" -m pip install pyinstaller

echo.
echo Generation de l'executable...
"%LOCALAPPDATA%\Microsoft\WindowsApps\python3.13.exe" -m PyInstaller --noconsole --onefile app.py

echo.
echo Termine !
pause