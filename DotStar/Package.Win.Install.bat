@echo off
rem This script will install DotStar on the machine

mkdir %LOCALAPPDATA%\DotStar
taskkill /IM dotstar.exe /F
copy .\dist\dotstar.exe %LOCALAPPDATA%\DotStar\ /Y
