@echo off
rem This script will uninstall DotStar on the machine

taskkill /IM dotstar.exe /F
rmdir %LOCALAPPDATA%\DotStar\ /S /Q
