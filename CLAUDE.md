# CPBC 주차장 대시보드

## 프로젝트 개요
가톨릭평화방송(CPBC) 주차장 입출차 데이터를 분석하고 시각화하는 대시보드.

## 기술 스택
- Python / pandas: 엑셀 → JSON 변환 (scripts/convert.py)
- 순수 HTML/JS + Chart.js: 대시보드 (dashboard.html, 서버 불필요)
- GitHub Pages: 배포

## 파일 구조
parking-dashboard/
├── dashboard.html          ← 대시보드 본체 (JSON 인라인 내장)
├── scripts/convert.py      ← 엑셀 → JSON + HTML 자동 갱신
├── data/parking_data.json  ← 변환된 집계 데이터
└── data/raw/               ← 원본 엑셀 보관

## 데이터 구조 (parking_data.json)
- monthly[]: 월별 집계 (건수, 수익, 패스권, 할인분류, 차종별)
- daily_ticket_analysis: 당일권 체류 패턴 (2025-09 이후)
- affiliate_discount: 제휴 할인 월별 현황
- mooju_passes: 모두의주차 패스권 4종 상세

## 할인 분류 기준
- 모주_당일권 / 모주_3시간권 / 모주_야간권 / 모주_심야권
- 시간단위할인 / 3시간할인 / 5시간할인 / 전액할인 (제휴)
- 정기/내부 / 일반유료

## 새 엑셀 추가할 때
python scripts/convert.py data/raw/새파일.xlsx data/parking_data.json
→ parking_data.json + dashboard.html 자동 갱신
→ git add . && git commit -m "data: YYYY-MM" && git push

## 작업 요청 예시
- "5월 데이터 추가해줘" → convert.py 실행
- "당일권 탭에 요일별 차트 추가해줘" → dashboard.html 수정
- "대시보드에 수익 전월 대비 증감률 추가해줘" → dashboard.html 수정
