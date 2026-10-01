@echo off
chcp 65001 > nul
title 한국어교원 채용공고 관리자 콘솔
cd /d "%~dp0"
echo ======================================================
echo    한국어교원 채용공고 운영자 관리 콘솔 실행 중...
echo    브라우저가 자동으로 열립니다 (http://localhost:8501)
echo ======================================================
.\.venv\Scripts\streamlit.exe run app.py
pause
