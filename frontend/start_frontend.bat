@echo off
echo Starting Chief of Staff AI Frontend...
echo.
echo Frontend will be available at: http://localhost:3000
echo Make sure the backend is running on http://localhost:8000
echo.
echo Press Ctrl+C to stop
echo.

python -m http.server 3000

pause
