import streamlit as st
import requests
from common_ui import api_health_check_or_stop

# 테이블 명세서 기반 MindWay 프로젝트 메인 랜딩 설정
st.set_page_config(
    page_title="MindWay",
    page_icon=None,   # 이모지 제거: 실무형/분석 시스템 지향
    layout="wide"
)

# -------------------------
# 🎨 Styles (MindWay Brand Identity)
# -------------------------
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.center-wrap {
    height: 80vh;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    text-align: center;
}

.title {
    font-size: 72px;
    font-weight: 900;
    letter-spacing: -2px;
    color: #111827;
    margin-bottom: 8px;
}

.subtitle {
    font-size: 22px;
    color: #4b5563;
    font-weight: 500;
    margin-bottom: 48px;
    line-height: 1.6;
}

.badge {
    font-size: 14px;
    padding: 8px 18px;
    border-radius: 999px;
    background: #f3f4f6;
    color: #374151;
    font-weight: 700;
    margin-bottom: 24px;
    border: 1px solid #e5e7eb;
}

.footer {
    position: fixed;
    bottom: 20px;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 13px;
    color: #9ca3af;
    font-weight: 500;
}

/* 버튼이나 링크가 필요한 경우를 대비한 힌트 */
.hint {
    font-size: 14px;
    color: #6366f1;
    font-weight: 600;
    text-decoration: none;
}
</style>

<div class="center-wrap">
    <div class="badge">MindWay Counseling Intelligence System</div>
    <div class="title">MindWay</div>
    <div class="subtitle">
        상담 이탈 직전 신호 탐지 및 품질 분석을 위한<br>
        데이터 기반 의사결정 보조 인터페이스
    </div>
    <div class="hint">← 왼쪽 사이드바에서 메뉴를 선택하여 시작하세요</div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# 📡 API/DB Health Check (Table Driven)
# -------------------------
# 명세서와 스냅샷에 정의된 DB 연결 상태 확인 API 호출
try:
    # db.py의 SessionLocal 연결 상태를 확인하는 엔드포인트
    r = requests.get("http://127.0.0.1:8000/health/db", timeout=2)
    if r.ok and r.json().get("db") == "ok":
        st.markdown('<div class="footer">● API & Database (counseling_db) Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="footer" style="color:#ef4444;">● Database Connection Error</div>', unsafe_allow_html=True)
except Exception:
    st.markdown('<div class="footer" style="color:#ef4444;">● API Server Disconnected</div>', unsafe_allow_html=True)