@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set REPO=%~dp0..
set INBOX=%REPO%\주차입출입내역엑셀파일
set RAW=%REPO%\data\raw

:: ── 가장 최근 xlsx 찾기 ──────────────────────────────────────────
set XLSX=
for /f "delims=" %%F in ('dir /b /od "%INBOX%\*.xlsx" 2^>nul') do set XLSX=%%F

if "!XLSX!"=="" (
    echo 오류: %INBOX% 에 xlsx 파일이 없습니다.
    pause
    exit /b 1
)

echo 변환 대상: !XLSX!
copy /y "%INBOX%\!XLSX!" "%RAW%\!XLSX!" > nul
echo data\raw\ 에 복사 완료

:: ── 변환 실행 ────────────────────────────────────────────────────
cd /d "%REPO%"
python scripts\convert.py "data\raw\!XLSX!" data\parking_data.json
if errorlevel 1 (
    echo 변환 실패
    pause
    exit /b 1
)

:: ── 커밋 메시지 자동 생성 ────────────────────────────────────────
for /f "delims=" %%M in ('python -c "import json; d=json.load(open('data/parking_data.json',encoding='utf-8')); print(d['meta']['period']['end'])"') do set LAST_MONTH=%%M

echo.
set /p MSG=커밋 메시지 [기본: data: %LAST_MONTH%]:
if "!MSG!"=="" set MSG=data: %LAST_MONTH%

git add dashboard.html data/parking_data.json "data/raw/!XLSX!"
git commit -m "!MSG!"
git push

echo.
echo 완료^! https://twowhy-prog.github.io/parking-inf/dashboard.html
pause
