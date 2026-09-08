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
KBOARD_PUBLISHED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "published_kboard.json")

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

def load_kboard_published():
    """Load records of jobs published to WordPress KBoard."""
    if not os.path.exists(KBOARD_PUBLISHED_PATH):
        return {}
    try:
        with open(KBOARD_PUBLISHED_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

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

    # WordPress KBoard Integration Section
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌐 워드프레스 KBoard")
    st.sidebar.caption("🔗 [korean-teacher.infinityfreeapp.com](https://korean-teacher.infinityfreeapp.com)")
    kboard_records = load_kboard_published()
    st.sidebar.info(f"게시판 동기화: **{len(kboard_records)}건** 완료")
    if st.sidebar.button("🚀 신규 공고 KBoard 동기화", use_container_width=True):
        with st.spinner("새로운 채용공고를 KBoard로 전송 중입니다..."):
            from src.publisher import WordPressPublisher
            pub = WordPressPublisher()
            stats = pub.publish_new_jobs(raw_jobs, delay_sec=0.5)
            st.sidebar.success(f"동기화 완료! (신규 {stats['published']}건, 기존 유지 {stats['skipped']}건)")
            st.rerun()

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

                kboard_info = kboard_records.get(str(job.get("id")))
                kboard_btn_html = ""
                if kboard_info:
                    k_uid = kboard_info.get("kboard_uid")
                    k_url = f"https://korean-teacher.infinityfreeapp.com/?mod=document&uid={k_uid}"
                    kboard_btn_html = f'<a href="{k_url}" target="_blank" style="display:inline-block; margin-left:6px; background-color:#ecfdf5; color:#047857 !important; border:1px solid #a7f3d0; padding:0.35rem 0.65rem; border-radius:0.4rem; font-size:0.8rem; font-weight:600; text-decoration:none;">KBoard ↗</a>'

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
                        <div>
                            <a href="{url}" target="_blank" class="apply-btn">공고 원문 ↗</a>
                            {kboard_btn_html}
                        </div>
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
