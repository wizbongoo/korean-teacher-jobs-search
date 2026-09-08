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
    Direct function to post a single job to KBoard via post_bridge.php.
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


def format_kboard_content(job: Dict[str, Any]) -> str:
    """
    Format job details into a modern, responsive HTML card for KBoard post content.
    """
    source = job.get("source", "기타")
    org = job.get("organization", "미기재")
    location = job.get("location", "전국/기타")
    grade = job.get("grade", "무관/미지정")
    deadline = job.get("deadline", "상시채용")
    created_at = job.get("created_at", "-")
    url = job.get("url", "#")

    html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333333; max-width: 680px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px; background-color: #ffffff;">
    <div style="margin-bottom: 15px; display: flex; gap: 8px; flex-wrap: wrap;">
        <span style="background-color: #eff6ff; color: #1d4ed8; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; border: 1px solid #bfdbfe;">{source}</span>
        <span style="background-color: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold;">📍 {location}</span>
        <span style="background-color: #fef3c7; color: #b45309; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold;">🎓 자격: {grade}</span>
    </div>

    <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px;">
        <tbody>
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 10px 8px; width: 100px; color: #64748b; font-weight: bold;">채용 기관</td>
                <td style="padding: 10px 8px; color: #0f172a; font-weight: bold;">{org}</td>
            </tr>
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 10px 8px; color: #64748b; font-weight: bold;">근무 지역</td>
                <td style="padding: 10px 8px; color: #0f172a;">{location}</td>
            </tr>
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 10px 8px; color: #64748b; font-weight: bold;">자격 등급</td>
                <td style="padding: 10px 8px; color: #0f172a;">{grade}</td>
            </tr>
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 10px 8px; color: #64748b; font-weight: bold;">접수 마감일</td>
                <td style="padding: 10px 8px; color: #dc2626; font-weight: bold;">{deadline}</td>
            </tr>
            <tr>
                <td style="padding: 10px 8px; color: #64748b; font-weight: bold;">공고 등록일</td>
                <td style="padding: 10px 8px; color: #64748b;">{created_at}</td>
            </tr>
        </tbody>
    </table>

    <div style="text-align: center; margin: 25px 0 15px 0;">
        <a href="{url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 28px; border-radius: 6px; font-weight: bold; text-decoration: none; font-size: 15px; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);">공고 원문 보러가기 ↗</a>
    </div>

    <div style="border-top: 1px solid #f1f5f9; padding-top: 15px; text-align: center; font-size: 12px; color: #94a3b8;">
        본 채용 정보는 한국어교원 채용 통합 대시보드 자동 수집 시스템을 통해 제공됩니다.
    </div>
</div>"""
    return html


class WordPressPublisher:
    """
    Manages publishing cleaned job openings to WordPress KBoard.
    Tracks published history to prevent duplicate postings.
    """
    def __init__(self, bridge_url: str = None, secret_key: str = None, board_id: int = BOARD_ID):
        self.bridge_url = bridge_url or f"{WP_URL}/post_bridge.php"
        self.secret_key = secret_key or SECRET_KEY
        self.board_id = board_id
        self.published_records = self._load_published_records()

    def _load_published_records(self) -> Dict[str, Any]:
        """Load history of previously published jobs to avoid duplicates."""
        if not os.path.exists(PUBLISHED_FILE):
            return {}
        try:
            with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_published_records(self):
        """Save history of published jobs."""
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
                json.dump(self.published_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Warning] Failed to save published records: {e}")

    def is_published(self, job_id: str) -> bool:
        """Check if a job has already been published to KBoard."""
        return str(job_id) in self.published_records

    def publish_single_job(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Publish a single job to KBoard and record its post ID."""
        job_id = job.get("id")
        title = job.get("title", "")
        content = format_kboard_content(job)

        res = post_job_opening(title=title, content=content, board_id=self.board_id)
        if res and res.get("status") == "success":
            kboard_uid = res.get("kboard_uid") or res.get("post_id")
            self.published_records[str(job_id)] = {
                "kboard_uid": kboard_uid,
                "title": title,
                "source": job.get("source"),
                "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self._save_published_records()
            return res
        return None

    def publish_new_jobs(self, jobs: List[Dict[str, Any]], limit: Optional[int] = None, delay_sec: float = 1.0) -> Dict[str, int]:
        """
        Publish only newly discovered jobs that haven't been published yet.
        """
        stats = {
            "total": len(jobs),
            "skipped": 0,
            "published": 0,
            "failed": 0
        }

        to_publish = [j for j in jobs if not self.is_published(j.get("id"))]
        if limit:
            to_publish = to_publish[:limit]

        stats["skipped"] = len(jobs) - len(to_publish)

        print(f"\n[WordPress KBoard 자동 연동] 총 {len(jobs)}건 중 신규 발행 대상: {len(to_publish)}건 (기존 등록 {stats['skipped']}건 스킵)")

        for idx, job in enumerate(to_publish, 1):
            title = job.get("title", "")
            print(f" -> [{idx}/{len(to_publish)}] 게시 중: {title[:35]}...")
            res = self.publish_single_job(job)
            if res:
                stats["published"] += 1
                uid = res.get("kboard_uid") or res.get("post_id")
                print(f"    [OK] 성공 (KBoard UID: {uid})")
            else:
                stats["failed"] += 1
                print(f"    [FAIL] 실패")

            if idx < len(to_publish) and delay_sec > 0:
                time.sleep(delay_sec)

        return stats
