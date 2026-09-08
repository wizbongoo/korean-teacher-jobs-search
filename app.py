import json
import os
import sys
from datetime import datetime, date
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="한국어교원 채용 운영자 관리 센터",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern Operator Admin styling
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* Header styling */
    .admin-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.8rem 1.5rem;
        border-radius: 0.85rem;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 6px solid #3b82f6;
    }
    .admin-header h1 {
        color: white !important;
        font-size: 1.85rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
    }
    .admin-header p {
        color: #cbd5e1;
        font-size: 0.95rem;
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
        padding: 1.1rem;
        border-radius: 0.75rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
        text-align: center;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 600;
    }

    /* Admin Job Card Styling */
    .admin-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: border-color 0.2s ease;
    }
    .admin-card:hover {
        border-color: #94a3b8;
    }
    .admin-card-pending {
        border-left: 5px solid #f59e0b;
    }
    .admin-card-published {
        border-left: 5px solid #10b981;
    }
    .admin-card-rejected {
        border-left: 5px solid #94a3b8;
        background-color: #f8fafc;
    }

    /* Badges */
    .badge-wrap {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 0.6rem;
        flex-wrap: wrap;
    }
    .badge {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
    }
    .badge-src-kteacher { background-color: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
    .badge-src-kleocean { background-color: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
    .badge-src-ksif     { background-color: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
    .badge-src-danuri   { background-color: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }
    .badge-src-worknet  { background-color: #f0fdfa; color: #0f766e; border: 1px solid #99f6e4; }

    .badge-dday-danger { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    .badge-dday-warn   { background-color: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
    .badge-dday-safe   { background-color: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
    .badge-dday-always { background-color: #f8fafc; color: #475569; border: 1px solid #e2e8f0; }

    .badge-tag { background-color: #f1f5f9; color: #334155; font-size: 0.72rem; padding: 0.2rem 0.5rem; border-radius: 0.375rem; }
    .badge-uid { background-color: #ecfdf5; color: #047857; border: 1px solid #6ee7b7; font-weight: 800; }

    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.4rem;
        line-height: 1.4;
    }
    .card-meta {
        font-size: 0.82rem;
        color: #475569;
        margin-bottom: 0.75rem;
    }

    .meta-item {
        margin-right: 0.8rem;
    }

    /* Outlink Buttons */
    .outlink-btn {
        display: inline-block;
        background-color: #f1f5f9;
        color: #334155 !important;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.35rem 0.7rem;
        border-radius: 0.375rem;
        text-decoration: none;
        border: 1px solid #cbd5e1;
    }
    .outlink-btn:hover {
        background-color: #e2e8f0;
    }

    .kboard-btn {
        display: inline-block;
        background-color: #ecfdf5;
        color: #047857 !important;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 0.35rem 0.7rem;
        border-radius: 0.375rem;
        text-decoration: none;
        border: 1px solid #a7f3d0;
    }
    .kboard-btn:hover {
        background-color: #d1fae5;
    }
</style>
""", unsafe_allow_html=True)

from src.poster import (
    load_jobs_file,
    save_jobs_file,
    approve_and_publish_job,
    reject_job,
    restore_to_pending,
    batch_approve_jobs,
    load_published_records,
    WP_URL,
    BOARD_ID
)

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
    <div class="admin-header">
        <h1>🛠️ 한국어교원 채용공고 운영자 관리 센터</h1>
        <p>Human-in-the-Loop 검토 · 편집 · 워드프레스 KBoard 원클릭 발행 관리 콘솔</p>
    </div>
    """, unsafe_allow_html=True)

    # Load Jobs Data
    all_jobs = load_jobs_file()
    today = datetime.now().date()

    if not all_jobs:
        st.warning("⚠️ 등록된 채용 공고가 없습니다. 사이드바에서 [🔄 크롤러 실행]을 눌러 데이터를 수집해 주세요.")
        if st.button("🔄 크롤러 수동 실행"):
            with st.spinner("5대 사이트 공고를 수집 및 정제 중입니다..."):
                from src.crawler import run_pipeline
                run_pipeline()
                st.rerun()
        return

    # Normalize missing status fields
    pub_records = load_published_records()
    for job in all_jobs:
        jid = str(job.get("id"))
        if jid in pub_records and job.get("status") != "published":
            job["status"] = "published"
            job["kboard_uid"] = pub_records[jid].get("kboard_uid")
        elif "status" not in job:
            job["status"] = "pending"
            job["kboard_uid"] = None
            job["reviewed_at"] = None

    # Categorize by status
    pending_jobs = [j for j in all_jobs if j.get("status") == "pending"]
    published_jobs = [j for j in all_jobs if j.get("status") == "published"]
    rejected_jobs = [j for j in all_jobs if j.get("status") == "rejected"]

    # Top KPI Metrics Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #f59e0b;">
            <div class="metric-value" style="color: #d97706;">{len(pending_jobs)}</div>
            <div class="metric-label">🟡 검토 대기 (Pending)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #10b981;">
            <div class="metric-value" style="color: #059669;">{len(published_jobs)}</div>
            <div class="metric-label">🟢 KBoard 게시 완료</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #64748b;">
            <div class="metric-value" style="color: #475569;">{len(rejected_jobs)}</div>
            <div class="metric-label">⚪ 반려 / 제외 목록</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 4px solid #3b82f6;">
            <div class="metric-value" style="color: #2563eb;">{len(all_jobs)}</div>
            <div class="metric-label">📦 전체 수집 후보</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sidebar: Controls & Instructions
    st.sidebar.header("⚙️ 운영자 관리 도구")
    if st.sidebar.button("🔄 최신 공고 크롤링 실행", use_container_width=True, type="primary"):
        with st.spinner("5대 포털에서 최신 채용 공고를 수집하고 정제 중입니다..."):
            from src.crawler import run_pipeline
            run_pipeline()
            st.sidebar.success("크롤링 및 후보군 적재 완료!")
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("🌐 워드프레스 KBoard")
    st.sidebar.markdown(f"- **사이트 주소**: [{WP_URL}]({WP_URL})")
    st.sidebar.markdown(f"- **게시판 ID**: `[kboard id={BOARD_ID}]`")
    st.sidebar.caption("운영자가 [게시 승인]을 누르면 위 사이트 KBoard 게시판에 즉시 발행됩니다.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("📖 운영 가이드 (10분 루틴)")
    st.sidebar.info("""
    1. **[검토 대기]** 탭에서 신규 공고 확인
    2. 필요시 **[공고 원문 ↗]** 확인
    3. 기관명·마감일·지역 오탈자 있을 경우 **[수정]**
    4. 검증 완료 시 **[✅ 게시 승인]** 클릭
    5. 부적절/중복 공고는 **[❌ 반려]** 처리
    """)

    # Source Badge Class Mapping
    src_class_map = {
        "국립국어원": "badge-src-kteacher",
        "한국어교육바다": "badge-src-kleocean",
        "세종학당재단": "badge-src-ksif",
        "다누리": "badge-src-danuri",
        "워크넷": "badge-src-worknet",
    }

    # 3 Main Tabs
    tab_pending, tab_published, tab_rejected = st.tabs([
        f"🟡 검토 대기 공고 ({len(pending_jobs)}건)",
        f"🟢 KBoard 게시 완료 ({len(published_jobs)}건)",
        f"⚪ 반려 / 제외 내역 ({len(rejected_jobs)}건)"
    ])

    # -------------------------------------------------------------
    # TAB 1: 🟡 검토 대기 (Pending Review)
    # -------------------------------------------------------------
    with tab_pending:
        st.subheader("🟡 검토 대기 공고 목록")
        st.caption("새로 수집된 후보 공고입니다. 내용을 검토한 후 승인하면 워드프레스 KBoard에 즉시 발행됩니다.")

        if not pending_jobs:
            st.success("🎉 현재 검토 대기 중인 공고가 모두 처리되었습니다!")
        else:
            # Filter bar for pending jobs
            f_col1, f_col2, f_col3 = st.columns([4, 3, 3])
            with f_col1:
                kw_pending = st.text_input("🔍 공고명 / 기관명 검색", key="kw_pending", placeholder="검색어 입력...")
            with f_col2:
                sources_pending = ["전체"] + sorted(list(set(j.get("source", "") for j in pending_jobs)))
                src_pending = st.selectbox("출처 필터", sources_pending, key="src_pending")
            with f_col3:
                sort_pending = st.selectbox("정렬 기준", ["마감일 빠른순", "최신 등록순", "기관명순"], key="sort_pending")

            # Apply pending filters
            display_pending = pending_jobs
            if kw_pending:
                k_low = kw_pending.lower()
                display_pending = [
                    j for j in display_pending
                    if k_low in j.get("title", "").lower() or k_low in j.get("organization", "").lower()
                ]
            if src_pending != "전체":
                display_pending = [j for j in display_pending if j.get("source") == src_pending]

            # Calculate D-days for sorting
            for j in display_pending:
                d_label, d_cls, d_days = get_dday_info(j.get("deadline", ""), today)
                j["_dday_label"] = d_label
                j["_dday_cls"] = d_cls
                j["_dday_days"] = d_days

            if sort_pending == "마감일 빠른순":
                display_pending.sort(key=lambda x: x["_dday_days"])
            elif sort_pending == "최신 등록순":
                display_pending.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            elif sort_pending == "기관명순":
                display_pending.sort(key=lambda x: x.get("organization", ""))

            # Batch Action Bar
            st.markdown("---")
            b_col1, b_col2 = st.columns([8, 2])
            with b_col1:
                st.write(f"조회된 검토 대기 공고: **{len(display_pending)}건**")
            with b_col2:
                if st.button("⚡ 상위 5건 일괄 승인", use_container_width=True, help="조회된 상위 5개 공고를 한 번에 승인하여 KBoard에 등록합니다."):
                    batch_targets = [j.get("id") for j in display_pending[:5]]
                    with st.spinner(f"{len(batch_targets)}건의 공고를 KBoard로 일괄 발행 중입니다..."):
                        stats = batch_approve_jobs(batch_targets, delay_sec=0.5)
                        st.success(f"일괄 승인 완료: {stats['published']}건 발행 성공!")
                        st.rerun()

            # Render pending job cards
            for idx, job in enumerate(display_pending):
                job_id = str(job.get("id"))
                src = job.get("source", "기타")
                src_cls = src_class_map.get(src, "badge-src-kteacher")
                title = job.get("title", "")
                org = job.get("organization", "미기재")
                loc = job.get("location", "전국/기타")
                grade = job.get("grade", "무관/미지정")
                dl = job.get("deadline", "상시채용")
                created = job.get("created_at", "-")
                url = job.get("url", "#")
                dday_label = job.get("_dday_label", "상시채용")
                dday_cls = job.get("_dday_cls", "badge-dday-always")

                with st.container():
                    st.markdown(f"""
                    <div class="admin-card admin-card-pending">
                        <div class="badge-wrap">
                            <span class="badge {src_cls}">{src}</span>
                            <span class="badge {dday_cls}">{dday_label}</span>
                            <span class="badge badge-tag">📍 {loc}</span>
                            <span class="badge badge-tag">🎓 자격: {grade}</span>
                        </div>
                        <div class="card-title">{title}</div>
                        <div class="card-meta">
                            <span class="meta-item">🏢 <b>{org}</b></span>
                            <span class="meta-item">⏰ 마감: <b style="color:#dc2626;">{dl}</b></span>
                            <span class="meta-item">📅 수집일: {created}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Controls row for this card
                    act_col1, act_col2, act_col3, act_col4 = st.columns([3, 2, 2, 3])
                    
                    with act_col1:
                        st.markdown(f'<a href="{url}" target="_blank" class="outlink-btn">🔗 공고 원문 확인 ↗</a>', unsafe_allow_html=True)

                    with act_col2:
                        # Direct Approval Button
                        if st.button("✅ 게시 승인", key=f"appr_{job_id}_{idx}", type="primary", use_container_width=True):
                            with st.spinner("KBoard로 발행 중..."):
                                res = approve_and_publish_job(job_id)
                                if res.get("status") == "success":
                                    st.success(f"승인 완료! (KBoard UID: {res.get('kboard_uid')})")
                                    st.rerun()
                                else:
                                    st.error(f"발행 실패: {res.get('message')}")

                    with act_col3:
                        # Reject Button
                        if st.button("❌ 반려/제외", key=f"rej_{job_id}_{idx}", use_container_width=True):
                            reject_job(job_id)
                            st.info("반려 처리되었습니다.")
                            st.rerun()

                    with act_col4:
                        # Optional edit expander
                        with st.expander("✏️ 공고 내용 수정"):
                            edit_title = st.text_input("제목", value=title, key=f"et_{job_id}")
                            edit_org = st.text_input("기관명", value=org, key=f"eo_{job_id}")
                            edit_dl = st.text_input("마감일 (YYYY-MM-DD 또는 상시채용)", value=dl, key=f"edl_{job_id}")
                            edit_loc = st.text_input("근무지역", value=loc, key=f"eloc_{job_id}")
                            edit_grade = st.text_input("자격요건", value=grade, key=f"egr_{job_id}")

                            if st.button("💾 수정 후 게시 승인", key=f"edit_appr_{job_id}", type="primary"):
                                with st.spinner("수정사항을 적용하여 KBoard로 발행 중..."):
                                    res = approve_and_publish_job(
                                        job_id,
                                        custom_title=edit_title,
                                        custom_org=edit_org,
                                        custom_deadline=edit_dl,
                                        custom_location=edit_loc,
                                        custom_grade=edit_grade
                                    )
                                    if res.get("status") == "success":
                                        st.success(f"수정 후 승인 완료! (KBoard UID: {res.get('kboard_uid')})")
                                        st.rerun()
                                    else:
                                        st.error(f"발행 실패: {res.get('message')}")

                    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 2: 🟢 게시 완료 (Published)
    # -------------------------------------------------------------
    with tab_published:
        st.subheader("🟢 KBoard 게시 완료 공고 목록")
        st.caption("운영자의 승인을 거쳐 워드프레스 KBoard 공개 커뮤니티에 등록된 공고들입니다.")

        if not published_jobs:
            st.info("아직 게시 승인된 공고가 없습니다. [검토 대기] 탭에서 공고를 승인해 주세요.")
        else:
            p_col1, p_col2 = st.columns([7, 3])
            with p_col1:
                kw_pub = st.text_input("🔍 게시된 공고 검색", key="kw_pub", placeholder="검색어 입력...")
            with p_col2:
                st.write(f"게시 완료 총계: **{len(published_jobs)}건**")

            display_published = published_jobs
            if kw_pub:
                k_low = kw_pub.lower()
                display_published = [
                    j for j in display_published
                    if k_low in j.get("title", "").lower() or k_low in j.get("organization", "").lower()
                ]

            for idx, job in enumerate(display_published):
                job_id = str(job.get("id"))
                src = job.get("source", "기타")
                src_cls = src_class_map.get(src, "badge-src-kteacher")
                title = job.get("title", "")
                org = job.get("organization", "미기재")
                loc = job.get("location", "전국/기타")
                grade = job.get("grade", "무관/미지정")
                dl = job.get("deadline", "상시채용")
                url = job.get("url", "#")
                k_uid = job.get("kboard_uid") or pub_records.get(job_id, {}).get("kboard_uid", "-")
                k_url = f"{WP_URL}/?mod=document&uid={k_uid}"
                rev_time = job.get("reviewed_at") or pub_records.get(job_id, {}).get("published_at", "-")

                with st.container():
                    st.markdown(f"""
                    <div class="admin-card admin-card-published">
                        <div class="badge-wrap">
                            <span class="badge {src_cls}">{src}</span>
                            <span class="badge badge-uid">KBoard UID: #{k_uid}</span>
                            <span class="badge badge-tag">📍 {loc}</span>
                            <span class="badge badge-tag">🎓 {grade}</span>
                        </div>
                        <div class="card-title">{title}</div>
                        <div class="card-meta">
                            <span class="meta-item">🏢 <b>{org}</b></span>
                            <span class="meta-item">⏰ 마감: <b>{dl}</b></span>
                            <span class="meta-item">🚀 발행일시: {rev_time}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_btn1, c_btn2, c_btn3 = st.columns([3, 3, 4])
                    with c_btn1:
                        st.markdown(f'<a href="{k_url}" target="_blank" class="kboard-btn">🌐 KBoard 게시글 보기 ↗</a>', unsafe_allow_html=True)
                    with c_btn2:
                        st.markdown(f'<a href="{url}" target="_blank" class="outlink-btn">🔗 원문 공고 보기 ↗</a>', unsafe_allow_html=True)
                    with c_btn3:
                        if st.button("↩️ 검토 대기로 되돌리기", key=f"restore_pub_{job_id}_{idx}"):
                            restore_to_pending(job_id)
                            st.info("검토 대기 상태로 복원되었습니다.")
                            st.rerun()

                    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 3: ⚪ 반려 / 제외 내역 (Rejected)
    # -------------------------------------------------------------
    with tab_rejected:
        st.subheader("⚪ 반려 / 제외 공고 내역")
        st.caption("운영자가 반려하거나 제외 처리한 공고입니다. 필요시 언제든지 검토 대기로 복원할 수 있습니다.")

        if not rejected_jobs:
            st.info("반려 처리된 공고가 없습니다.")
        else:
            st.write(f"반려 공고 총계: **{len(rejected_jobs)}건**")
            for idx, job in enumerate(rejected_jobs):
                job_id = str(job.get("id"))
                src = job.get("source", "기타")
                src_cls = src_class_map.get(src, "badge-src-kteacher")
                title = job.get("title", "")
                org = job.get("organization", "미기재")
                loc = job.get("location", "전국/기타")
                rev_time = job.get("reviewed_at", "-")
                url = job.get("url", "#")

                with st.container():
                    st.markdown(f"""
                    <div class="admin-card admin-card-rejected">
                        <div class="badge-wrap">
                            <span class="badge {src_cls}">{src}</span>
                            <span class="badge badge-tag">📍 {loc}</span>
                            <span class="badge" style="background-color:#fee2e2; color:#991b1b;">제외/반려됨</span>
                        </div>
                        <div class="card-title" style="color: #64748b; text-decoration: line-through;">{title}</div>
                        <div class="card-meta">
                            <span class="meta-item">🏢 {org}</span>
                            <span class="meta-item">📅 처리일시: {rev_time}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    r_col1, r_col2 = st.columns([3, 7])
                    with r_col1:
                        if st.button("↩️ 검토 대기로 복원", key=f"restore_rej_{job_id}_{idx}", type="secondary"):
                            restore_to_pending(job_id)
                            st.success("검토 대기 상태로 복원되었습니다.")
                            st.rerun()
                    with r_col2:
                        st.markdown(f'<a href="{url}" target="_blank" class="outlink-btn">🔗 원문 공고 확인 ↗</a>', unsafe_allow_html=True)

                    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.caption("🛠️ 한국어교원 채용 통합 관리자 콘솔 | Human-in-the-Loop 운영자 검토 & WordPress KBoard 공식 발행 파이프라인")

if __name__ == "__main__":
    main()
