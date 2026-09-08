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
