@echo off
echo =========================================
echo      Starting EasyChat Backend Server
echo =========================================
echo.

REM Navigate to the backend directory
cd backend

REM Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run the setup steps in README.md first.
    pause
    exit /b 1
)

REM Activate the virtual environment and run the Flask app
echo Activating virtual environment...
call venv\Scripts\activate

echo Starting Flask server...
flask run

echo.
echo Backend server has been stopped.
pause 