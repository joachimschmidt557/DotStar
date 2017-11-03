@echo off
rem This script will install DotStar on the machine

mkdir %LOCALAPPDATA%\DotStar
copy .\dist\dotstar.exe %LOCALAPPDATA%\DotStar\ /Y
