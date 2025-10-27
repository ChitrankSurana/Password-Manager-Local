@echo off
echo Installing required dependencies...
pip install tabulate > nul 2>&1

echo.
echo Starting Database Viewer...
echo.
python view_database.py

pause
