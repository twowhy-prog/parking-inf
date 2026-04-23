#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPBC 주차장 입출차 데이터 → JSON 변환 스크립트
사용법: python scripts/convert.py <새엑셀파일> [기존JSON경로]
  - 기존 JSON이 있으면 중복 월을 자동으로 걸러내고 신규 월만 병합합니다.
출력:  data/parking_data.json
"""

import sys, json, re
import pandas as pd
from pathlib import Path
from datetime import datetime

INTERNAL_TYPES = ['정기','입주','법인','직원','직무','사제','거래처','출연','평화']
DISC_COLS  = ['모주_당일권','모주_3시간권','모주_야간권','모주_심야권',
              '전액할인','5시간할인','3시간할인','시간단위할인','정기/내부','일반유료','기타']
VTYPE_COLS = ['일반','일반 정기주차','직원 월 정기주차','입주업체','직무주차',
              '법인차량','사제주차','고정출연자','거래처 정기주차','평화빌딩 직원',
              '직원 휴일주차','마케팅 직무주차']
DUR_BINS = [0,60,120,180,240,360,480,600,720,1440,99999]
DUR_LABS = ['1h이하','1-2h','2-3h','3-4h','4-6h','6-8h','8-10h','10-12h','12-24h','24h초과']
PASS_MAP = [('모주 당일권','당일권'),('모주 3시간권','3시간권'),
            ('모주 야간권','야간권'),('모주 심야권','심야권')]

def classify(row):
    h  = str(row['할인명']) if pd.notna(row['할인명']) else ''
    vt = str(row['차량종류']) if pd.notna(row['차량종류']) else ''
    if '모주 당일권'  in h: return '모주_당일권'
    if '모주 3시간권' in h: return '모주_3시간권'
    if '모주 야간권'  in h: return '모주_야간권'
    if '모주 심야권'  in h: return '모주_심야권'
    if '전액 할인'   in h: return '전액할인'
    if '5시간 할인'  in h: return '5시간할인'
    if '3시간 할인'  in h: return '3시간할인'
    if '1시간 할인' in h or '30분 할인' in h or '10분 할인' in h: return '시간단위할인'
    if h == '':
        if any(k in vt for k in INTERNAL_TYPES): return '정기/내부'
        return '일반유료'
    return '기타'

def parse_discount_min(h):
    if pd.isna(h): return 0
    t = 0
    for u, m in [('10분',10),('30분',30),('1시간',60),('3시간',180),('5시간',300)]:
        for n in re.findall(rf'{u} 할인\((\d+)\)', str(h)):
            t += int(n) * m
    return t

def make_record(row):
    return {
        "month"          : row['연월'],
        "total"          : int(row['총건수']),
        "paid_count"     : int(row['유료건수']),
        "revenue"        : int(row['총수익']),
        "discount_amount": int(row['총할인액']),
        "passes": {
            "당일권" : int(row.get('당일권', 0)),
            "3시간권": int(row.get('삼시간권', 0)),
            "야간권" : int(row.get('야간권', 0)),
            "심야권" : int(row.get('심야권', 0)),
        },
        "discount_types": {c: int(row.get(c, 0)) for c in DISC_COLS  if c in row.index},
        "vehicle_types" : {c: int(row.get(c, 0)) for c in VTYPE_COLS if c in row.index},
    }

def build_daily_analysis(df):
    daily_a = df[(df['할인분류']=='모주_당일권') & (df['입차시간'] >= '2025-09-01')].copy()
    if daily_a.empty:
        return {}
    daily_a['체류구간'] = pd.cut(daily_a['체류분'], bins=DUR_BINS, labels=DUR_LABS)
    wday = daily_a[daily_a['요일'] < 5]
    sat  = daily_a[daily_a['요일'] == 5]
    return {
        "period_note"            : "2025-09 이후",
        "total_count"            : len(daily_a),
        "avg_stay_min"           : round(float(daily_a['체류분'].mean()), 1),
        "median_stay_min"        : round(float(daily_a['체류분'].median()), 1),
        "weekday"                : {"count": len(wday), "avg_stay_min": round(float(wday['체류분'].mean()), 1) if len(wday) else 0},
        "saturday"               : {"count": len(sat),  "avg_stay_min": round(float(sat['체류분'].mean()),  1) if len(sat)  else 0},
        "duration_distribution"  : {k: int(v) for k,v in daily_a['체류구간'].value_counts().reindex(DUR_LABS).fillna(0).items()},
        "entry_hour_distribution": {str(k): int(v) for k,v in daily_a['입차시'].value_counts().sort_index().items()},
        "exit_hour_distribution" : {str(k): int(v) for k,v in daily_a['출차시간'].dt.hour.value_counts().sort_index().items()},
    }

def build_affiliate(df):
    aff = df[df['할인분류'].isin(['시간단위할인','3시간할인','5시간할인','전액할인'])].copy()
    if aff.empty: return {}
    return {
        "total_count"           : len(aff),
        "total_discount_min"    : int(aff['할인분(분)'].sum()),
        "avg_discount_min"      : round(float(aff['할인분(분)'].mean()), 1),
        "total_discount_amount" : int(aff['할인 요금'].sum()),
        "monthly": aff.groupby('연월').agg(
            count=('할인분(분)','count'), discount_amount=('할인 요금','sum'), avg_min=('할인분(분)','mean')
        ).round(1).reset_index().to_dict('records'),
    }

def build_mooju(df):
    mooju = df[df['할인분류'].str.startswith('모주_', na=False)].copy()
    if mooju.empty: return {}
    return {
        "total_count"           : len(mooju),
        "total_discount_amount" : int(mooju['할인 요금'].sum()),
        "by_type": {
            t: {
                "count"          : int((mooju['할인분류']==f'모주_{t}').sum()),
                "avg_stay_min"   : round(float(mooju[mooju['할인분류']==f'모주_{t}']['체류분'].mean()), 1)
                                    if (mooju['할인분류']==f'모주_{t}').any() else 0,
                "discount_amount": int(mooju[mooju['할인분류']==f'모주_{t}']['할인 요금'].sum()),
            } for t in ['당일권','3시간권','야간권','심야권']
        }
    }

def convert(xlsx_path, existing_json=None, out_path=None):
    xlsx_path = Path(xlsx_path)
    print(f"[1/5] 엑셀 읽는 중: {xlsx_path.name}")
    df = pd.read_excel(xlsx_path)
    df['입차시간'] = pd.to_datetime(df['입차시간'])
    df['출차시간'] = pd.to_datetime(df['출차시간'])

    old_records = []
    old_data    = {}

    if existing_json and Path(existing_json).exists():
        print(f"[2/5] 기존 JSON 로드 → 중복 월 제거: {existing_json}")
        with open(existing_json, encoding='utf-8') as f:
            old_data = json.load(f)
        old_records = old_data.get('monthly', [])
        existing_months = {r['month'] for r in old_records}
        df['_연월'] = df['입차시간'].dt.to_period('M').astype(str)
        overlap = existing_months & set(df['_연월'].unique())
        if overlap:
            print(f"    ※ 중복 월 → 기존 유지, 신규에서 제거: {sorted(overlap)}")
            df = df[~df['_연월'].isin(overlap)]
        df = df.drop(columns=['_연월'])
        if df.empty:
            print("    → 추가할 신규 월 없음. 종료.")
            return
    else:
        print("[2/5] 기존 JSON 없음 → 전체 신규 변환")

    print("[3/5] 전처리 및 분류 중...")
    df['체류분']   = (df['출차시간'] - df['입차시간']).dt.total_seconds() / 60
    df['연월']    = df['입차시간'].dt.to_period('M').astype(str)
    df['입차시']  = df['입차시간'].dt.hour
    df['요일']    = df['입차시간'].dt.dayofweek
    df['할인분류'] = df.apply(classify, axis=1)
    df['할인분(분)'] = df['할인명'].apply(parse_discount_min)
    for p, lab in PASS_MAP:
        df[lab] = df['할인명'].str.contains(p, na=False)

    print("[4/5] 월별 집계 중...")
    base = df.groupby('연월').agg(
        총건수=('차량종류','count'), 유료건수=('결제 요금', lambda x: (x>0).sum()),
        총수익=('결제 요금','sum'), 총할인액=('할인 요금','sum'),
        당일권=('당일권','sum'), 삼시간권=('3시간권','sum'),
        야간권=('야간권','sum'), 심야권=('심야권','sum'),
    ).reset_index()
    dp = df.groupby(['연월','할인분류']).size().unstack(fill_value=0).reset_index()
    vp = df.groupby(['연월','차량종류']).size().unstack(fill_value=0).reset_index()
    merged = base.merge(dp, on='연월', how='left').merge(vp, on='연월', how='left').fillna(0)
    new_records = [make_record(row) for _, row in merged.iterrows()]

    all_records = sorted(old_records + new_records, key=lambda r: r['month'])

    # 분석 섹션: 신규 데이터 있으면 갱신, 없으면 기존 유지
    daily_analysis = build_daily_analysis(df) or old_data.get('daily_ticket_analysis', {})
    aff_summary    = build_affiliate(df)       or old_data.get('affiliate_discount', {})
    mooju_summary  = build_mooju(df)           or old_data.get('mooju_passes', {})

    output = {
        "meta": {
            "source"       : xlsx_path.name,
            "generated"    : datetime.now().strftime('%Y-%m-%d %H:%M'),
            "period"       : {"start": all_records[0]['month'], "end": all_records[-1]['month']},
            "total_records": sum(r['total'] for r in all_records),
        },
        "monthly"              : all_records,
        "daily_ticket_analysis": daily_analysis,
        "affiliate_discount"   : aff_summary,
        "mooju_passes"         : mooju_summary,
    }

    if out_path is None:
        out_path = xlsx_path.parent.parent / 'data' / 'parking_data.json'
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    s, e = all_records[0]['month'], all_records[-1]['month']
    print(f"[5/5] 완료 → {out_path}  ({out_path.stat().st_size:,} bytes)")
    print(f"      기간: {s} ~ {e} | 총 {output['meta']['total_records']:,}건 ({len(all_records)}개월)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("사용법:")
        print("  첫 변환: python scripts/convert.py data/raw/파일.xlsx")
        print("  추가:    python scripts/convert.py data/raw/새파일.xlsx data/parking_data.json")
        sys.exit(1)
    convert(sys.argv[1],
            sys.argv[2] if len(sys.argv) > 2 else None,
            sys.argv[3] if len(sys.argv) > 3 else None)
