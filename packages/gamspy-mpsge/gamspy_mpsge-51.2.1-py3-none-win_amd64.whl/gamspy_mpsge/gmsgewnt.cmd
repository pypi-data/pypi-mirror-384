@echo off
gmsgewnx.exe "%~4"
if not %ERRORLEVEL% == 0 echo ERR: Solver rc %ERRORLEVEL% 1>&2
