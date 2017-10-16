@echo off
rem This script will install DotStar on the machine

mkdir %LOCALAPPDATA%\DotStar
copy .\dist\DotStar.exe %LOCALAPPDATA%\DotStar\ /Y
