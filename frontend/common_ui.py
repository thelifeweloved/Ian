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
# Health Check
# =========================================================
def api_health_check_or_stop(show_success: bool = True):
    """
    백엔드 연결/DB 연결 확인.
    - 실패하면 stop()
    """
    try:
        r = api_get("/health/db", timeout=3)
        if not r.ok:
            st.error(f"API 연결 실패: {r.status_code}")
            st.code(r.text)
            st.stop()

        if show_success:
            st.success(f"API 연결 OK: {r.json()}")
        return r.json()

    except Exception as e:
        st.error(f"API 연결 실패: {e}")
        st.stop()


# =========================================================
# Session Picker
# =========================================================
@st.cache_data(ttl=3)  # 너무 오래 캐시하면 최신 세션 반영이 느려서 ttl 짧게
def _fetch_sessions(limit: int = 200) -> Dict[str, Any]:
    r = api_get("/sessions", params={"limit": limit}, timeout=6)
    return api_json_or_show_error(r, title="/sessions 호출 실패")


def pick_session_id(default_id: int = 1, limit: int = 200) -> int:
    """
    세션이 있으면 selectbox, 없으면 입력 받기.
    """
    data = _fetch_sessions(limit=limit)
    items = data.get("items", [])

    if not items:
        st.warning("등록된 세션이 없습니다. seed_min.sql / seed.sql 먼저 실행해주세요.")
        sid = st.number_input("sess_id 입력", min_value=1, value=default_id, step=1)
        return int(sid)

    ids = [x.get("id") for x in items if x.get("id") is not None]
    if not ids:
        sid = st.number_input("sess_id 입력", min_value=1, value=default_id, step=1)
        return int(sid)

    # 최신 세션이 위에 오도록 내림차순 정렬
    ids = sorted(ids, reverse=True)
    sid = st.selectbox("세션 선택", ids, index=0)
    return int(sid)


# =========================================================
# Optional: Auto refresh helper
# =========================================================
def auto_refresh(seconds: int = 2, enabled: bool = False):
    """
    Streamlit 페이지를 일정 간격으로 새로고침.
    - enabled=True일 때만 작동
    """
    if not enabled:
        return
    time.sleep(max(1, int(seconds)))
    st.rerun()
