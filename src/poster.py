import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from Crypto.Cipher import AES
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

WP_URL = os.getenv("WP_URL", "https://korean-teacher.infinityfreeapp.com").rstrip("/")
SECRET_KEY = os.getenv("KBOARD_SECRET_KEY", "korean_secret_key_2026")
BOARD_ID = int(os.getenv("KBOARD_BOARD_ID", "1"))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_kboard.json")


def solve_infinityfree_challenge(session: requests.Session, url: str) -> bool:
    """
    Decrypt InfinityFree's slowAES bot barrier challenge using pycryptodome (AES-128-CBC)
    and set the resulting __test cookie into the requests session.
    """
    try:
        resp = session.get(url, timeout=15)
        if "__test" in session.cookies:
            return True

        text = resp.text
        if "slowAES" not in text:
            return False

        a_match = re.search(r'a=toNumbers\("([a-f0-9]+)"\)', text)
        b_match = re.search(r'b=toNumbers\("([a-f0-9]+)"\)', text)
        c_match = re.search(r'c=toNumbers\("([a-f0-9]+)"\)', text)

        if not (a_match and b_match and c_match):
            return False

        key = bytes.fromhex(a_match.group(1))
        iv = bytes.fromhex(b_match.group(1))
        ciphertext = bytes.fromhex(c_match.group(1))

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        test_cookie = decrypted.hex()

        domain = WP_URL.replace("https://", "").replace("http://", "").split("/")[0]
        session.cookies.set("__test", test_cookie, domain=domain, path="/")
        return True
    except Exception as e:
        print(f"[Warning] InfinityFree challenge bypass error: {e}")
        return False


