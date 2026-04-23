# CPBC 주차장 대시보드

## 프로젝트 개요
가톨릭평화방송(CPBC) 주차장 입출차 데이터 및 매출 데이터를 분석하고 시각화하는 대시보드.

## 기술 스택
- Python / pandas: 엑셀 → JSON 변환
- 순수 HTML/JS + Chart.js: 대시보드 (dashboard.html, 서버 불필요)
- GitHub Pages: 배포 (https://twowhy-prog.github.io/parking-inf/dashboard.html)

## 파일 구조
```
parking-inf/
├── dashboard.html               ← 대시보드 본체 (INLINE_DATA 내장)
├── data/
│   ├── parking_data.json        ← 입출차 집계 데이터
│   ├── revenue_data.json        ← 매출 집계 데이터
│   ├── raw/                     ← 입출차 원본 엑셀
│   └── revenue/                 ← 매출 원본 엑셀 (연도별)
│       ├── 2023년 주차장 매출.xlsx
│       ├── 2024년 주차장 매출.xlsx
│       ├── 2025년 주차장 매출.xlsx
│       └── 2026년 주차장 매출.xlsx
├── scripts/
│   ├── convert.py               ← 입출차 엑셀 → parking_data.json
│   ├── convert_revenue.py       ← 매출 엑셀 → revenue_data.json
│   ├── update.bat               ← Windows 자동화 (입출차+매출 변환+커밋+푸시)
│   └── update.sh                ← Linux/Mac 자동화
└── .github/workflows/
    └── update-data.yml          ← GitHub Actions (엑셀 업로드 시 자동 변환)
```

## 데이터 구조

### parking_data.json (입출차)
- monthly[]: 월별 집계 (건수, 유료건수, 패스권, 할인분류, 차종별)
- daily_ticket_analysis: 당일권 체류 패턴 (2025-09 이후)
- affiliate_discount: 제휴 할인 월별 현황
- mooju_passes: 모두의주차 패스권 4종 상세

### revenue_data.json (매출)
- monthly[]: 월별 매출 (total, subtotal, mooju, categories)
  - categories: 입주사 / 직원정기 / 직원일일 / 관리실 정기 / 관리실 일일 / 일반 정기 / 일일매출
  - mooju: 모두의주차 별도 집계 (2025-08 이후)

## 매출 구조
- 현장 일반 결제 (카드/현금)
- 모두의주차(모주) 할인권 판매 — 2025-08부터 별도 집계
- 정기권 판매 (입주사/직원/일반) — 구글시트 원본, revenue_data.json에 집계

## 할인 분류 기준
- 모주_당일권 / 모주_3시간권 / 모주_야간권 / 모주_심야권
- 시간단위할인 / 3시간할인 / 5시간할인 / 전액할인 (제휴)
- 정기/내부 / 일반유료
- 야간권 → 심야권 통합: 2026-01부터 (대시보드 차트에 자동 표시)

## 대시보드 탭 구성
1. 월별 이용 추이 — 입출차 건수, 필터(월별/분기별/연도별/날짜범위)
2. 패스권 현황 — 모주 4종 추이, 야간→심야 통합 시점 annotation
3. 당일권 분석 — 체류 패턴, 시간대 분포 (2025-09 이후)
4. 할인권 분석 — 이용 건수·체류 시간 중심 (금액 제외)
5. 차종별 현황 — 차량 유형별 비율
6. 수익 현황 — 현장+모주 월별 매출, 카테고리별 비중

## 로컬 데이터 갱신 방법

### 입출차 데이터 추가 (매월)
```
엑셀 파일 → C:\Users\김상현\Desktop\주차입출입내역엑셀파일\ 에 넣기
scripts\update.bat 더블클릭
```

### 매출 데이터 갱신 (연간)
```
data\revenue\ 폴더의 연도별 xlsx 파일 업데이트 후
python scripts\convert_revenue.py
```

### GitHub 웹에서 업로드 시
- 입출차: data/raw/ 에 xlsx 업로드 → GitHub Actions 자동 실행
- 매출: data/revenue/ 에 xlsx 업로드

## 작업 요청 예시
- "5월 데이터 추가해줘" → update.bat 실행 안내 또는 convert.py 직접 실행
- "수익 탭에 전월 대비 증감률 추가해줘" → dashboard.html renderRevenue() 수정
- "당일권 탭에 요일별 차트 추가해줘" → dashboard.html renderDaily() 수정
- "2026년 매출 파일 업데이트" → data/revenue/2026년 주차장 매출.xlsx 교체 후 convert_revenue.py 실행
