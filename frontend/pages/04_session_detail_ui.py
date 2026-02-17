import streamlit as st
import pandas as pd
import plotly.express as px

from common_ui import (
    api_health_check_or_stop,
    api_get,
    api_json_or_show_error,
    pick_session_id,
)

st.set_page_config(page_title="MindWay · Session Detail", page_icon=None, layout="wide")

st.title("🧾 세션 상세 분석")

api_health_check_or_stop(show_success=False)

# -------------------------
# Session 선택
# -------------------------
sess_id = pick_session_id()

# -------------------------
# 세션 기본 정보
# -------------------------
sess_r = api_get("/sessions", params={"limit": 200})
sess_data = api_json_or_show_error(sess_r)

df_sess = pd.DataFrame(sess_data.get("items", []))

session_row = df_sess[df_sess["id"] == sess_id].iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric("세션 ID", session_row.get("id"))
col2.metric("채널", session_row.get("channel"))
col3.metric("종료 사유", session_row.get("end_reason"))
col4.metric("상태", session_row.get("progress"))

st.caption(f"시작: {session_row.get('start_at')} / 종료: {session_row.get('end_at')}")

st.divider()

# -------------------------
# 메시지 로드
# -------------------------
msg_r = api_get(f"/sessions/{sess_id}/messages", params={"limit": 400})
msg_data = api_json_or_show_error(msg_r, title="메시지 조회 실패")

df_msg = pd.DataFrame(msg_data.get("items", []))

# -------------------------
# 감정 흐름 (있을 때만)
# -------------------------
if "emotion_score" in df_msg.columns:
    st.subheader("📉 감정 변화 흐름")

    fig = px.line(
        df_msg,
        x="at",
        y="emotion_score",
        color="speaker",
        markers=True,
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------------
# 위험 신호 / 알림
# -------------------------
alert_r = api_get(f"/sessions/{sess_id}/alerts")
if alert_r.ok:
    alert_data = alert_r.json()
    df_alert = pd.DataFrame(alert_data.get("items", []))

    st.subheader("🚨 탐지된 위험 신호")

    if df_alert.empty:
        st.success("위험 신호 없음")
    else:
        st.dataframe(df_alert, use_container_width=True)

st.divider()

# -------------------------
# 결정적 순간 탐지 (단순 휴리스틱)
# -------------------------
st.subheader("🎯 결정적 순간 분석")

if not df_msg.empty:

    last_msgs = df_msg.tail(6)

    for _, row in last_msgs.iterrows():
        speaker = row.get("speaker")
        text = row.get("text")

        if not text:
            continue

        if any(k in str(text) for k in ["그만", "힘들", "포기", "싫어"]):
            st.warning(f"위험 발화 감지 가능: {text}")
            break
    else:
        st.info("뚜렷한 위험 발화 패턴 없음")

st.divider()

# -------------------------
# 메시지 복기
# -------------------------
st.subheader("💬 대화 복기")

display_cols = [c for c in ["at", "speaker", "text", "stt_conf"] if c in df_msg.columns]

st.dataframe(df_msg[display_cols], use_container_width=True, height=420)

st.divider()

# -------------------------
# AI 인사이트 패널
# -------------------------
st.subheader("🧠 AI 인사이트")

if session_row.get("end_reason") == "DROPOUT":
    st.info(
        "이 세션은 이탈로 종료되었습니다.\n\n"
        "가능한 원인:\n"
        "- 내담자 부정 감정 표현 증가\n"
        "- 상담 흐름 단절 가능성\n"
        "- 위험 키워드 발화 존재 여부 확인 권장"
    )
else:
    st.success("이탈 세션 아님")
