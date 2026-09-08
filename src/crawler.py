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
    print(f"      [3/3] 운영자 검토 대기(Pending) 데이터 병합 및 저장: {OUTPUT_FILE}")
    print("=" * 60)

    existing_jobs = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_jobs = json.load(f)
        except Exception as e:
            print(f" -> [Warning] 기존 데이터 로드 실패: {e}")

    existing_map = {str(j.get("id")): j for j in existing_jobs if "id" in j}

    # Cross-reference published records
    published_records = {}
    pub_file = os.path.join(DATA_DIR, "published_kboard.json")
    if os.path.exists(pub_file):
        try:
            with open(pub_file, "r", encoding="utf-8") as pf:
                published_records = json.load(pf)
        except Exception:
            published_records = {}

    merged_jobs = []
    new_candidate_count = 0
    retained_count = 0

    for cj in clean_jobs:
        cid = str(cj.get("id"))
        if cid in existing_map:
            # Preserve existing job metadata and operator decisions
            old_job = existing_map[cid]
            cj["status"] = old_job.get("status", "pending")
            cj["kboard_uid"] = old_job.get("kboard_uid")
            cj["reviewed_at"] = old_job.get("reviewed_at")

            # If it's in published_records, ensure status reflects published
            if cid in published_records and cj["status"] != "published":
                cj["status"] = "published"
                cj["kboard_uid"] = published_records[cid].get("kboard_uid")

            retained_count += 1
        else:
            # Newly discovered job
            if cid in published_records:
                cj["status"] = "published"
                cj["kboard_uid"] = published_records[cid].get("kboard_uid")
                cj["reviewed_at"] = published_records[cid].get("published_at")
            else:
                cj["status"] = "pending"
                cj["kboard_uid"] = None
                cj["reviewed_at"] = None
            new_candidate_count += 1
        merged_jobs.append(cj)

    # Keep any existing jobs that weren't captured in the current crawl
    current_ids = {str(j.get("id")) for j in merged_jobs}
    for old_id, old_job in existing_map.items():
        if old_id not in current_ids:
            merged_jobs.append(old_job)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_jobs, f, ensure_ascii=False, indent=2)

    pending_total = len([j for j in merged_jobs if j.get("status") == "pending"])
    pub_total = len([j for j in merged_jobs if j.get("status") == "published"])
    rej_total = len([j for j in merged_jobs if j.get("status") == "rejected"])

    print(f"-> 총 {len(merged_jobs)}건 저장 완료 (기존 유지: {retained_count}건, 신규 발굴: {new_candidate_count}건)")
    print(f"-> [상태 요약] 🟡 검토 대기: {pending_total}건 | 🟢 게시 완료: {pub_total}건 | ⚪ 반려: {rej_total}건")
    print("-> 운영자 승인은 Streamlit 관리자 콘솔(app.py)에서 검토 후 진행됩니다.")

    return merged_jobs


if __name__ == "__main__":
    run_pipeline()
