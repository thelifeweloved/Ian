import streamlit as st
from common_ui import api_health_check_or_stop, api_get, api_post, api_json_or_show_error

st.set_page_config(page_title="MindWay · Client", page_icon=None, layout="wide")

# -------------------------
# 스타일 (실무 UX 안정형)
# -------------------------
st.markdown("""
<style>
.mw-title{
    text-align:center;
    font-size:24px;
    font-weight:900;
    margin-bottom:12px;
}

.mw-wrap{
    max-width:820px;
    margin:0 auto;
    padding-bottom:120px;
}

.row{display:flex; margin:10px 0;}
.left{justify-content:flex-start;}
.right{justify-content:flex-end;}

.name{
    font-size:12px;
    font-weight:800;
    margin-bottom:4px;
    opacity:0.6;
}

.time{
    font-size:11px;
    opacity:0.4;
    margin-top:3px;
}

.bubble{
    padding:10px 14px;
    border-radius:14px;
    max-width:70%;
    font-size:15px;
    line-height:1.4;
}

.client{
    background:#111827;
    color:white;
}

.counselor{
    background:#f3f4f6;
    color:#111827;
}

.input-wrap{
    position:fixed;
    bottom:15px;
    left:50%;
    transform:translateX(-50%);
    width:min(820px, calc(100vw - 40px));
    background:white;
    border:1px solid #e5e7eb;
    border-radius:18px;
    padding:10px;
    box-shadow:0 10px 25px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="mw-title">MindWay</div>', unsafe_allow_html=True)

api_health_check_or_stop(show_success=False)

# -------------------------
# 상담 방식 선택 (핵심 UI)
# -------------------------
mode = st.radio("상담 방식", ["CHAT", "VOICE"], horizontal=True)

if mode == "VOICE":
    st.caption("🎤 음성 상담 모드")

# -------------------------
# 세션 자동 선택
# -------------------------
if "client_sess_id" not in st.session_state:
    r = api_get("/sessions", params={"limit": 1})
    data = api_json_or_show_error(r)
    items = data.get("items", [])
    st.session_state.client_sess_id = items[0]["id"] if items else None

sess_id = st.session_state.client_sess_id

if not sess_id:
    st.warning("상담 세션 없음")
    st.stop()

# -------------------------
# 메시지 로드
# -------------------------
msgs_r = api_get(f"/sessions/{sess_id}/messages", params={"limit": 300})
msgs = api_json_or_show_error(msgs_r).get("items", [])

def fmt_time(x):
    if not x:
        return ""
    return str(x).replace("T", " ")[:19]

# -------------------------
# 메시지 렌더링
# -------------------------
st.markdown('<div class="mw-wrap">', unsafe_allow_html=True)

for m in msgs:
    speaker = (m.get("speaker") or "").upper()
    text = m.get("text") or ""
    at = fmt_time(m.get("at"))

    if speaker == "CLIENT":
        st.markdown(f"""
        <div class="row right">
            <div>
                <div class="name">내담자</div>
                <div class="bubble client">{text}</div>
                <div class="time">{at}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="row left">
            <div>
                <div class="name">상담사</div>
                <div class="bubble counselor">{text}</div>
                <div class="time">{at}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 입력 바 (마이크 포함)
# -------------------------
st.markdown('<div class="input-wrap">', unsafe_allow_html=True)

with st.form("send_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])

    with col1:
        user_text = st.text_input("msg", placeholder="메시지를 입력하세요", label_visibility="collapsed")

    with col2:
        if mode == "VOICE":
            st.markdown("🎤", help="음성 입력 모드")
        sent = st.form_submit_button("전송")

if sent and user_text.strip():

    payload = {
        "sess_id": int(sess_id),
        "speaker": "CLIENT",
        "speaker_id": 1,
        "text": user_text,
        "stt_conf": 0.9 if mode == "VOICE" else 1.0
    }

    r = api_post("/messages", json=payload)

    if r.ok:
        st.rerun()
    else:
        st.error("전송 실패")

st.markdown("</div>", unsafe_allow_html=True)
