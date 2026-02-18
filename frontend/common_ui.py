# frontend/common_ui.py
import os
import time
import requests
import streamlit as st
from typing import Any, Dict, Optional

# =========================================================
# API Base
# - 환경변수 FRONTEND_API_URL 우선
# - 없으면 로컬 FastAPI
# =========================================================
def get_api_base() -> str:
    return os.getenv("FRONTEND_API_URL", "http://127.0.0.1:8000").rstrip("/")


# =========================================================
# Low-level HTTP
# =========================================================
def api_get(path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 6) -> requests.Response:
    base = get_api_base()
    url = f"{base}{path}"
    return requests.get(url, params=params, timeout=timeout)


def api_post(path: str, json: Optional[Dict[str, Any]] = None, timeout: int = 10) -> requests.Response:
    base = get_api_base()
    url = f"{base}{path}"
    return requests.post(url, json=json, timeout=timeout)


# =========================================================
# Response Helpers
# =========================================================
def api_json_or_show_error(resp: Optional[requests.Response], title: str = "API 오류") -> Dict[str, Any]:
    """
    - resp가 None이거나 ok가 아니면 화면에 에러 출력 후 stop()
    - ok면 json 반환
    """
    if resp is None:
        st.error(f"{title}: 응답이 없습니다.")
        st.stop()

    if not resp.ok:
        st.error(f"{title}: {resp.status_code}")
        try:
            st.code(resp.text)
        except Exception:
            st.write(resp)
        st.stop()

    try:
        return resp.json()
    except Exception as e:
        st.error(f"{title}: JSON 파싱 실패 ({e})")
        st.code(resp.text)
        st.stop()


def api_ok_or_show_error(resp: Optional[requests.Response], title: str = "API 오류") -> None:
    """
    ok 여부만 검사하고, 실패면 출력 후 stop()
    """
    if resp is None:
        st.error(f"{title}: 응답이 없습니다.")
        st.stop()
    if not resp.ok:
        st.error(f"{title}: {resp.status_code}")
        st.code(resp.text)
        st.stop()


# =========================================================
# Health Check (Table Driven)
# =========================================================
def api_health_check_or_stop(show_success: bool = True):
    """
    백엔드 연결/DB(counseling_db) 연결 확인.
    - 실패하면 stop()
    """
    try:
        # 명세서 및 스냅샷에 정의된 기본 헬스체크 엔드포인트 호출
        r = api_get("/health/db", timeout=3)
        if not r.ok:
            st.error(f"API/Database 연결 실패: {r.status_code}")
            st.code(r.text)
            st.stop()

        if show_success:
            st.success(f"MindWay 시스템 연결 완료 (DB: counseling_db)")
        return r.json()

    except Exception as e:
        st.error(f"API 서버 연결 실패: {e}")
        st.stop()


# =========================================================
# Session Picker (sess Table 기반)
# =========================================================
@st.cache_data(ttl=3)  # 실시간 상담 분석을 위해 캐시 주기를 짧게 유지
def _fetch_sessions(limit: int = 200) -> Dict[str, Any]:
    # sess 테이블의 최신 레코드를 가져옵니다 [cite: 60, 120]
    r = api_get("/sessions", params={"limit": limit}, timeout=6)
    return api_json_or_show_error(r, title="/sessions 호출 실패")


def pick_session_id(default_id: int = 1, limit: int = 200) -> int:
    """
    상담 세션(sess) 목록이 있으면 selectbox, 없으면 수동 입력.
    """
    data = _fetch_sessions(limit=limit)
    items = data.get("items", [])

    if not items:
        # 명세서 기반 테이블 데이터 누락 안내
        st.warning("등록된 상담 세션(sess)이 없습니다. seed.sql을 먼저 실행해주세요.")
        sid = st.number_input("sess_id 수동 입력", min_value=1, value=default_id, step=1)
        return int(sid)

    # 명세서의 PK 컬럼인 id 추출 [cite: 60, 66]
    ids = [x.get("id") for x in items if x.get("id") is not None]
    if not ids:
        sid = st.number_input("sess_id 수동 입력", min_value=1, value=default_id, step=1)
        return int(sid)

    # 상담사가 최신 세션을 찾기 쉽도록 내림차순 정렬
    ids = sorted(ids, reverse=True)
    sid = st.selectbox("분석 및 관리 세션 선택 (sess_id)", ids, index=0)
    return int(sid)


# =========================================================
# Optional: Auto refresh helper
# =========================================================
def auto_refresh(seconds: int = 2, enabled: bool = False):
    """
    이탈 신호(alert) 실시간 감지를 위한 페이지 새로고침 도구. [cite: 259]
    """
    if not enabled:
        return
    time.sleep(max(1, int(seconds)))
    st.rerun()