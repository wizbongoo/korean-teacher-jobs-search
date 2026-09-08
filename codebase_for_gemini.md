# 📚 [프로젝트 전체 코드 분석 요청서] 한국어교원 채용 통합 대시보드

> 이 문서는 Google Gemini에게 프로젝트 전체 구조 및 소스 코드를 심층 분석시키기 위해 자동 생성된 번들 파일입니다.

## 🤖 Gemini 분석 가이드 (System Prompt)

```markdown
당신은 시니어 풀스택 소프트웨어 엔지니어이자 파이썬/데이터 파이프라인 아키텍트입니다.
아래에 첨부된 한국어교원 채용 대시보드 프로젝트의 전체 소스 코드를 면밀히 검토하고, 다음 항목에 대해 심층 분석 보고서를 작성해 주세요:

1. **아키텍처 및 모듈 분리 평가**: 크롤러, 데이터 정제기, 유틸리티, Streamlit 웹 UI 간의 결합도 및 확장성 진단
2. **크롤링 및 데이터 수집 안정성 분석**: 5대 포털(국립국어원, KLE Ocean, 세종학당재단, 다누리, 워크넷) 파싱 로직, 세션 처리, 네트워크 장애 대응력
3. **데이터 정제(자가진단) 품질**: 비관련 직종, 결과 발표 공지, 만료일자 필터링 규칙의 빈틈 및 개선점
4. **성능 및 보안 진단**: 메모리 누수, 불필요한 반복 연산, 외부 요청 예외 처리 및 잠재적 병목
5. **프로덕션 고도화 로드맵 제안**: SQLite/PostgreSQL 등 DB 도입, 비동기(asyncio) 수집, 알림 기능(카카오톡/텔레그램) 등 추천 발전 방향
```

## 📂 프로젝트 구조 (Directory Tree)

```text
korean-teacher-jobs-search/
├── .github/workflows/daily_crawl.yml  # GitHub Actions 매일 새벽 자동 수집 워크플로우
├── data/jobs.json                     # 정제 완료된 채용 공고 데이터셋 (59건)
├── src/
│   ├── __init__.py
│   ├── crawler.py                     # 5대 포털 모듈식 수집기 및 오케스트레이터
│   ├── cleaner.py                     # 노이즈 필터링 및 데이터 품질 자가진단 모듈
│   └── utils.py                       # 재시도 HTTP 요청, 날짜/D-Day/자격/지역 파싱
├── tests/test_pipeline.py             # 5개 자동화 단위 테스트 스위트
├── app.py                             # Streamlit 반응형 웹 대시보드
├── requirements.txt                   # 의존성 패키지
└── README.md                          # 프로젝트 종합 가이드
```

## 📊 데이터셋 현황 (`data/jobs.json` - 총 59건 중 상위 3건 샘플)

```json
[
  {
    "id": "kteacher_34727",
    "source": "국립국어원",
    "title": "2026학년도 하반기 3쿼터 건양대학교 한국어교육센터 한국어강사 추가 모집 공고",
    "organization": "건양대학교 국제교육팀",
    "location": "전국/기타",
    "grade": "무관/미지정",
    "deadline": "2026-09-08",
    "url": "https://kteacher.korean.go.kr/jobsearch/34727",
    "is_closed": false,
    "created_at": "2026-09-04"
  },
  {
    "id": "kteacher_34613",
    "source": "국립국어원",
    "title": "광주남구가족센터 결혼이민자역량강화지원(한국어 교육) 강사(위촉직) 모집 공고",
    "organization": "광주남구가족센터",
    "location": "전남/광주",
    "grade": "무관/미지정",
    "deadline": "2026-09-17",
    "url": "https://kteacher.korean.go.kr/jobsearch/34613",
    "is_closed": false,
    "created_at": "2026-09-03"
  },
  {
    "id": "kteacher_34564",
    "source": "국립국어원",
    "title": "경기한국어랭귀지스쿨(단기형) 디딤돌학교(초등)  시간제 강사 채용 공고",
    "organization": "수원시글로벌청소년드림센터",
    "location": "경기",
    "grade": "무관/미지정",
    "deadline": "2026-09-15",
    "url": "https://kteacher.korean.go.kr/jobsearch/34564",
    "is_closed": false,
    "created_at": "2026-09-02"
  }
]
```

## 💻 전체 소스 코드 전문 (Full Source Code)

### 📄 `requirements.txt`

```txt
streamlit>=1.35.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
python-dateutil>=2.8.2
lxml>=5.0.0

```

### 📄 `.github/workflows/daily_crawl.yml`

```yaml
name: Daily Korean Teacher Jobs Crawl

on:
  schedule:
    # 매일 한국 시간 06:00 (UTC 21:00)에 실행
    - cron: '0 21 * * *'
  workflow_dispatch: # 수동 즉시 실행 지원

permissions:
  contents: write

jobs:
  crawl-and-update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Crawler Pipeline
        run: |
          python src/crawler.py

      - name: Commit and Push if updated
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add data/jobs.json
          if git diff --staged --quiet; then
            echo "No changes detected in data/jobs.json. Skipping commit."
          else
            git commit -m "chore(data): auto-update jobs data [$(date -u +'%Y-%m-%d %H:%M:%S UTC')] [skip ci]"
            git push
          fi

```

### 📄 `src/utils.py`

