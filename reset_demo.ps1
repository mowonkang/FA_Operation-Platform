# FA Operation Platform — 데모 데이터 초기화 (Windows PowerShell)
# 사용법: 프로젝트 루트에서  .\reset_demo.ps1
# 백엔드 서버를 먼저 중지(Ctrl+C)한 뒤 실행하세요.

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\backend"

if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
}

if (Test-Path "fa_platform.db") {
    Remove-Item "fa_platform.db"
    Write-Host "기존 DB 삭제 완료"
}

python -m app.seed

Write-Host ""
Write-Host "완료! 이제 백엔드를 시작하세요:" -ForegroundColor Green
Write-Host "  uvicorn app.main:app --reload --port 8000"
