@echo off
REM Run this from the folder containing install_sat_windows_envs.ps1.
REM Best launched from "Miniforge Prompt".

powershell -ExecutionPolicy Bypass -File "%~dp0install_sat_windows_envs.ps1" %*
pause