```python
import re
from datetime import datetime, date
import requests
from dateutil import parser as date_parser

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

def fetch_url(url: str, method: str = "GET", params: dict = None, data: dict = None, timeout: int = 20, headers: dict = None) -> str:
    """Fetch URL content with retry logic and standard browser headers."""
    req_headers = DEFAULT_HEADERS.copy()
    if headers:
        req_headers.update(headers)
    
    for attempt in range(3):
        try:
            if method.upper() == "POST":
                resp = requests.post(url, data=data, params=params, headers=req_headers, timeout=timeout, verify=True)
            else:
                resp = requests.get(url, params=params, headers=req_headers, timeout=timeout, verify=True)
            
            resp.encoding = resp.apparent_encoding or "utf-8"
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                return ""
        except requests.exceptions.RequestException as e:
            if attempt == 2:
                print(f"[Warning] Failed to fetch {url} after 3 attempts: {e}")
                return ""
    return ""

def parse_date(date_str: str) -> str:
    """Normalize various date formats into YYYY-MM-DD."""
    if not date_str:
        return ""
    
    date_str = str(date_str).strip()
    
    if any(k in date_str for k in ["상시", "채용시", "마감시"]):
        return "상시채용"
    
    # Check 8-digit format YYYYMMDD
    if re.match(r"^\d{8}$", date_str):
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    
    # Extract YYYY-MM-DD or YYYY.MM.DD or YYYY/MM/DD or YYYY년 MM월 DD일
    match = re.search(r"(\d{4})(?:[-./]|년\s*)(\d{1,2})(?:[-./]|월\s*)(\d{1,2})", date_str)
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    
    # Try dateutil parser (e.g. for RFC 822 RSS pubDate)
    try:
        dt = date_parser.parse(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    
    return ""

def calculate_dday(deadline_str: str, today: date = None) -> tuple[str, int, bool]:
    """
    Calculate D-day badge string, sorting integer, and is_closed boolean.
    Returns: (dday_label, dday_days, is_closed)
    """
    if today is None:
        today = datetime.now().date()
        
    if not deadline_str or deadline_str == "상시채용":
        return ("상시", 9999, False)
    
    parsed_date_str = parse_date(deadline_str)
    if not parsed_date_str:
        return ("미정", 9998, False)
        
    try:
        deadline_date = datetime.strptime(parsed_date_str, "%Y-%m-%d").date()
        diff = (deadline_date - today).days
        if diff < 0:
            return ("마감", diff, True)
        elif diff == 0:
            return ("D-Day", 0, False)
        else:
            return (f"D-{diff}", diff, False)
    except Exception:
        return ("미정", 9998, False)

def extract_grade(text: str) -> str:
    """Extract teacher certificate grade (1급, 2급, 3급, etc.) from text."""
    if not text:
        return "무관/미지정"
    
    # Check for specific grade mentions
    if "1급" in text and "2급" in text:
        return "1급/2급"
    elif "1급" in text:
        return "1급"
    elif "2급" in text and "3급" in text:
        return "2급/3급"
    elif "2급" in text:
        return "2급"
    elif "3급" in text:
        return "3급"
    elif "자격증" in text or "교원자격" in text:
        return "자격소지자"
    return "무관/미지정"

REGION_KEYWORDS = [
    ("해외", ["해외", "파견교원", "미국", "중국", "일본", "베트남", "태국", "우즈벡", "프랑스", "독일", "국외", "방글라데시", "스탠포드", "캘리포니아", "하노이", "호치민", "방콕", "도쿄", "오사카", "베이징", "상하이"]),
    ("온라인/재택", ["온라인", "재택", "비대면", "화상"]),
    ("서울", ["서울"]),
    ("경기", ["경기", "수원", "성남", "안성", "파주", "고양", "용인", "부천", "안산", "평택", "안양", "시흥", "김포", "화성", "광명", "이천", "양주", "구리", "오산", "남양주"]),
    ("인천", ["인천", "계양", "부평", "연수"]),
    ("강원", ["강원", "춘천", "원주", "강릉"]),
    ("충북", ["충북", "청주", "충주", "제천"]),
    ("충남/대전/세종", ["충남", "대전", "세종시", "세종특별", "천안", "아산", "논산", "공주", "보령", "서산"]),
    ("전북", ["전북", "전주", "익산", "군산"]),
    ("전남/광주", ["전남", "광주", "목포", "여수", "순천", "나주", "광양"]),
    ("경북/대구", ["경북", "대구", "포항", "구미", "경산", "경주", "안동"]),
    ("경남/부산/울산", ["경남", "부산", "울산", "창원", "김해", "양산", "진주", "거제"]),
    ("제주", ["제주", "서귀포"]),
]

def extract_location(text: str, default: str = "전국/기타") -> str:
    """Normalize and extract location from text."""
    if not text:
        return default
    
    for region, keywords in REGION_KEYWORDS:
        for kw in keywords:
            if kw in text:
                return region
    return default

```

### 📄 `src/cleaner.py`

