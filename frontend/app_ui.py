import streamlit as st
import requests
from common_ui import api_health_check_or_stop

st.set_page_config(
    page_title="MindWay",
    page_icon=None,   # ← 이모지 제거 (중요)
    layout="wide"
)

# -------------------------
# 🎨 Minimal / 실무형 랜딩 스타일
# -------------------------
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.center-wrap {
    height: 82vh;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    text-align: center;
}

.title {
    font-size: 64px;
    font-weight: 900;
    letter-spacing: -1px;
    color: #111827;
    margin-bottom: 12px;
}

.subtitle {
    font-size: 20px;
    color: #6b7280;
    font-weight: 500;
    margin-bottom: 40px;
}

.badge {
    font-size: 13px;
    padding: 6px 14px;
    border-radius: 999px;
    background: #f3f4f6;
    color: #374151;
    font-weight: 600;
    margin-bottom: 16px;
}

.footer {
    text-align: center;
    font-size: 12px;
    color: #9ca3af;
    padding-bottom: 10px;
}
</style>

<div class="center-wrap">
    <div class="badge">MindWay Counseling Intelligence</div>
    <div class="title">MindWay</div>
    <div class="subtitle">
        이탈 직전 신호 탐지 · 상담 품질 분석 · 의사결정 보조
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# API 상태 체크
# -------------------------
try:
    r = requests.get("http://127.0.0.1:8000/health/db", timeout=2)
    if r.ok:
        st.markdown('<div class="footer">✅ API 연결 정상</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="footer">⚠️ API 응답 오류</div>', unsafe_allow_html=True)
except:
    st.markdown('<div class="footer">❌ API 서버 연결 실패</div>', unsafe_allow_html=True)
