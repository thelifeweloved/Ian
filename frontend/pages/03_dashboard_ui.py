import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

from common_ui import (
    api_health_check_or_stop,
    api_get,
    api_json_or_show_error,
)

st.set_page_config(page_title="MindWay · Dashboard", page_icon=None, layout="wide")

# -------------------------
# Styles (product-like)
# -------------------------
st.markdown(
    """
    <style>
      html, body, [class*="css"]{font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;}
      .mw-h1{font-size:22px;font-weight:950;color:#111827;margin:0 0 2px 0;}
      .mw-sub{font-size:12px;color:#6b7280;font-weight:650;margin:0 0 14px 0;}
      .mw-card{
        border:1px solid #eee;border-radius:14px;padding:14px;background:rgba(255,255,255,0.96);
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      }
      .mw-card-title{font-size:13px;font-weight:900;color:#111827;margin-bottom:10px;}
      .mw-muted{font-size:12px;color:#6b7280;font-weight:600;}
      .mw-badge{display:inline-block;padding:5px 10px;border-radius:999px;background:#f3f4f6;color:#374151;font-weight:800;font-size:12px;}
      .mw-alert{border-left: 4px solid #111827; padding-left: 10px; margin: 8px 0;}
      .mw-kpi-note{font-size:11px;color:#9ca3af;font-weight:650;margin-top:6px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="mw-h1">MindWay Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="mw-sub">상담사가 “지금 무엇을 해야 하는지” 빠르게 판단하는 운영 대시보드</div>', unsafe_allow_html=True)

api_health_check_or_stop(show_success=False)

# -------------------------
# Sidebar controls
# -------------------------
with st.sidebar:
    st.markdown("### 설정")
    counselor_id = st.number_input("상담사 ID", min_value=1, value=1)
    sess_limit = st.slider("세션 조회 개수", 20, 200, 50)
    st.divider()
    st.caption("※ 분석 그래프는 백엔드 /stats API 기반")
    st.caption("※ 운영 KPI는 /sessions 기반(프론트 계산)")

# -------------------------
# Helpers
# -------------------------
def _to_dt(s):
    if s is None:
        return pd.NaT
    try:
        return pd.to_datetime(s, errors="coerce")
    except Exception:
        return pd.NaT

def _col(df, *cands):
    """df에서 존재하는 첫 컬럼명 반환"""
    for c in cands:
        if c in df.columns:
            return c
    return None

def load_sessions(limit: int) -> pd.DataFrame:
    r = api_get("/sessions", params={"limit": int(limit)})
    data = api_json_or_show_error(r, title="/sessions 호출 실패")
    df = pd.DataFrame(data.get("items", []))
    return df

def load_stat(path: str) -> pd.DataFrame:
    r = api_get(path, params={"counselor_id": int(counselor_id)})
    data = api_json_or_show_error(r, title=f"{path} 호출 실패")
    return pd.DataFrame(data.get("items", []))

# -------------------------
# Data load
# -------------------------
df_sess = load_sessions(sess_limit)

# 세션 컬럼 추정(스키마가 바뀌어도 최대한 버티도록)
col_id = _col(df_sess, "id", "sess_id")
col_cid = _col(df_sess, "counselor_id", "cid")
col_client = _col(df_sess, "client_id", "client")
col_start = _col(df_sess, "start_at", "start_time", "started_at", "created_at")
col_end = _col(df_sess, "end_at", "ended_at")
col_reason = _col(df_sess, "end_reason", "reason")
col_progress = _col(df_sess, "progress", "status")
col_channel = _col(df_sess, "channel")

if not df_sess.empty and col_start:
    df_sess["_start_dt"] = df_sess[col_start].apply(_to_dt)
else:
    df_sess["_start_dt"] = pd.NaT

today = date.today()

# 상담사 필터(있으면)
if not df_sess.empty and col_cid:
    df_my = df_sess[df_sess[col_cid] == int(counselor_id)].copy()
else:
    df_my = df_sess.copy()

# KPI 계산
total_sessions = int(len(df_my))
today_sessions = int((df_my["_start_dt"].dt.date == today).sum()) if total_sessions and df_my["_start_dt"].notna().any() else 0

dropout_sessions = 0
if total_sessions and col_reason:
    dropout_sessions = int((df_my[col_reason].astype(str).str.upper() == "DROPOUT").sum())

# "활성" 세션 추정: end_at이 없거나 progress가 진행중처럼 보이는 것
active_sessions = 0
if total_sessions:
    if col_end:
        active_sessions = int(df_my[col_end].isna().sum())
    elif col_progress:
        active_sessions = int(df_my[col_progress].astype(str).str.contains("ING|ACTIVE|PROGRESS|RUN", case=False, na=False).sum())

# 채널 분포(있으면)
channel_summary = None
if total_sessions and col_channel:
    channel_summary = df_my[col_channel].value_counts(dropna=False).head(5)

# Work Queue: missed alerts
# (이 API는 "알림 없이 이탈" 목록/집계로 가정. 실제 컬럼명 몰라도 표로 보여줌)
df_missed = load_stat("/stats/missed-alerts")

# 분석 그래프용 데이터
df_topic = load_stat("/stats/topic-dropout")
df_grade = load_stat("/stats/client-grade-dropout")
df_time = load_stat("/stats/time-dropout")
df_channel = load_stat("/stats/channel-dropout")
df_growth = load_stat("/stats/monthly-growth")

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3 = st.tabs(["Overview", "Work Queue", "Analytics"])

# =========================================================
# TAB 1: Overview (운영 대시보드)
# =========================================================
with tab1:
    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("오늘 상담", today_sessions)
    c2.metric("총 세션(조회범위)", total_sessions)
    c3.metric("이탈(DROPOUT)", dropout_sessions)
    c4.metric("활성 세션(추정)", active_sessions)

    st.caption("운영 KPI는 /sessions 데이터를 기준으로 프론트에서 계산합니다. (DB seed 상태에 따라 값이 작을 수 있어요)")

    # Risk banner
    st.divider()
    left, right = st.columns([1.6, 1])

    with left:
        st.markdown("<div class='mw-card'><div class='mw-card-title'>⚠️ 운영 경고</div>", unsafe_allow_html=True)

        # “대시보드다운” 경고 로직 (단순하지만 직관적)
        alerts = []
        if dropout_sessions >= 1:
            alerts.append(f"최근 조회 범위 내 이탈 세션이 {dropout_sessions}건 있습니다. (원인 분석/재발 방지 필요)")
        if not df_missed.empty:
            alerts.append(f"‘알림 없이 이탈(탐지 실패)’ 케이스가 {len(df_missed)}건 있습니다. (룰/임계값 점검 필요)")
        if total_sessions == 0:
            alerts.append("세션 데이터가 없습니다. seed.sql/seed_min.sql 실행 또는 상담 생성이 필요합니다.")

        if not alerts:
            st.success("현재 확인된 주요 위험 신호가 없습니다.")
        else:
            for a in alerts[:4]:
                st.markdown(f"<div class='mw-alert'><b>{a}</b></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='mw-card'><div class='mw-card-title'>📡 채널/상태 요약</div>", unsafe_allow_html=True)
        if channel_summary is not None and len(channel_summary) > 0:
            for k, v in channel_summary.items():
                st.markdown(f"<div style='display:flex;justify-content:space-between; margin:6px 0;'><span class='mw-badge'>{k}</span><b>{int(v)}</b></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='mw-muted'>채널 정보(channel)가 없어 요약을 생략합니다.</div>", unsafe_allow_html=True)

        # “예약/예정” 영역(가능한 만큼만 추정)
        st.divider()
        st.markdown("<div class='mw-card-title'>📅 오늘/예정 업무(추정)</div>", unsafe_allow_html=True)
        if total_sessions == 0:
            st.caption("세션이 없어 표시할 항목이 없습니다.")
        else:
            # 예정 세션: end_at이 비었거나 progress가 미완료처럼 보이는 것
            df_up = df_my.copy()
            if col_end:
                df_up = df_up[df_up[col_end].isna()]
            if col_progress:
                # 완료/종료/드랍아웃처럼 보이면 제외
                df_up = df_up[~df_up[col_progress].astype(str).str.contains("DONE|END|CLOSE|DROPOUT", case=False, na=False)]
            # 오늘 시작한 것 우선
            if df_up["_start_dt"].notna().any():
                df_up = df_up.sort_values("_start_dt", ascending=False)

            show_cols = [c for c in [col_id, col_client, col_channel, col_progress, col_start] if c and c in df_up.columns]
            st.dataframe(df_up[show_cols].head(8), use_container_width=True, height=260)

        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # Recent sessions table (quick glance)
    st.subheader("🗂️ 최근 세션(빠른 확인)")
    if df_my.empty:
        st.info("표시할 세션이 없습니다.")
    else:
        show_cols = [c for c in [col_id, col_client, col_channel, col_progress, col_reason, col_start, col_end] if c and c in df_my.columns]
        st.dataframe(df_my[show_cols].head(30), use_container_width=True, height=420)

# =========================================================
# TAB 2: Work Queue (업무 우선순위/조치)
# =========================================================
with tab2:
    st.subheader("🧯 Work Queue · 지금 당장 조치가 필요한 항목")

    # 1) Missed alerts
    st.markdown("### 1) 알림 없이 이탈(탐지 실패) 케이스")
    if df_missed.empty:
        st.success("탐지 실패 케이스가 없습니다.")
    else:
        st.warning("탐지 실패 케이스가 존재합니다. 룰/임계값 조정 또는 데이터 누락 여부 점검이 필요합니다.")
        st.dataframe(df_missed, use_container_width=True, height=320)

    # 2) Quick actions (운영 플레이북)
    st.markdown("### 2) 빠른 조치 가이드(플레이북)")
    st.markdown(
        """
- **탐지 실패가 1건 이상**이면:  
  - (A) 해당 세션의 마지막 10개 메시지에서 키워드/감정 점수 누락 여부 확인  
  - (B) 규칙(NEG_KEYWORD 등) 적용 조건이 너무 좁지 않은지 점검  
  - (C) `speaker`, `end_reason` 값이 명세서 ENUM과 정확히 일치하는지 확인

- **이탈이 급증**하면:  
  - (A) 특정 채널/시간대에 집중되는지 확인  
  - (B) 특정 내담자 등급(status)에 집중되는지 확인  
  - (C) 상담사 발언 패턴(“왜/부정/반박”)이 늘었는지 확인
        """
    )

# =========================================================
# TAB 3: Analytics (통계/그래프)
# =========================================================
with tab3:
    st.subheader("📈 Analytics · 통계/패턴 분석")

    # Layout 2 columns
    a1, a2 = st.columns(2)

    # ---- Topic dropout
    with a1:
        st.markdown("### 🧠 주제별 이탈")
        if df_topic.empty:
            st.info("데이터 없음")
        else:
            # x: 첫 컬럼, y: 마지막 숫자 컬럼(가능한 경우)
            xcol = df_topic.columns[0]
            ycol = df_topic.columns[-1]
            fig = px.bar(df_topic, x=xcol, y=ycol)
            st.plotly_chart(fig, use_container_width=True)

    # ---- Client grade dropout
    with a2:
        st.markdown("### 👥 내담자 등급별 이탈")
        if df_grade.empty:
            st.info("데이터 없음")
        else:
            # 가능한 경우 pie, 아니면 bar로
            if len(df_grade.columns) >= 2:
                ncol = df_grade.columns[0]
                vcol = df_grade.columns[1]
                fig = px.pie(df_grade, names=ncol, values=vcol)
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.bar(df_grade, x=df_grade.columns[0], y=df_grade.columns[-1])
                st.plotly_chart(fig, use_container_width=True)

    st.divider()

    b1, b2 = st.columns(2)

    # ---- Time dropout
    with b1:
        st.markdown("### ⏰ 시간대별 이탈")
        if df_time.empty:
            st.info("데이터 없음")
        else:
            fig = px.bar(df_time, x=df_time.columns[0], y=df_time.columns[-1])
            st.plotly_chart(fig, use_container_width=True)

    # ---- Channel dropout
    with b2:
        st.markdown("### 📡 채널별 이탈")
        if df_channel.empty:
            st.info("데이터 없음")
        else:
            fig = px.bar(df_channel, x=df_channel.columns[0], y=df_channel.columns[-1])
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---- Monthly growth
    st.markdown("### 📈 월별 성장 추이")
    if df_growth.empty:
        st.info("데이터 없음")
    else:
        fig = px.line(df_growth, x=df_growth.columns[0], y=df_growth.columns[-1], markers=True)
        st.plotly_chart(fig, use_container_width=True)

    st.caption("그래프의 축/값 컬럼은 DB 변경에 견디도록 ‘첫 컬럼=범주, 마지막 컬럼=값’ 방식으로 자동 매핑합니다.")
