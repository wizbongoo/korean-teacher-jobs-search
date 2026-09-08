import json
import os
import re
import sys
from datetime import datetime
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


def run_pipeline() -> list[dict]:
    """Execute all crawlers, clean data, and save to jobs.json."""
    print("=" * 60)
    print("      [1/3] 한국어교원 채용 사이트 4개 수집 시작...")
    print("=" * 60)

    raw_jobs = []

    # 1. 국립국어원
    print("[1/4] 국립국어원 한국어교원 구인게시판 수집 중...")
    try:
        kteacher_jobs = KTeacherCrawler().crawl(max_pages=5)
        print(f" -> 국립국어원 수집 완료: {len(kteacher_jobs)}건")
        raw_jobs.extend(kteacher_jobs)
    except Exception as e:
        print(f" -> [Error] 국립국어원 수집 실패: {e}")

    # 2. KLE Ocean
    print("[2/4] 한국어교육바다 (KLE Ocean) RSS 피드 수집 중...")
    try:
        kle_jobs = KLEOceanCrawler().crawl()
        print(f" -> KLE Ocean 수집 완료: {len(kle_jobs)}건")
        raw_jobs.extend(kle_jobs)
    except Exception as e:
        print(f" -> [Error] KLE Ocean 수집 실패: {e}")

    # 3. 세종학당재단
    print("[3/4] 세종학당재단 채용정보 수집 중...")
    try:
        ksif_jobs = KSIFCrawler().crawl()
        print(f" -> 세종학당재단 수집 완료: {len(ksif_jobs)}건")
        raw_jobs.extend(ksif_jobs)
    except Exception as e:
        print(f" -> [Error] 세종학당재단 수집 실패: {e}")

    # 4. 다누리
    print("[4/4] 다누리(다문화가족포털) 한국어 구인공고 수집 중...")
    try:
        danuri_jobs = DanuriCrawler().crawl(max_pages=5)
        print(f" -> 다누리 수집 완료: {len(danuri_jobs)}건")
        raw_jobs.extend(danuri_jobs)
    except Exception as e:
        print(f" -> [Error] 다누리 수집 실패: {e}")

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
