# 📚 한국어교원 채용 통합 대시보드 (Korean Teacher Jobs Dashboard)

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Daily Crawl Status](https://github.com/actions/workflow/status/BICLO/korean-teacher-jobs-search/daily_crawl.yml?label=Daily%20Crawl&logo=githubactions&logoColor=white)](.github/workflows/daily_crawl.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

대한민국 5대 한국어교원 채용 공고 사이트의 정보를 실시간으로 수집하고, 비관련 공고 및 결과 발표 공지를 자동 정제하여 모바일과 PC에 최적화된 반응형 웹으로 제공하는 통합 대시보드입니다. GitHub Actions를 통해 매일 새벽 최신 공고가 자동으로 갱신됩니다.

---

## 🌐 대상 사이트 및 데이터 소스

| 사이트명 | 포털 구분 | 수집 대상 게시판 / URL | 수집 방식 |
| :--- | :--- | :--- | :--- |
| **국립국어원 한국어교원** | 공공 포털 | [구인게시판](https://kteacher.korean.go.kr/jobsearch/list) | Web Scraping (Pagination & Table Analysis) |
| **KLE Ocean (한국어교육바다)** | 교원 전문 커뮤니티 | [국내/해외 채용마당](https://kleocean.com) | KBoard RSS Feed Parsing + 정규표현식 메타 추출 |
| **세종학당재단** | 공공/해외파견 | [채용안내 (파견교원 / 직원채용)](https://www.ksif.or.kr) | 전자정부프레임워크 게시판 파싱 & 노이즈 필터링 |
| **다누리 (다문화가족지원포털)** | 여성가족부 포털 | [전국 다문화센터 채용정보](https://www.liveinkorea.kr) | 실시간 접수 공고(`search_recruit_stat=02`) 타겟팅 |
| **워크넷 (고용24)** | 국가 고용 포털 | [채용정보 상세검색](https://www.work24.go.kr) | 세션 기반 mForm 타겟팅 수집 & 한국어 교육직 정제 |

---

## 🚀 주요 기능 (Key Features)

### 1. 실시간 핵심 지표 (KPI Metrics)
- **접수중인 전체 공고**: 현재 지원 가능한 활성 채용 공고 총수
- **마감 임박 (D-7 이내)**: 7일 이내 마감 예정인 긴급 공고 수 (빨간색 강조)
- **해외 파견 / 취업**: 세종학당 파견 및 해외 교육기관 채용 공고 수
- **필터 조회 결과**: 사용자가 선택한 조건에 부합하는 공고 수

### 2. 다차원 상세 필터 및 정렬
- **스마트 키워드 검색**: 공고 제목 및 기관명 실시간 동시 검색 (대소문자 무관)
- **채용 출처 선택**: 국립국어원, 한국어교육바다, 세종학당재단, 다누리, 워크넷 개별/전체 조회
- **근무 지역 분류**: 서울, 경기, 인천, 강원, 충북, 충남/대전/세종, 전북, 전남/광주, 경북/대구, 경남/부산/울산, 제주, 해외, 온라인/재택 등 자동 분류
- **교원 자격 등급**: 1급, 2급, 3급, 자격소지자, 무관/미지정 필터링
- **접수 상태 필터**: 전체 / 접수중(마감 제외) / 마감임박순(D-7 이내) 라디오 선택
- **3중 정렬 옵션**: 마감일 빠른순, 최근 등록순, 기관명 가나다순

### 3. 모바일/PC 반응형 듀얼 뷰 (Dual View Mode)
- **🗂️ 카드 뷰 (추천)**:
  - 출처별 전용 배지 (`국립국어원: 블루`, `KLE: 그린`, `세종학당: 오렌지`, `다누리: 퍼플`, `워크넷: 틸/민트`)
  - D-Day 상태 칩 (`D-Day: 위험(빨강)`, `D-7 이내: 주의(노랑)`, `D-8 이상: 안전(초록)`, `상시: 그레이`)
  - 근무지 및 교원 자격 요건 태그
  - 원문 공고 원클릭 새창 열기
- **📋 테이블 뷰**:
  - 컬럼별 정렬 및 너비 최적화 데이터테이블
  - **📥 필터링된 공고 CSV 다운로드** (Excel 한글 깨짐 방지 `UTF-8 with BOM` 적용)

---

## 🧠 자가진단 및 노이즈 정제 파이프라인 (Self-Diagnosis Cleaner)

단순한 크롤링을 넘어 실제 구직자에게 유효한 정보만 전달하도록 다단계 노이즈 필터링이 적용되어 있습니다.

```
[Raw Crawled Postings] (약 180+건)
         │
         ▼
[1단계: 결과 발표 및 면접 공지 필터링]
  - '합격자 발표', '서류전형 결과', '면접 대상자 안내', '최종 합격' 등 제외
         │
         ▼
[2단계: 비관련 직종 필터링]
  - 다문화가족지원센터의 '아이돌봄', '조리사', '사회복지사', '보듬매니저', '운전원' 등
  - 단, '한국어', '강사', '교원', '다문화언어발달' 키워드가 명시된 경우 정상 수집
         │
         ▼
[3단계: 마감일 검증 및 만료 공지 처리]
  - 'YYYY-MM-DD' 기준 현재 일자 이전(D < 0) 공고는 `is_closed=True` 처리
  - '접수중' 필터 선택 시 자동 제외
         │
         ▼
[4단계: 중복 제거 및 데이터 규격화]
  - (URL, Title) 기반 해시 중복 제거
         │
         ▼
[최종 정제 완료: data/jobs.json] (유효 활성 공고 58건)
```

---

## 📊 표준 데이터 스키마 (Data Schema)

`data/jobs.json`에 저장되는 데이터 형식:

```json
[
  {
    "id": "kteacher_12345",
    "source": "국립국어원",
    "title": "[공고] 2026학년도 1학기 한국어학당 한국어교원 채용 공고",
    "organization": "○○대학교 언어교육원",
    "location": "서울",
    "grade": "2급",
    "deadline": "2026-09-25",
    "url": "https://kteacher.korean.go.kr/jobsearch/view?seq=12345",
    "is_closed": false,
    "created_at": "2026-09-01"
  }
]
```

### 필드 정의
- `id` (String): 출처 코드와 원본 게시물 식별자로 생성된 고유 키
- `source` (String): 출처명 (`국립국어원`, `한국어교육바다`, `세종학당재단`, `다누리`, `워크넷`)
- `title` (String): 채용 공고 제목 (공백 및 특수문자 정제)
- `organization` (String): 채용 기관명 / 학교명
- `location` (String): 정규화된 근무 지역 (예: `서울`, `경기`, `해외` 등)
- `grade` (String): 요구 교원 자격 등급 (`1급`, `2급`, `3급`, `자격소지자`, `무관/미지정`)
- `deadline` (String): 접수 마감일 (`YYYY-MM-DD` 또는 `상시채용`)
- `url` (String): 원본 공고 바로가기 URL
- `is_closed` (Boolean): 마감 여부 (만료 시 `true`)
- `created_at` (String): 공고 등록일 (`YYYY-MM-DD`)

---

## 📂 프로젝트 구조 (Directory Structure)

```
korean-teacher-jobs-search/
├── .github/
│   └── workflows/
│       └── daily_crawl.yml      # GitHub Actions 매일 새벽 자동 크롤링 & 커밋
├── data/
│   ├── jobs.json                # 정제된 최신 채용 공고 데이터셋
│   └── published_kboard.json    # 워드프레스 KBoard 자동 발행 이력 (중복 방지)
├── src/
│   ├── __init__.py
│   ├── crawler.py               # 5개 사이트 모듈식 수집기 및 파이프라인 총괄
│   ├── cleaner.py               # 결과 공지/비관련 직종/만료일자 정제 및 검증 모듈
│   ├── publisher.py             # 워드프레스(KBoard) slowAES 우회 및 자동 발행 모듈
│   └── utils.py                 # 네트워크 재시도, 날짜 계산, 자격/지역 정규표현식 유틸
├── app.py                       # Streamlit 반응형 웹 대시보드
├── requirements.txt             # 파이썬 의존성 패키지 목록
└── README.md                    # 프로젝트 종합 안내서
```

---

## 💻 로컬 개발 및 실행 방법 (Local Getting Started)

### 1. 레포지토리 복제 및 가상환경 설정
```bash
git clone https://github.com/YOUR_USERNAME/korean-teacher-jobs-search.git
cd korean-teacher-jobs-search

# Python 3.11+ 가상환경 생성
python -m venv .venv

# 가상환경 활성화
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터 수집 파이프라인 실행 (크롤러)
```bash
python src/crawler.py
```
> 실행 시 4대 사이트에서 공고를 수집하고 `src/cleaner.py`를 거쳐 `data/jobs.json`에 저장됩니다.

### 4. 대시보드 웹 실행
```bash
streamlit run app.py
```
브라우저에서 `http://localhost:8501`로 접속합니다.

---

## ☁️ 배포 가이드 (Deployment Guide)

### Streamlit Community Cloud (무료 1-클릭 호스팅)

1. [Streamlit Community Cloud](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
2. **"Create app"** 버튼을 클릭합니다.
3. 설정을 다음과 같이 입력합니다:
   - **Repository**: `YOUR_USERNAME/korean-teacher-jobs-search`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: 원하는 도메인명 지정 (예: `korean-teacher-jobs`)
4. **"Deploy!"** 버튼을 클릭하면 약 1분 이내에 글로벌 라이브 URL로 서비스가 배포됩니다.
5. GitHub Actions가 `data/jobs.json`을 자동 갱신하면 Streamlit 웹 앱에 즉시 최신 공고가 반영됩니다.

---

## 🌐 워드프레스 KBoard 자동 발행 연동 시스템

수집 및 정제된 한국어교원 채용 공고를 외부 워드프레스 커뮤니티의 KBoard 게시판으로 자동 전송 및 발행합니다.

- **연동 대상 사이트**: [https://korean-teacher.infinityfreeapp.com](https://korean-teacher.infinityfreeapp.com) (KBoard 게시판 ID: `1`)
- **보안 방어벽 우회 기술**:
  - InfinityFree 무료 호스팅의 `slowAES` 봇 방지 챌린지를 파이썬 `pycryptodome` (AES-128-CBC)으로 역연산하여 `__test` 세션 쿠키를 자동 발급받아 통신합니다.
- **안전한 브릿지 통신**:
  - `htdocs/post_bridge.php` 엔드포인트를 통해 비밀 키(`korean_secret_key_2026`) 기반으로 KBoard 전용 클래스(`KBContent`)를 직접 호출하여 안전하게 등록합니다.
- **중복 발행 방지 (Deduplication)**:
  - `data/published_kboard.json`에 기발행 공고 ID와 생성된 `kboard_uid`를 영구 저장하여, 매일 새로 수집된 신규 공고만 선별적으로 발행합니다.
- **반응형 HTML 본문 서식화**:
  - 출처, 마감일, 근무 지역, 자격 요건 및 원클릭 원문 바로가기 버튼이 포함된 스타일드 카드로 게시글 본문이 자동 생성됩니다.

---

## ⚙️ CI/CD 자동화 (GitHub Actions)

`.github/workflows/daily_crawl.yml` 파일에 구성되어 있습니다.

- **실행 주기**: 매일 한국 표준시 06:00 (UTC 21:00)
- **수동 트리거**: GitHub 레포지토리 > **Actions** 탭 > **Daily Korean Teacher Jobs Crawl** > **Run workflow** 클릭
- **동작 방식**:
  1. Ubuntu 가상환경에서 Python 3.11 설정 및 캐시 로드
  2. `requirements.txt` 패키지 설치
  3. `python src/crawler.py` 실행을 통한 데이터 수집 및 정제
  4. 변경사항이 있을 경우에만 GitHub Actions Bot 계정으로 `data/jobs.json` 자동 커밋 & 푸시 (`[skip ci]` 태그로 무한 루프 방지)

---

## 📄 라이선스 (License)

본 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.
공공 데이터 및 수집 정보의 저작권은 각 원본 사이트(국립국어원, 한국어교육바다, 세종학당재단, 다누리)에 있습니다.
