@echo off
REM Clip Workflow Tool Starter

REM DaVinci Resolve Pfade setzen
set RESOLVE_SCRIPT_API=C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules
set RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
set PATH=C:\Program Files\Blackmagic Design\DaVinci Resolve;%PATH%

echo ========================================
echo   Clip Workflow Tool
echo ========================================
echo.
echo Stelle sicher dass DaVinci Resolve laeuft!
echo.

REM Aktiviere venv und starte
call venv\Scripts\activate
python main.py

pause
