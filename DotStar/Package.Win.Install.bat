@echo off
rem This script will install DotStar on the machine

echo Installing DotStar...

echo Exiting all DotStar processes...
taskkill /IM dotstar.exe /F

echo Copying files...
rmdir %LOCALAPPDATA%\DotStar\ /S /Q
mkdir %LOCALAPPDATA%\DotStar
copy .\dist\dotstar.exe %LOCALAPPDATA%\DotStar\ /Y
copy .\GenerateShim.bat %LOCALAPPDATA%\DotStar\ /Y

rem Generate shims
.\GenerateShim.bat %LOCALAPPDATA%\DotStar\dotstar.exe
.\GenerateShim.bat %LOCALAPPDATA%\DotStar\GenerateShim.bat

rem TODO: Add Shim folder to PATH

rem Create other environment variables
setx DOTSTARPATH %LOCALAPPDATA%\DotStar\
setx DOTSTARSHIMS %LOCALAPPDATA%\DotStar\Shims\
