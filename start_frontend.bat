@echo off
echo ==========================================
echo      Starting EasyChat Frontend Server
echo ==========================================
echo.

REM Navigate to the frontend directory
cd frontend

REM Check if node_modules exist
if not exist node_modules (
    echo [ERROR] 'node_modules' directory not found.
    echo Please run 'npm install' in the frontend directory first.
    pause
    exit /b 1
)

REM Start the Vue development server
echo Starting Vue development server...
npm run serve

echo.
echo Frontend server has been stopped.
pause 