def post_job_opening(title: str, content: str, board_id: int = BOARD_ID) -> Optional[Dict[str, Any]]:
    """
    Post a job opening to WordPress KBoard via post_bridge.php.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        )
    })

    bridge_url = f"{WP_URL}/post_bridge.php"
    solve_infinityfree_challenge(session, bridge_url)

    payload = {
        "key": SECRET_KEY,
        "board_id": board_id,
        "title": title,
        "content": content
    }

    try:
        response = session.post(bridge_url, data=payload, timeout=20)
        if "slowAES" in response.text:
            solve_infinityfree_challenge(session, bridge_url)
            response = session.post(bridge_url, data=payload, timeout=20)

        result = response.json()
        return result
    except Exception as e:
        print(f"[전송 오류]: {e}")
        return None


def calculate_job_dday(deadline_str: str) -> tuple[str, str]:
    """Calculate D-day text and CSS style for badge."""
    if not deadline_str or deadline_str == "상시채용":
        return "상시채용", "background-color: #f8fafc; color: #475569; border: 1px solid #e2e8f0; font-weight: 700;"
    try:
        dt = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        diff = (dt - today).days
        if diff < 0:
            return "마감", "background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; font-weight: 800;"
        elif diff == 0:
            return "오늘마감 (D-Day)", "background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; font-weight: 800;"
        elif diff <= 3:
            return f"D-{diff} (임박)", "background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; font-weight: 800;"
        elif diff <= 7:
            return f"D-{diff}", "background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; font-weight: 800;"
        else:
            return f"D-{diff}", "background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; font-weight: 800;"
    except Exception:
        return "상시채용", "background-color: #f8fafc; color: #475569; border: 1px solid #e2e8f0; font-weight: 700;"


def format_deadline_tag(deadline_str: Optional[str]) -> str:
    """
    Format deadline tag for KBoard title.
    Examples:
      '2026-08-31' -> '[마감 26-08-31]'
      '상시채용'    -> '[상시채용]'
    """
    if not deadline_str or deadline_str in ("상시채용", "상시"):
        return "[상시채용]"

    val = str(deadline_str).strip()
    m_full = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", val)
    if m_full:
        year, month, day = m_full.groups()
        return f"[마감 {year[-2:]}-{month}-{day}]"

    m_short = re.match(r"^(\d{2})-(\d{2})-(\d{2})$", val)
    if m_short:
        return f"[마감 {val}]"

    return f"[마감 {val}]"


def format_kboard_title(job: Dict[str, Any]) -> str:
    """
    Format job title for KBoard.
    Prepends deadline tag: [마감 YY-MM-DD] 제목 or [상시채용] 제목.
    """
    title = job.get("title", "").strip()
    # Strip any leading source tag brackets or previous deadline tags to avoid duplication
    title = re.sub(
        r"^\[\s*(?:한국어교육바다|국립국어원|다누리|세종학당재단|워크넷|기타|마감|상시채용)[^\]]*\]\s*",
        "",
        title
    )
    deadline = job.get("deadline", "상시채용")
    tag = format_deadline_tag(deadline)

    return f"{tag} {title}".strip()


def format_job_html(job: Dict[str, Any]) -> str:
    """
    Format job details into a high-visibility, responsive HTML card matching the admin design.
    Minified without blank newlines to prevent WordPress wpautop from inserting excess <br/> tags.
    Does not include dynamic D-Day calculation as forum posts are static.
    """
    source = job.get("source", "기타")
    title = job.get("title", "")
    org = job.get("organization", "미기재")
    location = job.get("location", "전국/기타")
    grade = job.get("grade", "무관/미지정")
    deadline = job.get("deadline", "상시채용")
    created_at = job.get("created_at", "-")
    url = job.get("url", "#")

    # Source Badge Styles
    src_styles = {
        "국립국어원": "background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;",
        "한국어교육바다": "background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0;",
        "세종학당재단": "background-color: #fff7ed; color: #c2410c; border: 1px solid #fed7aa;",
        "다누리": "background-color: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff;",
        "워크넷": "background-color: #f0fdfa; color: #0f766e; border: 1px solid #99f6e4;",
    }
    src_style = src_styles.get(source, "background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;")

    # High-visibility card matching user screenshot (without dynamic D-Day)
    html = (
        f'<div class="job-card-wrapper" style="font-family: Pretendard, -apple-system, BlinkMacSystemFont, Malgun Gothic, sans-serif; line-height: 1.6; color: #1e293b; max-width: 700px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 14px; background-color: #ffffff; box-shadow: 0 4px 12px -2px rgba(0,0,0,0.05);">'
        # Top 3 Badges (Source, Location, Grade)
        f'<div class="badge-wrap" style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;">'
        f'<span class="badge" style="padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 700; {src_style}">{source}</span>'
        f'<span class="badge" style="padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; background-color: #f1f5f9; color: #334155; border: 1px solid #e2e8f0;">📍 {location}</span>'
        f'<span class="badge" style="padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; background-color: #f1f5f9; color: #334155; border: 1px solid #e2e8f0;">🎓 자격: {grade}</span>'
        f'</div>'
        # Large Bold Title
        f'<div class="card-title" style="font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 12px 0; line-height: 1.45;">{title}</div>'
        # Icon Meta Row
        f'<div class="card-meta" style="font-size: 0.9rem; color: #475569; display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid #f1f5f9;">'
        f'<span>🏢 <b>{org}</b></span>'
        f'<span>⏰ 마감: <b style="color: #dc2626;">{deadline}</b></span>'
        f'<span>🗓️ 수집일: {created_at}</span>'
        f'</div>'
        # Specifications Table
        f'<table class="job-spec-table" style="width: 100%; border-collapse: collapse; margin-bottom: 22px; font-size: 14px;">'
        f'<tbody>'
        f'<tr style="border-bottom: 1px solid #f1f5f9;"><td class="label" style="padding: 10px 8px; width: 110px; color: #64748b; font-weight: 700;">채용 기관</td><td class="val" style="padding: 10px 8px; color: #0f172a; font-weight: 700;">{org}</td></tr>'
        f'<tr style="border-bottom: 1px solid #f1f5f9;"><td class="label" style="padding: 10px 8px; color: #64748b; font-weight: 700;">근무 지역</td><td class="val" style="padding: 10px 8px; color: #0f172a;">{location}</td></tr>'
        f'<tr style="border-bottom: 1px solid #f1f5f9;"><td class="label" style="padding: 10px 8px; color: #64748b; font-weight: 700;">자격 등급</td><td class="val" style="padding: 10px 8px; color: #0f172a;">{grade}</td></tr>'
        f'<tr style="border-bottom: 1px solid #f1f5f9;"><td class="label" style="padding: 10px 8px; color: #64748b; font-weight: 700;">접수 마감일</td><td class="val danger" style="padding: 10px 8px; color: #dc2626; font-weight: 800;">{deadline}</td></tr>'
        f'<tr><td class="label" style="padding: 10px 8px; color: #64748b; font-weight: 700;">공고 등록일</td><td class="val" style="padding: 10px 8px; color: #64748b;">{created_at}</td></tr>'
        f'</tbody>'
        f'</table>'
        # Prominent CTA Button (unquoted url so magic_quotes never breaks it)
        f'<div class="job-cta-wrap" style="text-align: center; margin: 24px 0 10px 0;">'
        f'<a href={url} target=_blank rel=noopener class="job-apply-btn" style="display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 13px 34px; border-radius: 8px; font-weight: 800; text-decoration: none; font-size: 15px; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);">공고 원문 보러가기 ↗</a>'
        f'</div>'
        f'<div class="job-footer" style="border-top: 1px solid #f1f5f9; padding-top: 14px; text-align: center; font-size: 12px; color: #94a3b8;">'
        f'본 채용 정보는 한국어교원 채용 통합 대시보드 자동 수집 시스템을 통해 제공됩니다.'
        f'</div>'
        f'</div>'
    )
    return html



JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")


def load_jobs_file() -> List[Dict[str, Any]]:
    """Load jobs data from jobs.json."""
    if not os.path.exists(JOBS_FILE):
        return []
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Warning] Failed to load jobs file: {e}")
        return []


def save_jobs_file(jobs: List[Dict[str, Any]]):
    """Save jobs data to jobs.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Warning] Failed to save jobs file: {e}")