```python
import re
from datetime import datetime, date
from typing import List, Dict, Tuple

EXCLUDE_TITLE_KEYWORDS = [
    "합격자", "최종합격", "합격 공고", "서류전형 결과", "서류 합격",
    "면접 심사", "면접 대상자", "면접 안내", "면접 공지", "면접 일정", "면접심사",
    "선발 결과", "채용 결과", "[마감]", "(마감)", "접수마감", "마감완료",
    "공고 취소", "채용 취소", "적격자 없음", "시험 장소", "필기시험",
    "재공고 알림", "공지사항", "노동실태 설문조사"
]

NON_TEACHER_KEYWORDS = [
    "아이돌봄", "조리사", "영양사", "환경미화", "시설관리",
    "보듬매니저", "공동육아", "가족상담", "사회복지사", "회계직", "차량기사",
    "상담사", "상담전문", "조공", "용접", "도장", "단순노무", "지게차", "운전원",
    "미화원", "생산직", "배송기사", "선원", "요양보호사"
]

TEACHER_MUST_HAVE_KEYWORDS = [
    "한국어", "한국학", "korean", "언어발달", "다문화언어", "토픽", "topik", "교원", "강사", "교수"
]

WORKNET_TEACHING_KEYWORDS = [
    "강사", "교원", "교사", "지도사", "교수", "학당", "교육"
]

class JobDataCleaner:
    def __init__(self, today: date = None):
        self.today = today or datetime.now().date()
        self.stats = {
            "raw_total": 0,
            "removed_ended_result": 0,
            "removed_non_teacher": 0,
            "removed_expired": 0,
            "removed_duplicate": 0,
            "clean_total": 0,
            "by_source_raw": {},
            "by_source_clean": {},
        }

    def is_ended_or_result_notice(self, title: str) -> bool:
        """Check if announcement is a result notice, interview notice, or ended."""
        for kw in EXCLUDE_TITLE_KEYWORDS:
            if kw in title:
                return True
        return False

    def is_relevant_teacher_job(self, title: str, source: str, organization: str = "") -> bool:
        """
        Check if the job is specifically related to Korean teaching / language education.
        Crucial for general boards like Danuri, Worknet, or KSIF general staff.
        """
        title_lower = title.lower()
        org_lower = organization.lower()
        
        # Check if non-teaching keyword appears
        for non_kw in NON_TEACHER_KEYWORDS:
            if non_kw in title_lower:
                return False

        # In Danuri, Worknet and general portals, we MUST verify Korean teaching relevance
        if source in ["다누리", "세종학당재단", "워크넷"]:
            has_teacher_kw = any(kw in title_lower for kw in TEACHER_MUST_HAVE_KEYWORDS)
            if not has_teacher_kw:
                return False
            if source == "워크넷":
                has_worknet_teaching = any(kw in title_lower for kw in WORKNET_TEACHING_KEYWORDS)
                if not has_worknet_teaching:
                    return False
                
        return True

    def is_expired(self, deadline: str) -> bool:
        """Check if deadline has passed."""
        if not deadline or deadline in ["상시채용", "채용시까지", "마감일 미정"]:
            return False
            
        # If deadline is in YYYY-MM-DD format
        match = re.match(r"^\d{4}-\d{2}-\d{2}$", deadline)
        if match:
            try:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d").date()
                if deadline_dt < self.today:
                    return True
            except ValueError:
                pass
        return False

    def clean_jobs(self, raw_jobs: List[Dict]) -> List[Dict]:
        """Apply full self-diagnosis cleaning pipeline to raw jobs list."""
        self.stats["raw_total"] = len(raw_jobs)
        seen_ids = set()
        seen_urls = set()
        seen_title_org = set()
        cleaned = []

        for job in raw_jobs:
            source = job.get("source", "기타")
            self.stats["by_source_raw"][source] = self.stats["by_source_raw"].get(source, 0) + 1

            title = job.get("title", "").strip()
            org = job.get("organization", "").strip()
            url = job.get("url", "").strip()
            job_id = job.get("id", "").strip()
            deadline = job.get("deadline", "").strip()

            # Rule 1: Exclude result/interview/ended notices
            if self.is_ended_or_result_notice(title):
                self.stats["removed_ended_result"] += 1
                continue

            # Rule 2: Exclude non-teacher jobs (Danuri, general staff, etc.)
            if not self.is_relevant_teacher_job(title, source, org):
                self.stats["removed_non_teacher"] += 1
                continue

            # Rule 3: Exclude expired jobs (deadline < today)
            if self.is_expired(deadline):
                self.stats["removed_expired"] += 1
                continue

            # Rule 4: Deduplication by ID, URL, and normalized (title, org)
            norm_title = re.sub(r"\s+", "", title)
            norm_org = re.sub(r"\s+", "", org)
            key_title_org = (norm_title, norm_org)

            if job_id and job_id in seen_ids:
                self.stats["removed_duplicate"] += 1
                continue
            if url and url in seen_urls:
                self.stats["removed_duplicate"] += 1
                continue
            if key_title_org in seen_title_org:
                self.stats["removed_duplicate"] += 1
                continue

            if job_id:
                seen_ids.add(job_id)
            if url:
                seen_urls.add(url)
            seen_title_org.add(key_title_org)

            # Ensure proper is_closed flag
            job["is_closed"] = False

            # Add to clean list
            cleaned.append(job)
            self.stats["by_source_clean"][source] = self.stats["by_source_clean"].get(source, 0) + 1

        self.stats["clean_total"] = len(cleaned)
        return cleaned

    def print_diagnostic_report(self):
        """Print detailed self-diagnosis and filtering statistics."""
        print("=" * 60)
        print("          데이터 품질 자체 진단(Self-Diagnosis) 리포트")
        print("=" * 60)
        print(f"기준 일자: {self.today}")
        print(f"수집된 원시 공고 총 수: {self.stats['raw_total']}건")
        print("-" * 60)
        print("노이즈 필터링 제거 내역:")
        print(f" 1) 합격자 발표 / 면접 안내 / 결과 공고 제거 : {self.stats['removed_ended_result']}건")
        print(f" 2) 한국어 교육 무관 직종(타직종) 제거      : {self.stats['removed_non_teacher']}건")
        print(f" 3) 마감일 경과(종료된 공고) 제외          : {self.stats['removed_expired']}건")
        print(f" 4) URL / ID / 중복 공고 제거              : {self.stats['removed_duplicate']}건")
        print("-" * 60)
        print(f"최종 정제 완료 유효 공고 수: {self.stats['clean_total']}건")
        print("\n[출처별 수집 및 정제 현황]")
        for src, raw_cnt in self.stats["by_source_raw"].items():
            clean_cnt = self.stats["by_source_clean"].get(src, 0)
            print(f" - {src:<12}: 원시 {raw_cnt:>3}건 -> 정제 {clean_cnt:>3}건 (유효율: {clean_cnt/raw_cnt*100:.1f}%)")
        print("=" * 60)

```

### 📄 `src/crawler.py`

