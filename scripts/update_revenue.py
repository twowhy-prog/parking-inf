#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/revenue/*.xlsx → parking_data.json revenue 필드 업데이트 스크립트
각 연도 파일의 월별 시트에서 '합계' 행을 찾아 실제 수익으로 갱신합니다.
사용법: python scripts/update_revenue.py
"""

import sys, json, re, glob
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

def sheet_to_month(sheet_name):
    """'24년 01월' → '2024-01'"""
    m = re.match(r'(\d{2})년?\s*(\d{2})월', sheet_name)
    if m:
        return f'20{m.group(1)}-{m.group(2)}'
    return None

def extract_revenue_map(revenue_dir):
    files = sorted(glob.glob(str(revenue_dir / '*.xlsx')))
    if not files:
        print(f"  ※ 수익 엑셀 파일 없음: {revenue_dir}")
        return {}

    revenue_map = {}
    for f in files:
        xl = pd.ExcelFile(f)
        fname = Path(f).name
        for sheet in xl.sheet_names:
            month = sheet_to_month(sheet)
            if not month:
                continue
            df = pd.read_excel(f, sheet_name=sheet, header=None)
            for _, row in df.iterrows():
                v0 = str(row[0]) if pd.notna(row[0]) else ''
                if '합계' in v0:
                    amt = row[2] if pd.notna(row[2]) else 0
                    if isinstance(amt, (int, float)) and amt > 0:
                        revenue_map[month] = int(amt)
                    break
        print(f"  {fname}: {sum(1 for s in xl.sheet_names if sheet_to_month(s))}개 월 처리")
    return revenue_map

def update_html(json_data, html_path):
    if not html_path.exists():
        print(f"  ※ dashboard.html 없음 → 건너뜀")
        return
    text = html_path.read_text(encoding='utf-8')
    json_str = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('const INLINE_DATA'):
            lines[i] = f'const INLINE_DATA = {json_str};'
            break
    html_path.write_text('\n'.join(lines), encoding='utf-8')
    print("  → dashboard.html INLINE_DATA 갱신 완료")

def main():
    json_path    = REPO_ROOT / 'data' / 'parking_data.json'
    revenue_dir  = REPO_ROOT / 'data' / 'revenue'
    html_path    = REPO_ROOT / 'dashboard.html'

    print("[1/4] 수익 엑셀 파일 파싱 중...")
    revenue_map = extract_revenue_map(revenue_dir)
    if not revenue_map:
        print("수익 파일을 찾을 수 없어 종료합니다.")
        sys.exit(1)

    print(f"[2/4] parking_data.json 로드: {json_path}")
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    print("[3/4] revenue 필드 업데이트 중...")
    updated = 0
    for record in data['monthly']:
        month = record['month']
        if month in revenue_map:
            old, new = record['revenue'], revenue_map[month]
            record['revenue'] = new
            print(f"  {month}: {old:>10,} → {new:>10,}  (Δ{new-old:+,})")
            updated += 1
        else:
            print(f"  {month}: 수익 파일 없음 → 유지 ({record['revenue']:,})")

    print(f"  총 {updated}개 월 업데이트")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  → {json_path} 저장 완료")

    print("[4/4] dashboard.html INLINE_DATA 갱신 중...")
    update_html(data, html_path)

    print("\n완료! 변경사항 확인 후 git commit & push 하세요.")

if __name__ == '__main__':
    main()