def load_published_records() -> Dict[str, Any]:
    """Load history of previously published jobs to prevent duplicates."""
    if not os.path.exists(PUBLISHED_FILE):
        return {}
    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_published_records(records: Dict[str, Any]):
    """Save history of published jobs."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Warning] Failed to save published records: {e}")


# Alias for backward compatibility
format_kboard_content = format_job_html


def approve_and_publish_job(
    job_id: str,
    custom_title: Optional[str] = None,
    custom_org: Optional[str] = None,
    custom_deadline: Optional[str] = None,
    custom_location: Optional[str] = None,
    custom_grade: Optional[str] = None
) -> Dict[str, Any]:
    """
    Operator approves a pending job. Applies any edits made by the operator,
    posts the job to WordPress KBoard, and updates the job's status to 'published'.
    """
    jobs = load_jobs_file()
    job = None
    job_idx = -1
    for i, j in enumerate(jobs):
        if str(j.get("id")) == str(job_id):
            job = j
            job_idx = i
            break

    if not job:
        return {"status": "error", "message": f"공고 ID '{job_id}'를 찾을 수 없습니다."}

    # If already published, return existing status
    if job.get("status") == "published" and job.get("kboard_uid"):
        return {
            "status": "already_published",
            "kboard_uid": job.get("kboard_uid"),
            "message": "이미 KBoard에 게시된 공고입니다."
        }

    # Apply operator overrides if provided
    if custom_title is not None and custom_title.strip():
        job["title"] = custom_title.strip()
    if custom_org is not None and custom_org.strip():
        job["organization"] = custom_org.strip()
    if custom_deadline is not None and custom_deadline.strip():
        job["deadline"] = custom_deadline.strip()
    if custom_location is not None and custom_location.strip():
        job["location"] = custom_location.strip()
    if custom_grade is not None and custom_grade.strip():
        job["grade"] = custom_grade.strip()

    title = job.get("title", "")
    content = format_job_html(job)
    kboard_title = format_kboard_title(job)

    # Post to WordPress KBoard
    res = post_job_opening(title=kboard_title, content=content, board_id=BOARD_ID)

    if res and res.get("status") == "success":
        uid = res.get("kboard_uid") or res.get("post_id")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        job["status"] = "published"
        job["kboard_uid"] = uid
        job["reviewed_at"] = now_str
        jobs[job_idx] = job
        save_jobs_file(jobs)

        # Update published_kboard.json
        pub_records = load_published_records()
        pub_records[str(job_id)] = {
            "kboard_uid": uid,
            "title": title,
            "source": job.get("source"),
            "published_at": now_str
        }
        save_published_records(pub_records)

        return {
            "status": "success",
            "kboard_uid": uid,
            "message": f"KBoard에 성공적으로 게시되었습니다. (UID: {uid})"
        }
    else:
        err_msg = res.get("message", "전송 실패") if res else "서버 응답 없음"
        return {
            "status": "error",
            "message": f"KBoard 전송 실패: {err_msg}"
        }


def reject_job(job_id: str) -> bool:
    """
    Operator rejects/excludes a job. Updates status to 'rejected'.
    """
    jobs = load_jobs_file()
    updated = False
    for job in jobs:
        if str(job.get("id")) == str(job_id):
            job["status"] = "rejected"
            job["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated = True
            break
    if updated:
        save_jobs_file(jobs)
    return updated


def restore_to_pending(job_id: str) -> bool:
    """
    Restore a rejected or published job back to 'pending' review state.
    """
    jobs = load_jobs_file()
    updated = False
    for job in jobs:
        if str(job.get("id")) == str(job_id):
            job["status"] = "pending"
            job["reviewed_at"] = None
            updated = True
            break
    if updated:
        save_jobs_file(jobs)
    return updated


def batch_approve_jobs(job_ids: List[str], delay_sec: float = 0.5) -> Dict[str, Any]:
    """
    Batch approve and publish multiple jobs to KBoard.
    """
    stats = {
        "total": len(job_ids),
        "published": 0,
        "failed": 0,
        "already_published": 0,
        "details": []
    }
    for idx, jid in enumerate(job_ids):
        res = approve_and_publish_job(jid)
        st_code = res.get("status")
        if st_code == "success":
            stats["published"] += 1
        elif st_code == "already_published":
            stats["already_published"] += 1
        else:
            stats["failed"] += 1
        stats["details"].append({"id": jid, "result": res})

        if idx < len(job_ids) - 1 and delay_sec > 0:
            time.sleep(delay_sec)
    return stats


def sync_jobs_to_kboard(jobs: List[Dict[str, Any]], limit: Optional[int] = None, delay_sec: float = 1.0) -> Dict[str, int]:
    """
    Iterate over crawled & cleaned jobs and post new openings to KBoard.
    Skips already published jobs (deduplication).
    """
    published_records = load_published_records()
    stats = {
        "total": len(jobs),
        "skipped": 0,
        "published": 0,
        "failed": 0
    }

    # Filter out already published jobs
    unposted_jobs = [j for j in jobs if str(j.get("id")) not in published_records]
    stats["skipped"] = len(jobs) - len(unposted_jobs)

    if limit:
        unposted_jobs = unposted_jobs[:limit]

    print(f"\n[KBoard 자동 전송 파이프라인] 전체 {len(jobs)}건 중 신규 전송 대상: {len(unposted_jobs)}건 (기존 등록 {stats['skipped']}건 스킵)")

    for idx, job in enumerate(unposted_jobs, 1):
        job_id = str(job.get("id"))
        title = job.get("title", "")
        kboard_title = format_kboard_title(job)
        html_content = format_job_html(job)

        print(f" -> [{idx}/{len(unposted_jobs)}] 전송 중: {kboard_title[:35]}...")
        result = post_job_opening(title=kboard_title, content=html_content, board_id=BOARD_ID)

        if result and result.get("status") == "success":
            uid = result.get("kboard_uid") or result.get("post_id")
            stats["published"] += 1
            published_records[job_id] = {
                "kboard_uid": uid,
                "title": title,
                "source": job.get("source"),
                "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_published_records(published_records)
            print(f"    [OK] 성공 (KBoard UID: {uid})")
        else:
            stats["failed"] += 1
            print(f"    [FAIL] 전송 실패")

        if idx < len(unposted_jobs) and delay_sec > 0:
            time.sleep(delay_sec)

    return stats


if __name__ == "__main__":
    jobs_file = os.path.join(DATA_DIR, "jobs.json")
    if os.path.exists(jobs_file):
        with open(jobs_file, "r", encoding="utf-8") as f:
            clean_jobs = json.load(f)
        sync_jobs_to_kboard(clean_jobs, limit=1)

