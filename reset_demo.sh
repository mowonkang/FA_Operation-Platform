#!/bin/bash
# FA Operation Platform — 데모 데이터 초기화 (macOS/Linux)
# 사용법: 프로젝트 루트에서  ./reset_demo.sh
set -e
cd "$(dirname "$0")/backend"
[ -f .venv/bin/activate ] && source .venv/bin/activate
rm -f fa_platform.db && echo "기존 DB 삭제 완료"
python -m app.seed
echo ""
echo "완료! 이제 백엔드를 시작하세요:  uvicorn app.main:app --reload --port 8000"
