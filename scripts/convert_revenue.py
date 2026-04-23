#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPBC 주차장 매출 엑셀 → revenue_data.json 변환
사용법: python scripts/convert_revenue.py [파일1.xlsx 파일2.xlsx ...]
        파일 미지정 시 루트에서 '*주차장 매출*.xlsx' 자동 탐색
"""
import json, re, sys
import pandas as pd
from pathlib import Path
from datetime import datetime

def parse_month(sheet_name):
    m = re.match(r'(\d{2})년\s*(\d{2})월', sheet_name)
    if not m: return None
    return f'20{m.group(1)}-{m.group(2)}'

def to_int(val):
    try:
        v = float(val)
        return int(v) if v == v else 0  # NaN check
    except (TypeError, ValueError):
        return 0

def extract_month(df):
    categories = {}
    current_cat = None
    subtotal = 0      # 합계 (row에 col[0]='합계')
    mooju = 0
    grand_total = 0

    for _, row in df.iterrows():
        c0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        c1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        c2 = to_int(row.iloc[2]) if len(row) > 2 else 0

        # 새 카테고리 시작
        if c0 and c0 not in ('nan', 'NaN'):
            if c0 == '합계':
                subtotal = c2
            else:
                current_cat = c0
                if current_cat not in categories:
                    categories[current_cat] = 0

        # 소계 행
        if c1 == '소계' and current_cat and current_cat != '합계':
            categories[current_cat] = c2

        # 하단 결제수단 요약 행
        if c1 == '모주':
            mooju = c2
        if c1 == '합계' and (mooju > 0 or subtotal > 0):
            grand_total = c2

    if grand_total == 0:
        grand_total = subtotal + mooju

    return {
        'categories': categories,
        'subtotal': subtotal,
        'mooju': mooju,
        'total': grand_total,
    }

def convert(xlsx_files, out_path='data/revenue_data.json'):
    monthly = []

    for path in sorted(xlsx_files):
        print(f'[파일] {path.name}')
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names:
            month = parse_month(sheet)
            if not month:
                continue
            df = pd.read_excel(path, sheet_name=sheet, header=None)
            data = extract_month(df)
            data['month'] = month
            monthly.append(data)
            print(f'  {month}: 합계 {data["total"]:,}원'
                  + (f' (현장 {data["subtotal"]:,} + 모주 {data["mooju"]:,})' if data["mooju"] else ''))

    monthly.sort(key=lambda x: x['month'])
    # 중복 월 제거 (같은 월이 여러 파일에 있으면 마지막 것 사용)
    seen = {}
    for r in monthly:
        seen[r['month']] = r
    # 합계 0인 미래 빈 월 제거
    monthly = sorted([r for r in seen.values() if r['total'] > 0], key=lambda x: x['month'])

    output = {
        'meta': {
            'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'period': {
                'start': monthly[0]['month'],
                'end':   monthly[-1]['month'],
            },
            'total_revenue': sum(r['total'] for r in monthly),
        },
        'monthly': monthly,
    }

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n→ {out} 저장 완료 ({out.stat().st_size:,} bytes)')
    print(f'   기간: {output["meta"]["period"]["start"]} ~ {output["meta"]["period"]["end"]}')
    print(f'   총 매출 합계: {output["meta"]["total_revenue"]:,}원')

if __name__ == '__main__':
    REPO = Path(__file__).parent.parent
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]
    else:
        files = sorted((REPO / 'data' / 'revenue').glob('*.xlsx'))

    if not files:
        print('오류: 매출 xlsx 파일을 찾을 수 없습니다.')
        print('사용법: python scripts/convert_revenue.py 2024년\ 주차장\ 매출.xlsx ...')
        sys.exit(1)

    convert(files, REPO / 'data' / 'revenue_data.json')
