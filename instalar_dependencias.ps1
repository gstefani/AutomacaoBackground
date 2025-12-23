Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalando Dependencias - Tibia Auto" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Atualizando pip..." -ForegroundColor Yellow
py -m pip install --upgrade pip

Write-Host ""
Write-Host "Instalando pywin32..." -ForegroundColor Yellow
py -m pip install pywin32

Write-Host ""
Write-Host "Instalando pynput..." -ForegroundColor Yellow
py -m pip install pynput

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Instalacao Concluida!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Agora execute: py .\tibia_auto_v2.py" -ForegroundColor Yellow
