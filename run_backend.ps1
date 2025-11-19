#!/usr/bin/env pwsh
# Traffic Signal Dashboard Backend Startup Script (PowerShell)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Traffic Signal Dashboard Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

# Activate virtual environment if it exists
if (Test-Path ".venv/Scripts/Activate.ps1") {
    & .venv/Scripts/Activate.ps1
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "WARNING: Virtual environment not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting Flask API server..." -ForegroundColor Green
Write-Host "API will be available at http://localhost:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& python dashboard/backend/app.py
