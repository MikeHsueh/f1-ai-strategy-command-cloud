@echo off
setlocal

echo Stopping services on ports 5000 and 5173...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5000 .*LISTENING"') do (
    taskkill /PID %%P /F >nul 2>&1
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173 .*LISTENING"') do (
    taskkill /PID %%P /F >nul 2>&1
)

echo F1 dashboard services stopped.
timeout /t 2 /nobreak >nul

endlocal
