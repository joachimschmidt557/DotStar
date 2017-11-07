@echo off
rem This script will install DotStar on the machine

echo Installing DotStar...

echo Exiting all DotStar processes...
taskkill /IM dotstar.exe /F

echo Copying files...
rmdir %LOCALAPPDATA%\DotStar\ /S /Q
mkdir %LOCALAPPDATA%\DotStar
copy .\dist\dotstar.exe %LOCALAPPDATA%\DotStar\ /Y
