@echo off
title FINSIGHT - Smart Finance System
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    if exist "C:\Users\keshav bhardwaj\AppData\Local\Programs\Python\Python312\python.exe" (
        "C:\Users\keshav bhardwaj\AppData\Local\Programs\Python\Python312\python.exe" main.py
    )
)
if errorlevel 1 pause
