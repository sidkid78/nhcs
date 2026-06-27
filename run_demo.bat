@echo off
REM Run NHCS demo using the project venv (guarantees GUDHI is available).
REM Usage: run_demo.bat
SET SCRIPT_DIR=%~dp0
"%SCRIPT_DIR%.venv\Scripts\python.exe" -m nhcs.orchestrator.digital_twin_demo %*