```python
import json
import os
import re
import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils import (
    fetch_url,
    parse_date,
    extract_grade,
    extract_location
)
from src.cleaner import JobDataCleaner

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "jobs.json")


class KTeacherCrawler:
    """국립국어원 한국어교원 구인게시판 크롤러"""
    BASE_URL = "https://kteacher.korean.go.kr"
    LIST_URL = f"{BASE_URL}/jobsearch/list"

    def crawl(self, max_pages: int = 5) -> list[dict]:
        jobs = []
        for page in range(1, max_pages + 1):
            url = f"{self.LIST_URL}?pageNo={page}"
            html = fetch_url(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            target_table = None
            for table in soup.find_all("table"):
                if table.find("a", href=lambda h: h and "/jobsearch/" in h):
                    target_table = table
                    break

            if not target_table:
                continue

            rows = target_table.find_all("tr")[1:]  # Skip header row
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue

                category = cols[1].get_text(strip=True) if len(cols) > 1 else "국내"
                title_td = cols[2] if len(cols) > 2 else None
                if not title_td:
                    continue

                link_elem = title_td.find("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                href = link_elem.get("href", "")

                match = re.search(r"/jobsearch/(\d+)", href)
                item_id = match.group(1) if match else href

                org = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                created_raw = cols[4].get_text(strip=True) if len(cols) > 4 else ""
                deadline_raw = cols[5].get_text(strip=True) if len(cols) > 5 else ""

                created_at = parse_date(created_raw)
                deadline = parse_date(deadline_raw)

                loc_text = f"{category} {title} {org}"
                location = "해외" if "국외" in category else extract_location(loc_text, default="전국/기타")
                grade = extract_grade(title)
                detail_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

                jobs.append({
                    "id": f"kteacher_{item_id}",
                    "source": "국립국어원",
                    "title": title,
                    "organization": org,
                    "location": location,
                    "grade": grade,
                    "deadline": deadline or "상시채용",
                    "url": detail_url,
                    "is_closed": False,
                    "created_at": created_at or datetime.now().strftime("%Y-%m-%d"),
                })
        return jobs


class KLEOceanCrawler:
    """한국어교육바다 (KLE Ocean) KBoard RSS 피드 크롤러"""
    RSS_DOMESTIC = "https://kleocean.com/wp-content/plugins/kboard/rss.php?board_id=19"
    RSS_OVERSEAS = "https://kleocean.com/wp-content/plugins/kboard/rss.php?board_id=22"

    def crawl(self) -> list[dict]:
        jobs = []
        targets = [
            (self.RSS_DOMESTIC, "국내"),
            (self.RSS_OVERSEAS, "해외")
        ]

        for rss_url, default_region in targets:
            xml_text = fetch_url(rss_url)
            if not xml_text:
                continue

            try:
                root = ET.fromstring(xml_text)
            except ET.ParseError:
                continue

            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_elem = item.find("pubDate")
                desc_elem = item.find("description")

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_raw = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

                if not title or not link:
                    continue

                match = re.search(r"redirect=(\d+)", link)
                item_id = match.group(1) if match else link
                created_at = parse_date(pub_raw)

                # Comprehensive deadline extraction from title and description
                combined_text = f"{title} {desc}"
                deadline = ""

                # Pattern 1: YYYY.MM.DD ~ YYYY.MM.DD
                m1 = re.search(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})[^\d]*[~-][^\d]*(\d{4}[-./]\d{1,2}[-./]\d{1,2})", combined_text)
                if m1:
                    deadline = parse_date(m1.group(2))
                else:
                    # Pattern 2: (~\d{1,2}/\d{1,2}) e.g. (~8/10)
                    m2 = re.search(r"[~-]\s*(\d{1,2})/(\d{1,2})", title)
                    if m2 and created_at:
                        c_year = created_at[:4]
                        deadline = f"{c_year}-{int(m2.group(1)):02d}-{int(m2.group(2)):02d}"
                    else:
                        # Pattern 3: English deadline "submitted by April 15, 2026" or "deadline is November 30, 2026"
                        m3 = re.search(r"(?:deadline|submitted by|due)[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})", combined_text, re.IGNORECASE)
                        if m3:
                            deadline = parse_date(m3.group(1))
                        else:
                            # Pattern 4: "YYYY-MM-DD까지"
                            m4 = re.search(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})\s*까지", combined_text)
                            if m4:
                                deadline = parse_date(m4.group(1))

                # Extract organization from title
                org_match = re.match(r"^(\[?[^\]\s]+(?:대학교|학교|재단|센터|어학당|대학|교육원|University|School|College))", title)
                org = org_match.group(1) if org_match else "한국어 교육기관"

                # Extract location
                if default_region == "해외":
                    location = "해외"
                else:
                    loc_match = re.search(r"근무\s*지역\s*<[^>]+>\s*([^<]+)", desc)
                    if loc_match:
                        location = extract_location(loc_match.group(1), default="서울/수도권")
                    else:
                        location = extract_location(title, default="전국/기타")

                grade = extract_grade(combined_text)

                jobs.append({
                    "id": f"kleocean_{item_id}",
                    "source": "한국어교육바다",
                    "title": title,
                    "organization": org,
                    "location": location,
                    "grade": grade,
                    "deadline": deadline or "상시채용",
                    "url": link,
                    "is_closed": False,
                    "created_at": created_at or datetime.now().strftime("%Y-%m-%d"),
                })
        return jobs


class KSIFCrawler:
    """세종학당재단 채용정보 및 파견교원 게시판 크롤러"""
    BASE_URL = "https://www.ksif.or.kr"
    TEACHER_LIST_URL = f"{BASE_URL}/cop/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000001&menuNo=30101710"
    STAFF_LIST_URL = f"{BASE_URL}/cop/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000001&menuNo=30101700"

    def crawl(self) -> list[dict]:
        jobs = []
        targets = [
            (self.TEACHER_LIST_URL, "파견교원"),
            (self.STAFF_LIST_URL, "직원채용")
        ]

        for url, category in targets:
            html = fetch_url(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            board_ul = soup.find("ul", class_="board_lst")
            if not board_ul:
                continue

            items = board_ul.find_all("li")
            for li in items:
                link_elem = li.find("a")
                if not link_elem:
                    continue

                href = link_elem.get("href", "")
                p_elem = link_elem.find("p")
                if not p_elem:
                    continue

                title = p_elem.get_text(strip=True)
                clean_title = re.sub(r"^(직원|파견교원|공지|안내)\s*", "", title).strip()

                match = re.search(r"nttId=(\d+)", href)
                item_id = match.group(1) if match else href

                date_num = link_elem.find("div", class_="date_num")
                created_at = ""
                if date_num:
                    spans = date_num.find_all("span")
                    for span in spans:
                        txt = span.get_text(strip=True)
                        parsed = parse_date(txt)
                        if parsed and parsed != "상시채용":
                            created_at = parsed
                            break

                location = "해외" if category == "파견교원" or "국외" in clean_title else "서울"
                grade = extract_grade(clean_title)
                detail_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

                jobs.append({
                    "id": f"ksif_{item_id}",
                    "source": "세종학당재단",
                    "title": clean_title,
                    "organization": "세종학당재단",
                    "location": location,
                    "grade": grade,
                    "deadline": "상시채용",
                    "url": detail_url,
                    "is_closed": False,
                    "created_at": created_at or datetime.now().strftime("%Y-%m-%d"),
                })
        return jobs


class DanuriCrawler:
    """다문화가족지원포털 다누리 채용정보 크롤러"""
    BASE_URL = "https://www.liveinkorea.kr"
    LIST_URL = f"{BASE_URL}/web/lay1/bbs/S1T10C29/A/6/list.do"

    def crawl(self, max_pages: int = 5) -> list[dict]:
        jobs = []
        
        # 1. Search keyword "한국어" across pages
        for page in range(1, max_pages + 1):
            url = f"{self.LIST_URL}?keyword=%ED%95%9C%EA%B5%AD%EC%96%B4&cpage={page}&rows=10"
            html = fetch_url(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            dl_items = soup.find_all("dl", class_="tbl_list_type1")
            for dl in dl_items:
                job = self._parse_dl(dl)
                if job:
                    jobs.append(job)

        # 2. Also search all currently active (search_recruit_stat=02) announcements
        active_url = f"{self.LIST_URL}?search_recruit_stat=02&rows=20"
        active_html = fetch_url(active_url)
        if active_html:
            active_soup = BeautifulSoup(active_html, "html.parser")
            for dl in active_soup.find_all("dl", class_="tbl_list_type1"):
                job = self._parse_dl(dl)
                if job:
                    jobs.append(job)

        return jobs

    def _parse_dl(self, dl) -> dict:
        dt = dl.find("dt")
        dd = dl.find("dd")
        if not dt:
            return None

        loc_elem = dt.find("span", class_="icon_zone")
        loc_raw = loc_elem.get_text(strip=True) if loc_elem else ""

        link_elem = dt.find("a")
        if not link_elem:
            return None

        title = link_elem.get_text(strip=True)
        href = link_elem.get("href", "")

        match = re.search(r"article_seq=(\d+)", href)
        item_id = match.group(1) if match else href

        created_at = ""
        deadline = ""
        status_text = ""
        if dd:
            date_li = dd.find("ul", class_="date_search")
            if date_li:
                full_txt = date_li.get_text(" ", strip=True)
                match_period = re.search(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})\s*~\s*(\d{4}[-./]\d{1,2}[-./]\d{1,2})", full_txt)
                if match_period:
                    created_at = parse_date(match_period.group(1))
                    deadline = parse_date(match_period.group(2))
                
                stat_li = date_li.find("li", class_="icon_text_application")
                if stat_li:
                    status_text = stat_li.get_text(strip=True)

        org_match = re.search(r"([가-힣]+(?:가족센터|다문화가족지원센터|종합사회복지관|센터))", title)
        if org_match:
            org = org_match.group(1)
        elif loc_raw:
            clean_loc = loc_raw.replace("[", "").replace("]", "").strip()
            org = f"{clean_loc} 가족센터"
        else:
            org = "가족센터"

        location = extract_location(f"{loc_raw} {title}", default="전국/기타")
        grade = extract_grade(title)
        detail_url = f"{self.BASE_URL}/web/lay1/bbs/S1T10C29/A/6/{href}" if not href.startswith("http") else href

        return {
            "id": f"danuri_{item_id}",
            "source": "다누리",
            "title": title,
            "organization": org,
            "location": location,
            "grade": grade,
            "deadline": deadline or "상시채용",
            "url": detail_url,
            "is_closed": status_text == "완료",
            "created_at": created_at or datetime.now().strftime("%Y-%m-%d"),
        }


class WorknetCrawler:
    """Crawler for Worknet (고용24) job postings using session-based form search."""
    BASE_URL = "https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do"
    POST_URL = "https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchListInPost.do"
    DETAIL_URL = "https://www.work24.go.kr/wk/a/b/1500/empDetailAuthView.do?wantedAuthNo={wantedAuthNo}"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Referer": self.BASE_URL,
            "Origin": "https://www.work24.go.kr",
        })

    def crawl(self) -> list[dict]:
        jobs = []
        try:
            resp = self.session.get(self.BASE_URL, timeout=15)
            soup = BeautifulSoup(resp.content.decode("utf-8", "ignore"), "html.parser")
            mform = soup.select_one("form#mForm")
            if not mform:
                return jobs

            base_payload = {}
            for inp in mform.find_all("input"):
                name = inp.get("name")
                if name:
                    base_payload[name] = inp.get("value", "")

            keywords = ["한국어강사", "한국어교원", "한국어교사", "한국어교육", "다문화 한국어"]
            seen_ids = set()

            for kw in keywords:
                payload = base_payload.copy()
                payload["srcKeyword"] = kw
                payload["keyword"] = kw
                payload["srckeywordWantedTitle"] = "Y"
                payload["keywordWantedTitle"] = "Y"

                try:
                    post_resp = self.session.post(self.POST_URL, data=payload, timeout=15)
                    post_soup = BeautifulSoup(post_resp.content.decode("utf-8", "ignore"), "html.parser")
                    links = post_soup.select("a[href*='empDetailAuthView']")

                    for a in links:
                        href = a.get("href", "")
                        title = a.get_text(strip=True)
                        if not title:
                            continue

                        m = re.search(r"wantedAuthNo=([A-Za-z0-9]+)", href)
                        if not m:
                            continue
                        auth_no = m.group(1)
                        if auth_no in seen_ids:
                            continue
                        seen_ids.add(auth_no)

                        tr = a.find_parent("tr")
                        org = "워크넷 구인처"
                        loc_text = ""
                        deadline_str = "상시채용"
                        created_str = datetime.now().strftime("%Y-%m-%d")

                        if tr:
                            tds = tr.find_all("td")
                            if len(tds) > 0:
                                cp_tag = tds[0].select_one("a.cp_name, .cp_name, strong")
                                if cp_tag:
                                    org = cp_tag.get_text(strip=True)
                            if len(tds) > 1:
                                loc_text = tds[1].get_text(" ", strip=True)
                            if len(tds) > 2:
                                date_td_text = tds[2].get_text(" ", strip=True)
                                dl_match = re.search(r"마감일\s*:\s*(\d{4}[-./]\d{1,2}[-./]\d{1,2})", date_td_text)
                                if dl_match:
                                    deadline_str = parse_date(dl_match.group(1))
                                cr_match = re.search(r"등록일\s*:\s*(\d{4}[-./]\d{1,2}[-./]\d{1,2})", date_td_text)
                                if cr_match:
                                    created_str = parse_date(cr_match.group(1))

                        full_url = self.DETAIL_URL.format(wantedAuthNo=auth_no)
                        combined_text = f"{title} {loc_text}"
                        job = {
                            "id": f"worknet_{auth_no}",
                            "source": "워크넷",
                            "title": title,
                            "organization": org,
                            "location": extract_location(combined_text),
                            "grade": extract_grade(combined_text),
                            "deadline": deadline_str,
                            "url": full_url,
                            "is_closed": False,
                            "created_at": created_str,
                        }
                        jobs.append(job)
                except Exception as e:
                    print(f" -> [Warning] 워크넷 '{kw}' 검색 실패: {e}")
        except Exception as e:
            print(f" -> [Error] 워크넷 초기화 실패: {e}")

        return jobs


def run_pipeline() -> list[dict]:
    """Execute all crawlers, clean data, and save to jobs.json."""
    print("=" * 60)
    print("      [1/3] 한국어교원 채용 사이트 5개 수집 시작...")
    print("=" * 60)

    raw_jobs = []

    # 1. 국립국어원
    print("[1/5] 국립국어원 한국어교원 구인게시판 수집 중...")
    try:
        kteacher_jobs = KTeacherCrawler().crawl(max_pages=5)
        print(f" -> 국립국어원 수집 완료: {len(kteacher_jobs)}건")
        raw_jobs.extend(kteacher_jobs)
    except Exception as e:
        print(f" -> [Error] 국립국어원 수집 실패: {e}")

    # 2. KLE Ocean
    print("[2/5] 한국어교육바다 (KLE Ocean) RSS 피드 수집 중...")
    try:
        kle_jobs = KLEOceanCrawler().crawl()
        print(f" -> KLE Ocean 수집 완료: {len(kle_jobs)}건")
        raw_jobs.extend(kle_jobs)
    except Exception as e:
        print(f" -> [Error] KLE Ocean 수집 실패: {e}")

    # 3. 세종학당재단
    print("[3/5] 세종학당재단 채용정보 수집 중...")
    try:
        ksif_jobs = KSIFCrawler().crawl()
        print(f" -> 세종학당재단 수집 완료: {len(ksif_jobs)}건")
        raw_jobs.extend(ksif_jobs)
    except Exception as e:
        print(f" -> [Error] 세종학당재단 수집 실패: {e}")

    # 4. 다누리
    print("[4/5] 다누리(다문화가족포털) 한국어 구인공고 수집 중...")
    try:
        danuri_jobs = DanuriCrawler().crawl(max_pages=5)
        print(f" -> 다누리 수집 완료: {len(danuri_jobs)}건")
        raw_jobs.extend(danuri_jobs)
    except Exception as e:
        print(f" -> [Error] 다누리 수집 실패: {e}")

    # 5. 워크넷 (고용24)
    print("[5/5] 워크넷 (고용24) 한국어교원/강사 구인공고 수집 중...")
    try:
        worknet_jobs = WorknetCrawler().crawl()
        print(f" -> 워크넷 수집 완료: {len(worknet_jobs)}건")
        raw_jobs.extend(worknet_jobs)
    except Exception as e:
        print(f" -> [Error] 워크넷 수집 실패: {e}")

    print(f"\n총 {len(raw_jobs)}건의 원시 데이터 수집 완료.")
    print("=" * 60)
    print("      [2/3] 데이터 자체 비평 및 정제(Self-Diagnosis) 시작...")
    print("=" * 60)

    cleaner = JobDataCleaner()
    clean_jobs = cleaner.clean_jobs(raw_jobs)
    cleaner.print_diagnostic_report()

    print("=" * 60)
    print(f"      [3/3] 최종 데이터 저장 중: {OUTPUT_FILE}")
    print("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_jobs, f, ensure_ascii=False, indent=2)

    print(f"-> {len(clean_jobs)}건의 정제된 유효 공고가 성공적으로 저장되었습니다.")
    return clean_jobs


if __name__ == "__main__":
    run_pipeline()

```

