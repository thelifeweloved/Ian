import os
import json
import requests
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/helper", tags=["helper"])

# =========================================================
# Request
# =========================================================
class HelperRequest(BaseModel):
    sess_id: int = Field(..., ge=1)
    counselor_id: int = Field(..., ge=1)
    last_client_text: str = ""
    last_counselor_text: str = ""
    context: Optional[Dict[str, Any]] = None

NEG_KEYS = ["그만", "포기", "싫어", "힘들", "못하겠", "안 할래", "의미없"]

def rule_helper(text: str) -> Dict[str, Any]:
    t = (text or "").strip()

    if not t:
        return {"mode": "RULE", "suggestion": "내담자 발화가 없습니다. 라포 형성부터 시작하세요."}

    if any(k in t for k in NEG_KEYS):
        return {
            "mode": "RULE",
            "suggestion": (
                "① 공감: 정말 힘드셨겠어요.\n"
                "② 구체화: 가장 힘든 부분을 한 가지만 말해주실래요?\n"
                "③ 안정화: 잠깐 호흡을 같이 맞춰볼까요?"
            ),
            "risk_hint": "이탈 위험 신호 가능",
        }

    if any(k in t for k in ["불안", "걱정"]):
        return {
            "mode": "RULE",
            "suggestion": (
                "① 공감: 불안이 느껴지시는군요.\n"
                "② 수치화: 0~10 중 몇 정도인가요?"
            ),
        }

    return {"mode": "RULE", "suggestion": "공감 → 구체화 질문 → 다음 행동 제안 순서 권장"}

# =========================================================
# HyperCLOVA X (CLOVA Studio v3 chat-completions, SSE)
# =========================================================
def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

def call_hcx_sse(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    host = _env("HCX_HOST")
    model = _env("HCX_MODEL", "HCX-DASH-002")
    api_key = _env("HCX_API_KEY")
    request_id = _env("HCX_REQUEST_ID", "mindway-helper")
    timeout = int(_env("HCX_TIMEOUT", "20"))

    if not host or not api_key:
        raise RuntimeError("HCX_HOST / HCX_API_KEY 가 비어있습니다. (.env 확인)")

    url = f"{host}/v3/chat-completions/{model}"
    headers = {
        "Authorization": api_key,
        "X-NCP-CLOVASTUDIO-REQUEST-ID": request_id,
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "text/event-stream",
    }

    payload = {
        "messages": messages,
        "topP": float(_env("HCX_TOP_P", "0.8") or 0.8),
        "topK": int(_env("HCX_TOP_K", "0") or 0),
        "maxTokens": int(_env("HCX_MAX_TOKENS", "256") or 256),
        "temperature": float(_env("HCX_TEMPERATURE", "0.5") or 0.5),
        "repetitionPenalty": float(_env("HCX_REP_PENALTY", "1.1") or 1.1),
        "stop": [],
        "seed": int(_env("HCX_SEED", "0") or 0),
        "includeAiFilters": True,
    }

    last_content = ""
    final_content = ""
    last_finish_reason = None

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout) as r:
        if not r.ok:
            raise RuntimeError(f"HCX HTTP 실패: {r.status_code} {r.text}")

        for raw in r.iter_lines(decode_unicode=True):
            if not raw:
                continue

            line = raw.strip()

            # ✅ SSE에서 JSON은 보통 data: 로 시작
            if not line.startswith("data:"):
                # id: / event: 등은 무시
                continue

            data_str = line[len("data:"):].strip()

            # JSON이 아닐 수 있어서 보호
            if not (data_str.startswith("{") and data_str.endswith("}")):
                continue

            try:
                obj = json.loads(data_str)
            except Exception:
                continue

            msg = obj.get("message") or {}
            content = msg.get("content")
            finish = obj.get("finishReason")

            if isinstance(content, str) and content:
                last_content = content

            if finish:
                last_finish_reason = finish

            # ✅ 최종 result(대개 finishReason="stop")면 확정
            if finish == "stop":
                final_content = last_content
                break

    # 혹시 stop이 안 왔으면 마지막 content 사용
    if not final_content:
        final_content = last_content

    return {
        "mode": "HCX",
        "suggestion": final_content.strip(),
        "finishReason": last_finish_reason,
    }

@router.post("/suggestion")
def helper_suggestion(payload: HelperRequest):
    base = rule_helper(payload.last_client_text)

    use_hcx = _env("USE_HCX", "0") == "1"
    if not use_hcx:
        return base

    try:
        system = (
            "너는 상담사를 돕는 '헬퍼'다. "
            "내담자 발화를 바탕으로 상담사가 다음에 말할 문장을 2~3문장으로 제안해라. "
            "공감→구체화 질문→다음 행동 제안 순서로. "
            "진단/처방은 하지 말고, 위기 신호(자해/자살 암시)가 보이면 안전 확인 질문과 전문기관 연결을 우선 제안해라."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"내담자: {payload.last_client_text}\n상담사(직전): {payload.last_counselor_text}".strip()},
        ]
        return call_hcx_sse(messages)

    except Exception as e:
        base["hcx_error"] = str(e)
        return base
