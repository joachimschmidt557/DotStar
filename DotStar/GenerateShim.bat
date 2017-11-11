@echo off
rem DotStar shim generator
rem Pass on a full path to generate a shim
rem Platforms: Win32, Win64
set file=%~n1
(
    echo @echo off
    echo %* %%*
) > %~dp0\%file%.bat