### 📄 `app.py`

```python
import json
import os
from datetime import datetime, date
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="한국어교원 채용 대시보드",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern, responsive styling
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem 1.5rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white !important;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.5rem 0;
    }
    .main-header p {
        color: #e0e7ff;
        font-size: 1rem;
        margin: 0;
    }

    /* Metric cards */
    .metric-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    .metric-card {
        flex: 1;
        min-width: 140px;
        background: white;
        padding: 1.2rem;
        border-radius: 0.75rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
    }

    /* Job Card Styling */
    .job-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .job-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px -2px rgba(59, 130, 246, 0.12);
    }

    /* Badges */
    .badge-wrap {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
    }
    .badge {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        letter-spacing: -0.01em;
    }
    .badge-src-kteacher { background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .badge-src-kleocean { background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .badge-src-ksif     { background-color: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
    .badge-src-danuri   { background-color: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .badge-src-worknet  { background-color: #f0fdfa; color: #0f766e; border: 1px solid #99f6e4; }

    .badge-dday-danger { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; font-weight: 800; }
    .badge-dday-warn   { background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; font-weight: 800; }
    .badge-dday-safe   { background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; font-weight: 800; }
    .badge-dday-always { background-color: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }

    .badge-tag { background-color: #f1f5f9; color: #334155; font-size: 0.75rem; padding: 0.2rem 0.5rem; border-radius: 0.375rem; }

    .job-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.5rem;
        line-height: 1.45;
        text-decoration: none;
    }
    .job-title:hover {
        color: #2563eb;
    }
    .job-org {
        font-size: 0.9rem;
        color: #475569;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .job-meta {
        font-size: 0.8rem;
        color: #64748b;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 0.75rem;
        border-top: 1px solid #f1f5f9;
        margin-top: 0.5rem;
    }
    
    .apply-btn {
        display: inline-block;
        background-color: #2563eb;
        color: white !important;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 0.4rem 0.8rem;
        border-radius: 0.4rem;
        text-decoration: none;
        transition: background-color 0.15s;
    }
    .apply-btn:hover {
        background-color: #1d4ed8;
    }
</style>
""", unsafe_allow_html=True)

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jobs.json")

@st.cache_data(ttl=60)
def load_jobs_data():
    """Load and parse jobs data from data/jobs.json."""
    if not os.path.exists(DATA_PATH):
        return []
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return []

def get_dday_info(deadline_str, today=None):
    """Calculate D-day text, class, and integer days for sorting."""
    if today is None:
        today = datetime.now().date()
        
    if not deadline_str or deadline_str == "상시채용":
        return "상시채용", "badge-dday-always", 9999
        
    try:
        dt = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        diff = (dt - today).days
        if diff < 0:
            return "마감", "badge-dday-danger", -1
        elif diff == 0:
            return "오늘 마감 (D-Day)", "badge-dday-danger", 0
        elif diff <= 3:
            return f"D-{diff} (임박)", "badge-dday-danger", diff
        elif diff <= 7:
            return f"D-{diff}", "badge-dday-warn", diff
        else:
            return f"D-{diff}", "badge-dday-safe", diff
    except Exception:
        return "상시/미정", "badge-dday-always", 9998

def main():
    # Header Banner
    st.markdown("""
    <div class="main-header">
        <h1>📚 한국어교원 채용 대시보드</h1>
        <p>국립국어원 · KLE Ocean · 세종학당재단 · 다누리 · 워크넷 5대 포털 실시간 정제 채용 정보</p>
    </div>
    """, unsafe_allow_html=True)

    raw_jobs = load_jobs_data()
    today = datetime.now().date()

    if not raw_jobs:
        st.warning("⚠️ 등록된 채용 공고가 없습니다. 크롤러를 실행하여 데이터를 수집해 주세요.")
        if st.button("🔄 크롤러 수동 실행"):
            with st.spinner("4대 사이트 공고를 수집 및 정제 중입니다..."):
                from src.crawler import run_pipeline
                run_pipeline()
                st.cache_data.clear()
                st.rerun()
        return

    # Pre-process jobs for filtering and sorting
    processed_jobs = []
    for job in raw_jobs:
        dday_label, dday_class, dday_days = get_dday_info(job.get("deadline", ""), today)
        processed_jobs.append({
            **job,
            "dday_label": dday_label,
            "dday_class": dday_class,
            "dday_days": dday_days,
        })

    # Sidebar Filters
    st.sidebar.header("🔍 검색 및 상세 필터")

    # Keyword Search
    keyword = st.sidebar.text_input("공고명 / 기관명 검색", placeholder="예: 대학, 강사, 세종, 베트남...")

    # Source Filter
    all_sources = ["전체"] + sorted(list(set(j["source"] for j in processed_jobs)))
    selected_source = st.sidebar.selectbox("채용 출처", all_sources)

    # Location Filter
    all_locations = ["전체"] + sorted(list(set(j.get("location", "전국/기타") for j in processed_jobs)))
    selected_location = st.sidebar.selectbox("근무 지역", all_locations)

    # Grade Filter
    all_grades = ["전체", "1급", "2급", "3급", "자격소지자", "무관/미지정"]
    selected_grade = st.sidebar.selectbox("교원 자격 등급", all_grades)

    # Status Filter
    status_options = ["전체", "접수중 (마감 공고 제외)", "마감임박순 (D-7 이내)"]
    selected_status = st.sidebar.radio("접수 상태", status_options, index=1)

    # Sorting
    sort_option = st.sidebar.selectbox("정렬 기준", ["마감일 빠른순", "최근 등록순", "기관명 가나다순"])

    # Apply Filters
    filtered_jobs = processed_jobs

    if keyword:
        kw_lower = keyword.lower()
        filtered_jobs = [
            j for j in filtered_jobs
            if kw_lower in j.get("title", "").lower() or kw_lower in j.get("organization", "").lower()
        ]

    if selected_source != "전체":
        filtered_jobs = [j for j in filtered_jobs if j.get("source") == selected_source]

    if selected_location != "전체":
        filtered_jobs = [j for j in filtered_jobs if j.get("location") == selected_location]

    if selected_grade != "전체":
        filtered_jobs = [j for j in filtered_jobs if selected_grade in j.get("grade", "")]

    if selected_status == "접수중 (마감 공고 제외)":
        filtered_jobs = [j for j in filtered_jobs if j["dday_days"] >= 0]
    elif selected_status == "마감임박순 (D-7 이내)":
        filtered_jobs = [j for j in filtered_jobs if 0 <= j["dday_days"] <= 7]

    # Apply Sorting
    if sort_option == "마감일 빠른순":
        filtered_jobs.sort(key=lambda x: x["dday_days"])
    elif sort_option == "최근 등록순":
        filtered_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_option == "기관명 가나다순":
        filtered_jobs.sort(key=lambda x: x.get("organization", ""))

    # Top KPI Metrics Cards
    total_valid = len([j for j in processed_jobs if j["dday_days"] >= 0])
    urgent_count = len([j for j in processed_jobs if 0 <= j["dday_days"] <= 7])
    overseas_count = len([j for j in processed_jobs if j.get("location") == "해외"])
    filtered_count = len(filtered_jobs)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #2563eb;">{total_valid}</div>
            <div class="metric-label">접수중인 전체 공고</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #dc2626;">{urgent_count}</div>
            <div class="metric-label">마감 임박 (D-7 이내)</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #059669;">{overseas_count}</div>
            <div class="metric-label">해외 파견 / 취업</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #7c3aed;">{filtered_count}</div>
            <div class="metric-label">필터 조회 결과</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # View Mode Toggle & Actions
    view_col1, view_col2 = st.columns([8, 2])
    with view_col1:
        view_mode = st.radio("뷰 모드 선택", ["🗂️ 카드 뷰 (모바일/PC 추천)", "📋 테이블 뷰 (전체 목록)"], horizontal=True)
    with view_col2:
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if not filtered_jobs:
        st.info("💡 조건에 맞는 공고가 없습니다. 사이드바 필터를 변경해 보세요.")
        return

    # Source Badge Class Mapping
    src_class_map = {
        "국립국어원": "badge-src-kteacher",
        "한국어교육바다": "badge-src-kleocean",
        "세종학당재단": "badge-src-ksif",
        "다누리": "badge-src-danuri",
        "워크넷": "badge-src-worknet",
    }

    # 1. Card View
    if "카드" in view_mode:
        # Responsive 2-column grid layout
        cols = st.columns(2)
        for idx, job in enumerate(filtered_jobs):
            target_col = cols[idx % 2]
            with target_col:
                src = job.get("source", "기타")
                src_cls = src_class_map.get(src, "badge-src-kteacher")
                title = job.get("title", "")
                org = job.get("organization", "미기재")
                loc = job.get("location", "전국/기타")
                grade = job.get("grade", "무관/미지정")
                dl = job.get("deadline", "상시채용")
                created = job.get("created_at", "-")
                url = job.get("url", "#")
                dday_label = job["dday_label"]
                dday_cls = job["dday_class"]

                st.markdown(f"""
                <div class="job-card">
                    <div>
                        <div class="badge-wrap">
                            <span class="badge {src_cls}">{src}</span>
                            <span class="badge {dday_cls}">{dday_label}</span>
                            <span class="badge badge-tag">📍 {loc}</span>
                            <span class="badge badge-tag">🎓 {grade}</span>
                        </div>
                        <a href="{url}" target="_blank" class="job-title">{title}</a>
                        <div class="job-org">🏢 {org}</div>
                    </div>
                    <div class="job-meta">
                        <div>
                            <span>접수마감: <b>{dl}</b></span> &nbsp;·&nbsp;
                            <span>등록일: {created}</span>
                        </div>
                        <a href="{url}" target="_blank" class="apply-btn">공고 원문 ↗</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 2. Table View
    else:
        df_display = pd.DataFrame([
            {
                "출처": j.get("source"),
                "D-Day": j["dday_label"],
                "채용공고명": j.get("title"),
                "기관명": j.get("organization"),
                "지역": j.get("location"),
                "자격요건": j.get("grade"),
                "접수마감일": j.get("deadline"),
                "등록일": j.get("created_at"),
                "원문링크": j.get("url"),
            }
            for j in filtered_jobs
        ])

        st.dataframe(
            df_display,
            use_container_width=True,
            column_config={
                "원문링크": st.column_config.LinkColumn("원문 바로가기", display_text="상세보기 ↗"),
                "D-Day": st.column_config.TextColumn("D-Day", width="small"),
                "출처": st.column_config.TextColumn("출처", width="small"),
                "지역": st.column_config.TextColumn("지역", width="small"),
                "자격요건": st.column_config.TextColumn("자격요건", width="small"),
            },
            hide_index=True,
            height=600
        )

        # CSV Download Button
        csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 필터링된 공고 CSV 다운로드",
            data=csv_data,
            file_name=f"korean_teacher_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    # Footer
    st.markdown("---")
    st.caption("🤖 한국어교원 채용 대시보드 | 국립국어원 · 한국어교육바다 · 세종학당재단 · 다누리 · 워크넷 5대 포털 데이터 실시간 연동")

if __name__ == "__main__":
    main()

```

