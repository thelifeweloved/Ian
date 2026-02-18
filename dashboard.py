import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 명세서 기반 API 엔드포인트 설정
API = "http://127.0.0.1:8000"

st.set_page_config(page_title="Mindway Dashboard", layout="wide")
st.title("🧠 Mindway 상담 대시보드")

# -------------------------
# Health check
# -------------------------
try:
    health = requests.get(f"{API}/health/db", timeout=3)
    st.success(f"API 연결 OK: {health.json()}")
except Exception as e:
    st.error(f"API 연결 실패: {e}")
    st.stop()

# 상담사 ID 입력 (counselor 테이블 기반) [cite: 11]
cid = st.number_input("상담사 ID", min_value=1, value=1)

# -------------------------
# 오늘 예약 리스트 (appt + client 테이블 기반)
# -------------------------
st.subheader("📅 오늘 예약 상담 (appt)")

# 백엔드 경로 /appointments?counselor_id=X 에 맞춰 수정
appt_resp = requests.get(f"{API}/appointments", params={"counselor_id": cid})

if appt_resp.status_code == 200:
    appts = appt_resp.json().get("items", [])
    if len(appts) == 0:
        st.info("오늘 배정된 예약이 없습니다.")
    else:
        # 명세서의 appt(id, at, status)와 client(name, status) 데이터 출력 [cite: 7, 14, 43]
        df_appt = pd.DataFrame(appts)
        st.dataframe(df_appt, use_container_width=True)
else:
    st.warning(f"예약 API를 불러올 수 없습니다 (Error: {appt_resp.status_code})")

st.divider()

# -------------------------
# 세션 목록 (sess 테이블 기반)
# -------------------------
st.subheader("📋 세션 목록 (sess)")

sess_res = requests.get(f"{API}/sessions?limit=50").json()
sessions = sess_res.get("items", [])
count = sess_res.get("count", 0)

if count == 0:
    st.warning("세션 데이터가 없습니다. DB Seed를 확인해주세요.")
    st.stop()

df = pd.DataFrame(sessions)
st.dataframe(df, use_container_width=True)

# 세션 선택 (FK 참조를 위한 sess.id) [cite: 60]
sess_id = st.selectbox("분석할 세션 선택", df["id"].tolist())

# -------------------------
# 세션 대시보드
# -------------------------
st.subheader("📌 세션 상세 대시보드")

dash = requests.get(f"{API}/sessions/{sess_id}/dashboard").json()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 세션 정보 (sess)")
    st.json(dash.get("session", {}))

with col2:
    # alert 테이블의 score 평균값으로 계산된 Risk Score [cite: 259]
    st.markdown("### Risk Score")
    st.metric("이탈 위험도", dash.get("risk_score", 0.0))

st.divider()

# -------------------------
# 상담 시뮬레이터 (msg + alert 테이블 연동)
# -------------------------
st.subheader("💬 상담 시뮬레이터 (Real-time Detection)")

# 명세서 ENUM: COUNSELOR, CLIENT, SYSTEM [cite: 125, 134]
speaker = st.radio("발화자 선택", ["CLIENT", "COUNSELOR", "SYSTEM"], horizontal=True)
speaker_id = st.number_input("발화자 고유 ID (speaker_id)", min_value=1, value=1)

if speaker == "SYSTEM":
    speaker_id = None

text = st.text_area("내담자 또는 상담사 메시지 입력")

if st.button("메시지 전송 및 분석"):
    payload = {
        "sess_id": int(sess_id),
        "speaker": speaker,
        "speaker_id": speaker_id,
        "text": text,
        "stt_conf": 0.95 # HyperCLOVA Speech 신뢰도 가정 [cite: 144]
    }

    resp = requests.post(f"{API}/messages", json=payload)

    if resp.ok:
        st.success("메시지가 msg 테이블에 저장되었으며 이탈 신호를 분석했습니다.")
        st.rerun()
    else:
        st.error(f"저장 실패: {resp.text}")

st.divider()

# -------------------------
# 대화 / 알림 내역
# -------------------------
col3, col4 = st.columns(2)

with col3:
    st.markdown("### 대화 기록 로그 (msg)")
    msgs = requests.get(f"{API}/sessions/{sess_id}/messages?limit=200").json().get("items", [])
    if len(msgs) == 0:
        st.info("기록된 대화가 없습니다.")
    else:
        st.dataframe(pd.DataFrame(msgs), use_container_width=True)

with col4:
    # alert 테이블 기반 이탈 신호 [cite: 259]
    st.markdown("### 탐지된 이탈 신호 (alert)")
    alerts = requests.get(f"{API}/sessions/{sess_id}/alerts").json().get("items", [])
    if len(alerts) == 0:
        st.info("탐지된 위험 신호가 없습니다.")
    else:
        st.dataframe(pd.DataFrame(alerts), use_container_width=True)

st.divider()

# -------------------------
# 사후 분석 기능 영역 (명세서 기반 통계)
# -------------------------
st.header("📊 사후 분석 리포트 (통계)")

def show_analysis(title, url):
    st.markdown(f"#### {title}")
    r = requests.get(url)
    if r.status_code == 200:
        items = r.json().get("items", [])
        if len(items) == 0:
            st.info("분석할 데이터가 부족합니다.")
        else:
            st.dataframe(pd.DataFrame(items), use_container_width=True)
    else:
        st.error(f"통계 API 호출 실패 (상태 코드: {r.status_code})")

# 명세서 비고란의 '이탈 직전 신호 분석' 목적 반영 [cite: 372]
show_analysis("주제별 이탈률 (topic)", f"{API}/stats/topic-dropout?counselor_id={cid}")
show_analysis("내담자 등급별 이탈 분포 (client.status)", f"{API}/stats/client-grade-dropout?counselor_id={cid}")
show_analysis("탐지 실패 세션 (Missed Alerts)", f"{API}/stats/missed-alerts?counselor_id={cid}")
show_analysis("시간대별 이탈 패턴", f"{API}/stats/time-dropout?counselor_id={cid}")
show_analysis("채널별 이탈 비교 (CHAT vs VOICE)", f"{API}/stats/channel-dropout?counselor_id={cid}")
show_analysis("세션 품질 점수 추이 (quality)", f"{API}/stats/quality-trend?counselor_id={cid}")

st.caption(f"MindWay Analytics System | Data Source: counseling_db | Spec: 2026.02.14")