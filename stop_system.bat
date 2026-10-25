
@echo off
setlocal EnableExtensions

title CollaborativeDeliveryMAS - Stop System

cd /d "%~dp0"
set "PROJECT_DIR=%CD%"

echo.
echo ==========================================
echo   CollaborativeDeliveryMAS - Stop System
echo ==========================================
echo.

echo [1/4] Stopping Streamlit...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$root = [regex]::Escape('%PROJECT_DIR%');" ^
 "$p = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('streamlit') -and $_.CommandLine.Contains('%PROJECT_DIR%') };" ^
 "foreach ($x in $p) { Stop-Process -Id $x.ProcessId -Force -ErrorAction SilentlyContinue }"

echo [2/4] Stopping Coordinator Agent...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$p = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('%PROJECT_DIR%') -and $_.CommandLine -match 'coordinator_agent\.py' };" ^
 "foreach ($x in $p) { Stop-Process -Id $x.ProcessId -Force -ErrorAction SilentlyContinue }"

echo [3/4] Stopping Courier Agent...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$p = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('%PROJECT_DIR%') -and $_.CommandLine -match 'courier_agent\.py' };" ^
 "foreach ($x in $p) { Stop-Process -Id $x.ProcessId -Force -ErrorAction SilentlyContinue }"

echo [4/4] Stopping XMPP Server...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$p = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('%PROJECT_DIR%') -and $_.CommandLine -match 'server\.py' };" ^
 "foreach ($x in $p) { Stop-Process -Id $x.ProcessId -Force -ErrorAction SilentlyContinue }"

timeout /t 2 /nobreak >nul

echo.
echo Backend stop commands completed.
echo.

REM Close only the terminal windows created by this launcher.
for %%T in ("MAS - XMPP Server" "MAS - Courier Agent" "MAS - Coordinator Agent" "MAS - Streamlit UI") do (
    taskkill /FI "WINDOWTITLE eq %%~T*" /T /F >nul 2>&1
)

echo System shutdown requested.
exit /b 0
