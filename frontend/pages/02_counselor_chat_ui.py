import time
import random
import streamlit as st
from typing import List, Dict, Any

from common_ui import (
    api_health_check_or_stop,
    api_get,
    api_post,
    api_json_or_show_error,
)

# --------------------------------
# Page config
# --------------------------------
st.set_page_config(page_title="MindWay · Counselor", page_icon=None, layout="wide")

# --------------------------------
# Styles (Minimal, product-like) + Camera/Emoji Bar add-ons
# --------------------------------
st.markdown(
    """
    <style>
      html, body, [class*="css"]{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      .mw-topbar{
        position: sticky; top:0; z-index:999;
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(8px);
        padding: 14px 0 12px 0;
        border-bottom: 1px solid #f0f0f0;
      }
      .mw-title{
        text-align:center; font-size: 20px; font-weight: 950;
        letter-spacing: -0.2px; color:#111827; margin: 0;
      }
      .mw-sub{
        text-align:center; font-size: 12px; color:#6b7280; margin-top: 4px;
        font-weight: 650;
      }

      .mw-wrap{max-width: 1100px; margin: 0 auto; padding: 16px 12px 120px 12px;}
      .row{display:flex; margin: 10px 0; width: 100%;}
      .left{justify-content:flex-start;}  /* client */
      .right{justify-content:flex-end;}   /* counselor */

      .bubble{
        padding: 12px 14px; border-radius: 16px;
        max-width: 74%; word-break: break-word;
        font-size: 15px; line-height: 1.45;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        border: 1px solid rgba(17,24,39,0.06);
      }
      .bub-counselor{background:#111827; color:white; border: 1px solid rgba(17,24,39,0.30);}
      .bub-client{background:#f9fafb; color:#111827;}

      .name{ font-size: 12px; color:#6b7280; font-weight: 850; margin: 0 2px 4px 2px; }
      .meta{ font-size: 11px; color:#9ca3af; margin-top: 4px; }

      /* Right panel cards */
      .card{
        border: 1px solid #eee; border-radius: 14px;
        padding: 12px; background: rgba(255,255,255,0.95);
        margin-bottom: 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      }
      .card-title{ font-weight: 950; margin-bottom: 10px; font-size: 13px; color:#111827; }
      .badge{
        display:inline-block; padding: 5px 10px; border-radius: 999px;
        background:#f3f4f6; font-size: 12px; color:#374151; font-weight: 800;
      }
      .muted{ color:#6b7280; font-size: 12px; font-weight: 600; }

      /* Bottom input bar */
      .mw-inputbar{
        position: fixed; left: 50%; transform: translateX(-50%);
        bottom: 16px; width: min(820px, calc(100vw - 36px));
        background: rgba(255,255,255,0.94);
        backdrop-filter: blur(8px);
        border: 1px solid #e5e7eb;
        border-radius: 22px;
        padding: 10px 12px 10px 12px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.10);
        z-index: 1000;
      }

      /* TextInput */
      div[data-testid="stTextInput"] input{
        border-radius: 16px !important;
        border: 1px solid #e5e7eb !important;
        padding: 12px 12px !important;
        height: 44px !important;
        background: white !important;
      }
      div[data-testid="stTextInput"] label{ display:none !important; }

      /* --- Camera preview mock (right panel) --- */
      .mw-cam{
        width: 100%;
        aspect-ratio: 16 / 9;
        border-radius: 12px;
        background: linear-gradient(135deg, #0b1220, #111827);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
      }
      .mw-cam::after{
        content:"";
        position:absolute; inset:-40%;
        background: radial-gradient(circle at 30% 30%, rgba(59,130,246,0.28), transparent 55%),
                    radial-gradient(circle at 70% 60%, rgba(236,72,153,0.18), transparent 58%),
                    radial-gradient(circle at 40% 80%, rgba(34,197,94,0.15), transparent 60%);
        transform: rotate(8deg);
      }
      .mw-live{
        position:absolute; top:10px; left:10px;
        display:flex; align-items:center; gap:8px;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(0,0,0,0.45);
        color: white;
        font-size: 11px;
        font-weight: 800;
        z-index: 2;
      }
      .mw-dot{
        width:8px; height:8px; border-radius:999px;
        background:#ef4444;
        box-shadow:0 0 0 3px rgba(239,68,68,0.18);
      }
      .mw-cam-hint{
        position:absolute; inset:0;
        display:flex; align-items:center; justify-content:center;
        color: rgba(255,255,255,0.70);
        font-size: 12px;
        font-weight: 700;
        z-index: 2;
        text-align:center;
        padding: 0 16px;
      }

      /* --- Emoji score bar --- */
      .mw-emo-row{
        display:flex;
        gap:10px;
        align-items:center;
        justify-content:space-between;
        margin-top: 10px;
        padding: 10px 10px;
        border-radius: 12px;
        background: #0b1220;
        border: 1px solid rgba(17,24,39,0.10);
      }
      .mw-emo-left{
        display:flex; align-items:center; gap:10px;
        color:white;
      }
      .mw-emo-emoji{
        font-size: 26px;
        line-height: 1;
      }
      .mw-emo-text{
        display:flex; flex-direction:column; gap:2px;
      }
      .mw-emo-label{
        font-size: 12px; font-weight: 900; color: rgba(255,255,255,0.92);
      }
      .mw-emo-sub{
        font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.55);
      }
      .mw-emo-score{
        font-size: 16px;
        font-weight: 950;
        color: white;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.10);
        min-width: 68px;
        text-align:center;
      }

      .mw-mini-note{
        font-size: 11px;
        color: #9ca3af;
        font-weight: 650;
        margin-top: 8px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="mw-topbar">
      <div class="mw-title">MindWay</div>
      <div class="mw-sub">상담사 집중 관제 모드 · 실시간 AI 보조</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------
# API health (호환형 호출)
# --------------------------------
try:
    api_health_check_or_stop(show_success=False)
except TypeError:
    api_health_check_or_stop()

# --------------------------------
# Helpers
# --------------------------------
def fmt_time(x):
    if not x:
        return ""
    return str(x).replace("T", " ")[:19]

def last_client_text(msgs: List[Dict[str, Any]]) -> str:
    for m in reversed(msgs):
        if (m.get("speaker") or "").upper() == "CLIENT":
            t = (m.get("text") or "").strip()
            if t:
                return t
    return ""

def last_counselor_text(msgs: List[Dict[str, Any]]) -> str:
    for m in reversed(msgs):
        if (m.get("speaker") or "").upper() == "COUNSELOR":
            t = (m.get("text") or "").strip()
            if t:
                return t
    return ""

def coach_tip(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "내담자 발화가 아직 없어요. 먼저 라포 형성을 위해 짧게 인사/상황 확인을 진행해보세요."
    if any(k in t for k in ["그만", "포기", "싫어", "힘들", "못하겠", "안 할래"]):
        return (
            "① 공감: “정말 힘드셨겠어요.”\n"
            "② 구체화: “지금 가장 힘든 부분이 무엇인지 한 가지만 말해주실래요?”\n"
            "③ 안정화: “잠깐 호흡을 같이 맞춰볼까요?”\n"
            "④ 확인: “지금 안전한 곳에 계신가요?”"
        )
    if any(k in t for k in ["불안", "걱정", "무서", "떨려"]):
        return (
            "① 공감: “지금 불안이 크게 느껴지시는군요.”\n"
            "② 범위 좁히기: “불안이 0~10이면 지금 몇 정도일까요?”\n"
            "③ 대처: “최근에 도움이 됐던 행동이 있었나요?”"
        )
    return (
        "① 공감 → ② 구체화 질문 → ③ 다음 행동 제안 순서로 진행해보세요.\n"
        "예: “그 상황에서 어떤 생각이 가장 먼저 들었나요?”"
    )

def deepface_demo_result() -> Dict[str, Any]:
    options = [
        {"emo": "안정", "emoji": "🙂", "score": 0.83, "hint": "표정이 안정적입니다."},
        {"emo": "불안", "emoji": "😟", "score": 0.74, "hint": "불안 신호가 감지됩니다."},
        {"emo": "우울", "emoji": "😢", "score": 0.69, "hint": "감정 저하 가능성이 있습니다."},
        {"emo": "분노", "emoji": "😠", "score": 0.62, "hint": "긴장/방어 반응이 보입니다."},
    ]
    return random.choice(options)

def helper_suggestion(sess_id: int, counselor_id: int, msgs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    /helper/suggestion 호출
    - 성공하면 {"mode": "...", "suggestion": "..."}
    - 실패하면 {"mode": "ERROR", "suggestion": "..."}
    """
    payload = {
        "sess_id": int(sess_id),
        "counselor_id": int(counselor_id),
        "last_client_text": last_client_text(msgs),
        "last_counselor_text": last_counselor_text(msgs),
        "context": {}
    }

    try:
        r = api_post("/helper/suggestion", json=payload)
        if not r.ok:
            return {"mode": "ERROR", "suggestion": f"헬퍼 호출 실패: {r.status_code}"}
        data = r.json() if r.text else {}
        return {
            "mode": data.get("mode", "RULE"),
            "suggestion": data.get("suggestion", "") or "응답이 비어있습니다."
        }
    except Exception as e:
        return {"mode": "ERROR", "suggestion": f"헬퍼 호출 예외: {e}"}

# --------------------------------
# Sidebar settings
# --------------------------------
with st.sidebar:
    st.markdown("### 🧑‍⚕️ 상담사 설정")
    counselor_id = st.number_input("상담사 ID", min_value=1, value=1)

    st.divider()
    st.markdown("### 🔒 동의/기능")
    consent_face = st.toggle("내담자 동의: 표정 분석 사용", value=False)
    demo_deepface = st.toggle("DeepFace 데모 모드(권장)", value=True)

    st.divider()
    st.markdown("### 🔄 실시간 동기화")
    auto_refresh = st.toggle("자동 새로고침", value=False)
    refresh_sec = st.slider("새로고침 주기(초)", 2, 8, 3)

# --------------------------------
# Session selection
# --------------------------------
sess_r = api_get("/sessions", params={"limit": 50})
sess_data = api_json_or_show_error(sess_r, title="/sessions 호출 실패")
sessions = sess_data.get("items", [])

if not sessions:
    st.warning("진행 중인 상담 세션이 없습니다. (seed 데이터 필요)")
    st.stop()

sess_ids = sorted([s.get("id") for s in sessions if s.get("id") is not None], reverse=True)
sess_id = st.selectbox("현재 상담 세션 선택", sess_ids, index=0)

# --------------------------------
# Load messages
# --------------------------------
msgs_r = api_get(f"/sessions/{sess_id}/messages", params={"limit": 300})
msgs_data = api_json_or_show_error(msgs_r, title="메시지 조회 실패")
msgs = msgs_data.get("items", [])

# --------------------------------
# Layout: Chat | Panels
# --------------------------------
left, right = st.columns([2.3, 1])

with left:
    st.markdown("<div class='mw-wrap'>", unsafe_allow_html=True)

    for m in msgs:
        speaker = (m.get("speaker") or "").upper()
        text = (m.get("text") or "").strip()
        at = fmt_time(m.get("at"))

        if not text and speaker != "SYSTEM":
            continue

        if speaker == "COUNSELOR":
            st.markdown(
                f"""
                <div class="row right">
                  <div style="text-align:right;">
                    <div class="name">상담사</div>
                    <div class="bubble bub-counselor">{text}</div>
                    <div class="meta">{at}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif speaker == "CLIENT":
            st.markdown(
                f"""
                <div class="row left">
                  <div>
                    <div class="name">내담자</div>
                    <div class="bubble bub-client">{text}</div>
                    <div class="meta">{at}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="row left">
                  <div>
                    <div class="name">SYSTEM</div>
                    <div class="bubble bub-client">{text}</div>
                    <div class="meta">{at}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    # -------------------------
    # 1) Consent & Face Analysis
    # -------------------------
    st.markdown("<div class='card'><div class='card-title'>표정 분석 (동의 기반)</div>", unsafe_allow_html=True)

    if not consent_face:
        st.markdown("<div class='muted'>내담자 동의가 없어 표정 분석이 비활성화되었습니다.</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="mw-cam" style="opacity:0.55;">
              <div class="mw-live"><span class="mw-dot"></span> CAMERA</div>
              <div class="mw-cam-hint">동의가 필요합니다<br/>내담자 동의 토글을 켜면 활성화됩니다</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)
        result = None
    else:
        st.markdown("<div class='muted'>데모에서는 이미지 업로드로 분석을 시연합니다.</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="mw-cam">
              <div class="mw-live"><span class="mw-dot"></span> LIVE</div>
              <div class="mw-cam-hint">카메라 스트림 전송 중…<br/>※ 데모: 아래 이미지 업로드로 대체</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        img = st.file_uploader("내담자 얼굴 이미지 업로드", type=["jpg", "jpeg", "png"])

        result = None
        if img:
            st.image(img, use_container_width=True)

            if demo_deepface:
                result = deepface_demo_result()
            else:
                try:
                    from deepface import DeepFace  # type: ignore
                    analysis = DeepFace.analyze(img.getvalue(), actions=["emotion"], enforce_detection=False)
                    if isinstance(analysis, list) and analysis:
                        analysis = analysis[0]

                    emo = "unknown"
                    score = None
                    if isinstance(analysis, dict):
                        emo = (analysis.get("dominant_emotion") or "unknown")
                        emod = analysis.get("emotion", {}) or {}
                        if isinstance(emod, dict):
                            score = emod.get(emo, None)

                    if score is None:
                        result = {"emo": emo, "emoji": "🙂", "score": 0.50, "hint": "분석 결과(점수 없음)"}
                    else:
                        result = {"emo": emo, "emoji": "🙂", "score": float(score) / 100.0, "hint": "분석 완료"}
                except Exception:
                    result = {"emo": "실패", "emoji": "⚠️", "score": 0.00, "hint": "DeepFace 미설치/오류 → 데모 모드 권장"}

        if result:
            st.markdown(
                f"""
                <div class="mw-emo-row">
                  <div class="mw-emo-left">
                    <div class="mw-emo-emoji">{result["emoji"]}</div>
                    <div class="mw-emo-text">
                      <div class="mw-emo-label">{result["emo"]}</div>
                      <div class="mw-emo-sub">{result.get("hint","")}</div>
                    </div>
                  </div>
                  <div class="mw-emo-score">{result["score"]:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="mw-emo-row" style="opacity:0.85;">
                  <div class="mw-emo-left">
                    <div class="mw-emo-emoji">🙂</div>
                    <div class="mw-emo-text">
                      <div class="mw-emo-label">표정 분석 대기</div>
                      <div class="mw-emo-sub">이미지를 업로드하면 점수가 표시됩니다</div>
                    </div>
                  </div>
                  <div class="mw-emo-score">--</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<div class='mw-mini-note'>※ 실제 카메라 스트림 연동은 WebRTC/별도 모듈로 연결 가능합니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # 2) AI Helper (헬퍼 연동 + fallback 유지)
    # -------------------------
    st.markdown("<div class='card'><div class='card-title'>AI 헬퍼 · 개입 전략</div>", unsafe_allow_html=True)

    h = helper_suggestion(sess_id=int(sess_id), counselor_id=int(counselor_id), msgs=msgs)
    mode = h.get("mode", "RULE")
    suggestion = h.get("suggestion", "")

    # 헬퍼 실패 시: 기존 룰 기반 코칭으로 fallback
    if mode == "ERROR":
        st.warning(suggestion)
        lc = last_client_text(msgs)
        st.info(coach_tip(lc))
    else:
        # 정상
        st.caption(f"mode: {mode}")
        st.info(suggestion)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # 3) Alerts panel (optional)
    # -------------------------
    try:
        a_r = api_get(f"/sessions/{sess_id}/alerts")
        if a_r.ok:
            a = a_r.json().get("items", [])
            st.markdown("<div class='card'><div class='card-title'>최근 알림</div>", unsafe_allow_html=True)
            if not a:
                st.caption("알림 없음")
            else:
                import pandas as pd
                df_a = pd.DataFrame(a)
                keep = [c for c in ["at", "type", "status", "score", "rule"] if c in df_a.columns]
                st.dataframe(df_a[keep], use_container_width=True, height=220)
            st.markdown("</div>", unsafe_allow_html=True)
    except Exception:
        pass

# --------------------------------
# Bottom input bar (Counselor send)
# --------------------------------
st.markdown('<div class="mw-inputbar">', unsafe_allow_html=True)

with st.form("send_form", clear_on_submit=True):
    counselor_text = st.text_input("message", placeholder="상담사 메시지를 입력하세요", label_visibility="collapsed")
    sent = st.form_submit_button("전송", use_container_width=True)

if sent:
    text = (counselor_text or "").strip()
    if not text:
        st.warning("메시지를 입력하세요.")
        st.stop()

    payload = {
        "sess_id": int(sess_id),
        "speaker": "COUNSELOR",
        "speaker_id": int(counselor_id),
        "text": text,
        "stt_conf": 1.0,
    }
    resp = api_post("/messages", json=payload)
    if resp.ok:
        st.rerun()
    else:
        st.error(f"전송 실패: {resp.status_code}")
        st.code(resp.text)

st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------
# Auto refresh (optional)
# --------------------------------
if auto_refresh:
    time.sleep(int(refresh_sec))
    st.rerun()