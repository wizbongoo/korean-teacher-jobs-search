import re
from datetime import datetime, date
from typing import List, Dict, Tuple

EXCLUDE_TITLE_KEYWORDS = [
    "합격자", "최종합격", "최종 합격", "합격 공고", "합격공고", "서류전형 결과", "서류 합격",
    "면접 심사", "면접 대상자", "면접 안내", "면접 공지", "면접 일정", "면접심사", "면접안내",
    "선발 결과", "채용 결과", "결과 공고", "결과공고", "결과 안내", "결과안내",
    "결정 공고", "결정공고", "서류심사 결과", "서류심사결과", "서류심사 합격", "서류심사 안내", "서류심사",
    "심사 안내", "심사안내",
    "[마감]", "(마감)", "접수마감", "마감완료",
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

    def is_expired(self, deadline: str, title: str = "", created_at: str = "") -> bool:
        """
        Check if deadline has passed or if the notice is outdated/stale.
        Handles:
        1. Explicit YYYY-MM-DD deadline < today
        2. Deadline dates extracted from title (e.g. ~1.19, ~8.13, ~01/09, ~1월 19일)
        3. Past years in title (e.g. 2025년, 2024년 when today is 2026)
        4. Past semester/period in title (e.g. 2026년 봄학기, 26년3월~7월 when today is in second half of the year)
        5. Stale "상시채용" or unstated deadline created > 90 days ago
        """
        # 1. Explicit deadline check (YYYY-MM-DD or YYYY.MM.DD)
        if deadline and deadline not in ["상시채용", "채용시까지", "마감일 미정"]:
            match = re.match(r"^(\d{4})[-./](\d{1,2})[-./](\d{1,2})", deadline)
            if match:
                try:
                    d_val = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                    if d_val < self.today:
                        return True
                except ValueError:
                    pass

        # 2. Extract deadline and period from title if present
        if title:
            # Check past year mention in title (e.g., 2025년, 2024년, 2025학년도)
            current_year = self.today.year
            past_year_match = re.search(r"\b(20[12]\d)년", title)
            if past_year_match:
                title_year = int(past_year_match.group(1))
                if title_year < current_year:
                    return True

            # Check title date formats: (~1.19), (~8/13), (~2026.01.09)
            m_date = re.search(r"[~-]\s*(?:(\d{4})[-./])?(\d{1,2})[-./](\d{1,2})", title)
            if m_date:
                try:
                    y = int(m_date.group(1)) if m_date.group(1) else (int(created_at[:4]) if created_at and len(created_at) >= 4 else current_year)
                    m = int(m_date.group(2))
                    d = int(m_date.group(3))
                    dt = date(y, m, d)
                    if dt < self.today:
                        return True
                except ValueError:
                    pass

            # Check Korean date format in title: (~1월 19일)
            m_ko = re.search(r"[~-]\s*(\d{1,2})월\s*(\d{1,2})일", title)
            if m_ko:
                try:
                    y = int(created_at[:4]) if created_at and len(created_at) >= 4 else current_year
                    m = int(m_ko.group(1))
                    d = int(m_ko.group(2))
                    dt = date(y, m, d)
                    if dt < self.today:
                        return True
                except ValueError:
                    pass

            # Check past semester/period if we are in 2nd semester (month >= 8)
            if self.today.month >= 8:
                if re.search(r"(봄\s*학기|1학기|상반기|3월\s*~\s*7월|3월\s*~\s*6월)", title):
                    return True

        # 3. Check stale "상시채용" or unstated deadline created > 90 days ago
        if created_at and (not deadline or deadline in ["상시채용", "채용시까지", "마감일 미정"]):
            c_match = re.match(r"^(\d{4})[-./](\d{1,2})[-./](\d{1,2})", created_at)
            if c_match:
                try:
                    c_date = date(int(c_match.group(1)), int(c_match.group(2)), int(c_match.group(3)))
                    if (self.today - c_date).days > 90:
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
            created_at = job.get("created_at", "").strip()

            # Rule 1: Exclude result/interview/ended notices
            if self.is_ended_or_result_notice(title):
                self.stats["removed_ended_result"] += 1
                continue

            # Rule 2: Exclude non-teacher jobs (Danuri, general staff, etc.)
            if not self.is_relevant_teacher_job(title, source, org):
                self.stats["removed_non_teacher"] += 1
                continue

            # Rule 3: Exclude expired jobs (deadline < today, past dates in title, stale 90+ days)
            if self.is_expired(deadline, title=title, created_at=created_at):
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
