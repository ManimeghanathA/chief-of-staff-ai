@echo off
echo Starting Chief of Staff AI Backend...
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file with required environment variables.
    echo See TESTING_GUIDE.md for details.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install/update dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Start the server
echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
