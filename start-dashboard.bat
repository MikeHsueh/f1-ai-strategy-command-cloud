@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "PYTHON_EXE=C:\Users\leow3\anaconda3\python.exe"
set "FRONTEND_URL=http://127.0.0.1:5173"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python was not found:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%\run_server.py" (
    echo [ERROR] Backend entry point was not found:
    echo %BACKEND_DIR%\run_server.py
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%node_modules" (
    echo [SETUP] Installing frontend dependencies...
    pushd "%PROJECT_DIR%"
    call npm.cmd install
    if errorlevel 1 (
        popd
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
    popd
)

echo [1/3] Starting F1 backend on http://127.0.0.1:5000 ...
start "F1 Strategy Backend" cmd /k "set KMP_DUPLICATE_LIB_OK=TRUE&& cd /d ""%BACKEND_DIR%""&& ""%PYTHON_EXE%"" run_server.py"

echo [2/3] Starting Vue frontend on %FRONTEND_URL% ...
start "F1 Strategy Frontend" cmd /k "cd /d ""%PROJECT_DIR%""&& npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo [3/3] Waiting for startup...
timeout /t 8 /nobreak >nul
start "" "%FRONTEND_URL%"

echo.
echo Dashboard opened at %FRONTEND_URL%
echo Keep both command windows open while using the dashboard.
echo Run stop-dashboard.bat to stop both services.
timeout /t 3 /nobreak >nul

endlocal
