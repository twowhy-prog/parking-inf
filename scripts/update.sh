#!/usr/bin/env bash
# 사용법:
#   bash scripts/update.sh data/raw/새파일.xlsx
#   bash scripts/update.sh  ← data/raw/ 에서 가장 최근 xlsx 자동 선택

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW_DIR="$REPO_ROOT/data/raw"
JSON_PATH="$REPO_ROOT/data/parking_data.json"
HTML_PATH="$REPO_ROOT/dashboard.html"

# ── 엑셀 파일 결정 ──────────────────────────────────────────────
if [ -n "$1" ]; then
    XLSX="$(realpath "$1")"
    # data/raw/ 외부에서 넣은 경우 복사
    if [[ "$XLSX" != "$RAW_DIR"/* ]]; then
        cp "$XLSX" "$RAW_DIR/$(basename "$XLSX")"
        XLSX="$RAW_DIR/$(basename "$XLSX")"
        echo "→ data/raw/에 복사: $(basename "$XLSX")"
    fi
else
    XLSX=$(ls -t "$RAW_DIR"/*.xlsx 2>/dev/null | head -1)
    if [ -z "$XLSX" ]; then
        echo "오류: data/raw/ 에 xlsx 파일이 없습니다."
        echo "사용법: bash scripts/update.sh 파일.xlsx"
        exit 1
    fi
    echo "→ 자동 선택: $(basename "$XLSX")"
fi

# ── 변환 실행 ────────────────────────────────────────────────────
cd "$REPO_ROOT"
echo ""
python scripts/convert.py "$XLSX" "$JSON_PATH"

# ── 커밋 메시지 자동 생성 (JSON에서 마지막 월 읽기) ────────────────
LAST_MONTH=$(python3 -c "
import json
with open('$JSON_PATH') as f:
    d = json.load(f)
print(d['meta']['period']['end'])
" 2>/dev/null || echo "unknown")

echo ""
echo "── git 상태 ────────────────────────────────────────────────"
git status --short

echo ""
read -rp "커밋 메시지 [기본: data: $LAST_MONTH]: " MSG
MSG="${MSG:-data: $LAST_MONTH}"

git add dashboard.html data/parking_data.json "data/raw/$(basename "$XLSX")"
git commit -m "$MSG"
git push -u origin "$(git rev-parse --abbrev-ref HEAD)"

echo ""
echo "완료! 대시보드: https://twowhy-prog.github.io/parking-inf/dashboard.html"
