$ErrorActionPreference='SilentlyContinue'
$Root='/mnt/data/YILBAY_RELEASE_v0.5.0'
$Bat='/mnt/data/YILBAY_RELEASE_v0.5.0/PROGRAMI_CALISTIR.bat'
$Content=@'
@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title YILBAY OGRENCI TAKIP SISTEMI

echo ================================================================
echo       YILBAY OGRENCI TAKIP SISTEMI - KALICI BASLATICI
echo ================================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap\orchestrator.ps1"
set EXITCODE=%ERRORLEVEL%
exit /b %EXITCODE%

'@

# Current orchestrator/report cycle must finish first.
for($i=0;$i -lt 900;$i++){
  $running=Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'powershell.exe' -and
    $_.CommandLine -like '*bootstrap\orchestrator.ps1*' -and
    $_.CommandLine -like ('*'+$Root+'*')
  }
  if(-not $running){break}
  Start-Sleep -Milliseconds 500
}

# Replace launcher only after the current PowerShell cycle has ended.
[System.IO.File]::WriteAllText($Bat,$Content,(New-Object System.Text.UTF8Encoding($false)))

# Close the old cmd window that is waiting at PAUSE.
Start-Sleep -Milliseconds 300
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq 'cmd.exe' -and
  $_.CommandLine -like '*PROGRAMI_CALISTIR.bat*' -and
  $_.CommandLine -like ('*'+$Root+'*')
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
