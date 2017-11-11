@echo off
rem DotStar shim generator
rem Pass on a full path to generate a shim
rem Platforms: Win32, Win64
if not exist %LOCALAPPDATA%\DotStar\Shims mkdir %LOCALAPPDATA%\DotStar\Shims
set file=%~n1
(
    echo @echo off
    echo %* %%*
) > %LOCALAPPDATA%\DotStar\Shims\%file%.bat
