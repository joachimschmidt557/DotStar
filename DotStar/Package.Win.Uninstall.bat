@echo off
rem This script will uninstall DotStar on the machine

echo Uninstalling DotStar...

echo Exiting all DotStar processes...
taskkill /IM dotstar.exe /F

echo Removing files...
rmdir %LOCALAPPDATA%\DotStar\ /S /Q

rem TODO: Remove DotStar from PATH
