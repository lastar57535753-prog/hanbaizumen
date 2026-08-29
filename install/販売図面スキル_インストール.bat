@echo off
rem This launcher is ASCII-only on purpose. Japanese text in a .bat gets
rem mangled by cmd's codepage handling, so all messages live in _setup.ps1.
setlocal
title Mysoku skill installer

set "PS1=%~dp0_setup.ps1"
if not exist "%PS1%" (
  echo _setup.ps1 was not found next to this file.
  echo Put install .bat / _setup.ps1 / the .zip in the same folder.
  echo Folder: %~dp0
  goto :end
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"

:end
echo.
pause
