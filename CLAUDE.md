# CPBC 주차장 대시보드

## 프로젝트 개요
가톨릭평화방송(CPBC) 주차장 입출차 데이터를 분석하고 시각화하는 대시보드.

## 기술 스택
- Python / pandas: 엑셀 → JSON 변환 (scripts/convert.py)
- 순수 HTML/JS + Chart.js 4.4.1: 대시보드 (dashboard.html, 서버 불필요)
- GitHub Pages: 배포

## 파일 구조
parking-inf/
├── dashboard.html              ← 대시보드 본체 (JSON 인라인 내장)
├── scripts/convert.py          ← 엑셀 → JSON + HTML 자동 갱신
├── data/parking_data.json      ← 변환된 집계 데이터
├── data/raw/                   ← 입출차 원본 엑셀 보관
└── data/revenue/               ← 수익 원본 엑셀 (연도별)
    ├── 2024년 주차장 수익.xlsx  ← 월별 시트 → '합계' 행이 실제 수익
    ├── 2025년 주차장 수익.xlsx
    └── 2026년 주차장 수익.xlsx

## 대시보드 탭 구조 (4탭, 2025-04 재구성)
| 탭 | data-p | 렌더 함수 | 주요 콘텐츠 |
|---|---|---|---|
| 종합 현황 | overview | renderOverview() | KPI 4종, 입출차+수익 복합차트, 유료율 추이, 최근 6개월 요약 테이블 |
| 수익 분석 | revenue | renderRevenue() | KPI 4종, 입출차 막대, 수익+건당수익 이중축 차트, 월별 랭킹 |
| 할인·패스 분석 | discount | renderDiscount() | 패스권 stacked bar, 패스권 도넛, 모주 콤보, 제휴할인 추이, 할인유형 도넛 |
| 이용 패턴 | pattern | renderPattern() | 입출차 시간대 분포, 체류시간 분포, 인사이트 |

### 탭 전환 방식
- `.tab[data-p]` 클릭 → `#page-{data-p}` show/hide
- 각 탭 렌더 함수는 `load()` 에서 일괄 호출 (페이지 로드 1회)

## 데이터 구조 (parking_data.json)
- `monthly[]`: 월별 집계 (건수, 수익, 패스권, 할인분류, 차종별)
  - ⚠️ `revenue` 필드는 **data/revenue/*.xlsx 각 월 시트의 합계** 기준
  - 입출차 로그의 `결제 요금`만 쓰면 정기주차·계약 수입이 빠져 수치가 ~1/3로 잘못됨
- `daily_ticket_analysis`: 당일권 체류 패턴 (2025-09 이후)
- `affiliate_discount`: 제휴 할인 월별 현황
  - ⚠️ `affiliate_discount.monthly[]` 항목의 월 키는 **`연월`** (month 아님)
  - 접근: `r['연월']` — `r.month` 사용 시 undefined 에러 발생
- `mooju_passes`: 모두의주차 패스권 4종 상세

## 할인 분류 기준
- 모주_당일권 / 모주_3시간권 / 모주_야간권 / 모주_심야권
- 시간단위할인 / 3시간할인 / 5시간할인 / 전액할인 (제휴)
- 정기/내부 / 일반유료

## 공통 필터
- `filtMonthly()`: 불완전 월(현재: 2026-04) 제외한 monthly[] 반환
- `RNG`: 수익 분석 탭의 기간 범위 상태 (setR() 로 갱신)

## 새 엑셀 추가할 때

### 입출차 데이터 추가 (할인·패스·이용패턴 탭)
python scripts/convert.py data/raw/새파일.xlsx data/parking_data.json

### 수익 데이터 업데이트 (수익 분석 탭)
수익 엑셀 파일(data/revenue/YYYY년 주차장 수익.xlsx) 업데이트 후:
python scripts/update_revenue.py
→ 각 월 시트의 '합계' 행 값을 monthly[].revenue 에 반영

→ git add . && git commit -m "data: YYYY-MM" && git push

## 작업 요청 예시
- "5월 데이터 추가해줘" → convert.py 실행
- "종합 현황 탭에 전월 대비 증감률 추가해줘" → renderOverview() 수정
- "할인·패스 탭에 차트 추가해줘" → renderDiscount() 수정
- "이용 패턴 탭에 요일별 분포 추가해줘" → renderPattern() 수정
