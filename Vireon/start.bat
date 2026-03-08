@echo off

title Vireon

REM 
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM 
python -m pip install --upgrade pip

REM
python -m pip install -r requirements.txt

echo.
echo Installation complete!

cls
py bin/interface.py
echo Please keep this open.

exit