
@echo off
setlocal EnableExtensions

title CollaborativeDeliveryMAS Launcher

pushd "%~dp0"
set "PROJECT_DIR=%CD%"
set "PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"

echo.
echo ==========================================
echo    CollaborativeDeliveryMAS
echo ==========================================
echo.
echo Project: "%PROJECT_DIR%"
echo.

if not exist "%PYTHON%" (
    echo ERROR: Virtual environment Python not found:
    echo "%PYTHON%"
    pause
    popd
    exit /b 1
)

if not exist "%PROJECT_DIR%\server.py" (
    echo ERROR: server.py not found.
    pause
    popd
    exit /b 1
)

if not exist "%PROJECT_DIR%\main.py" (
    echo ERROR: main.py not found.
    pause
    popd
    exit /b 1
)

if not exist "%PROJECT_DIR%\dashboard\app.py" (
    echo ERROR: Dashboard file not found.
    pause
    popd
    exit /b 1
)

echo [1/3] Starting XMPP Server...
start "MAS - XMPP Server" /D "%PROJECT_DIR%" cmd /k "set PYTHONPATH=%PROJECT_DIR%&& "%PYTHON%" server.py"

timeout /t 5 /nobreak >nul

echo [2/3] Starting MAS Agents...
start "MAS - Agents" /D "%PROJECT_DIR%" cmd /k "set PYTHONPATH=%PROJECT_DIR%&& "%PYTHON%" main.py"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Streamlit UI...
start "MAS - Streamlit UI" /D "%PROJECT_DIR%" cmd /k "set PYTHONPATH=%PROJECT_DIR%&& "%PYTHON%" -m streamlit run dashboard\app.py --server.port 8502"

echo.
echo Startup commands launched.
echo Dashboard: http://localhost:8502
echo Check all three windows for errors.
echo.

popd
pause
