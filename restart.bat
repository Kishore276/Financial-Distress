@echo off
echo ====================================
echo Smart Finance Guardian - Restart
echo ====================================
echo.
echo Stopping any running Flask instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *app.py*" 2>NUL
taskkill /F /IM python3.12.exe /FI "WINDOWTITLE eq *app.py*" 2>NUL
timeout /t 2 /nobreak >NUL
echo.
echo Starting Flask app...
echo.
python app.py