### 📄 `tests/test_pipeline.py`

```python
import json
import os
import unittest
from datetime import datetime
from src.utils import calculate_dday, extract_grade, extract_location, parse_date
from src.cleaner import JobDataCleaner

class TestPipeline(unittest.TestCase):
    def test_utils_grade_extraction(self):
        self.assertEqual(extract_grade("한국어교원 2급 이상 채용"), "2급")
        self.assertEqual(extract_grade("한국어 교원 1급 자격증 필수"), "1급")
        self.assertEqual(extract_grade("3급 교원 자격증 소지자"), "3급")
        self.assertEqual(extract_grade("한국어교원자격증 소지자 모집"), "자격소지자")
        self.assertEqual(extract_grade("다문화센터 프로그램 안내"), "무관/미지정")

    def test_utils_location_extraction(self):
        self.assertEqual(extract_location("서울 마포구 한국어학당"), "서울")
        self.assertEqual(extract_location("수원시 다문화가족지원센터"), "경기")
        self.assertEqual(extract_location("부산외국어대학교 한국어교육원"), "경남/부산/울산")
        self.assertEqual(extract_location("베트남 하노이 세종학당 교원 채용"), "해외")
        self.assertEqual(extract_location("기타 지역"), "전국/기타")

    def test_utils_date_and_dday(self):
        parsed = parse_date("2026.09.30")
        self.assertEqual(parsed, "2026-09-30")
        parsed2 = parse_date("2026년 10월 15일")
        self.assertEqual(parsed2, "2026-10-15")
        
        # Test D-day calculation
        label, days, is_closed = calculate_dday("상시채용")
        self.assertEqual(label, "상시")
        self.assertFalse(is_closed)

    def test_cleaner_noise_filtering(self):
        cleaner = JobDataCleaner()
        # Non-job items (results/interviews)
        self.assertTrue(cleaner.is_ended_or_result_notice("2026년도 제1차 면접심사 결과 공고 및 합격자 안내"))
        self.assertTrue(cleaner.is_ended_or_result_notice("서류전형 합격자 및 면접일정 공지"))
        self.assertTrue(cleaner.is_ended_or_result_notice("최종합격자 안내문"))
        
        # Valid teacher job items
        self.assertFalse(cleaner.is_ended_or_result_notice("[채용] 2026학년도 가을학기 한국어교원 모집 공고"))
        self.assertFalse(cleaner.is_ended_or_result_notice("한국어교육 강사 채용 공고"))

        # Irrelevant non-teacher jobs in multicultural centers
        self.assertFalse(cleaner.is_relevant_teacher_job("다문화가족지원센터 아이돌봄전담인력 채용 공고", "다누리"))
        self.assertFalse(cleaner.is_relevant_teacher_job("다문화센터 조리원 채용", "다누리"))
        self.assertTrue(cleaner.is_relevant_teacher_job("다문화가족지원센터 한국어집합교육 강사 채용", "다누리"))

    def test_jobs_json_schema(self):
        jobs_file = os.path.join(os.path.dirname(__file__), "..", "data", "jobs.json")
        self.assertTrue(os.path.exists(jobs_file), "data/jobs.json must exist")
        
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
            
        self.assertIsInstance(jobs, list)
        self.assertGreater(len(jobs), 0, "jobs.json should not be empty")

        required_keys = {
            "id", "source", "title", "organization", "location",
            "grade", "deadline", "url", "is_closed", "created_at"
        }

        for job in jobs:
            self.assertTrue(required_keys.issubset(job.keys()), f"Missing keys in {job}")
            self.assertTrue(job["title"].strip(), "Title must not be blank")
            self.assertTrue(job["url"].startswith("http"), f"Invalid url: {job['url']}")
            self.assertIn(job["source"], ["국립국어원", "한국어교육바다", "세종학당재단", "다누리", "워크넷"])

if __name__ == "__main__":
    unittest.main()

```

### 📄 `README.md`

```md
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
│   └── jobs.json                # 정제된 최신 채용 공고 데이터셋
├── src/
│   ├── __init__.py
│   ├── crawler.py               # 5개 사이트 모듈식 수집기 및 파이프라인 총괄
│   ├── cleaner.py               # 결과 공지/비관련 직종/만료일자 정제 및 검증 모듈
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

```
