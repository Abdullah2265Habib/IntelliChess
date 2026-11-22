@echo off
REM Run from the project root so asset paths like gui/img/*.png resolve.
cd /d "%~dp0\.."
python gui/main.py
pause
