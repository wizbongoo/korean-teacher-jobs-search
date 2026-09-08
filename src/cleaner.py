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
    "상담사", "상담전문"
]

TEACHER_MUST_HAVE_KEYWORDS = [
    "한국어", "한국학", "korean", "언어발달", "다문화언어", "토픽", "topik", "교원", "강사", "교수"
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
        Crucial for general boards like Danuri or KSIF general staff.
        """
        title_lower = title.lower()
        org_lower = organization.lower()
        
        # Check if non-teaching keyword appears without teacher qualification
        for non_kw in NON_TEACHER_KEYWORDS:
            if non_kw in title_lower and "한국어" not in title_lower:
                return False

        # In Danuri and general portals, we MUST verify Korean teaching relevance
        if source in ["다누리", "세종학당재단"]:
            has_teacher_kw = any(kw in title_lower for kw in TEACHER_MUST_HAVE_KEYWORDS)
            if not has_teacher_kw:
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
