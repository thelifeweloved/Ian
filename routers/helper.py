"""
helper.py — MindWay AI 헬퍼 모듈 (전체 재설계)
================================================
역할  : 상담사 채팅 화면에서 내담자의 최근 발화(슬라이딩 윈도우)를
        분석하여 상담사의 판단을 돕는 참고 정보와 응답 후보 3개를 제공한다.
구조  : [설정] → [HCX 클라이언트] → [룰 엔진] → [서비스] → [라우터]

주의  : 본 모듈은 상담사의 의사결정을 보조하는 참고 도구이며,
        진단·처방·상담 개입의 주체는 반드시 상담사 본인이다.
        AI는 어떠한 경우에도 상담사의 권한을 대행하거나
        내담자에게 직접 응답하지 않는다.

API키 : HCX_API_KEY는 .env에 순수 키값만 저장. Bearer 조합은 코드에서 처리.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel, Field

load_dotenv(find_dotenv())


# =============================================================
# 1. 설정 — 환경변수 중앙 관리
# =============================================================

class HCXConfig:
    """HyperCLOVA X 연결 설정. .env 값을 한 곳에서 관리한다."""

    host:       str  = os.getenv("HCX_HOST",           "https://clovastudio.stream.ntruss.com").strip()
    model:      str  = os.getenv("HCX_MODEL",           "HCX-DASH-002").strip()
    api_key:    str  = os.getenv("HCX_API_KEY",         "").strip()
    request_id: str  = os.getenv("HCX_REQUEST_ID",      "mindway-helper").strip()
    timeout:    int  = int(os.getenv("HCX_TIMEOUT",     "20") or "20")
    version:    str  = os.getenv("HCX_API_VERSION",     "v3").strip()   # .env 값 활용
    use_hcx:    bool = os.getenv("USE_HCX",             "0").strip() == "1"

    # 분석에 사용할 최근 발화 개수 (기본 5개, .env의 HCX_HISTORY_WINDOW로 조정 가능)
    history_window: int = int(os.getenv("HCX_HISTORY_WINDOW", "5") or "5")

    @classmethod
    def endpoint(cls) -> str:
        """실제 호출 URL을 조합하여 반환"""
        return f"{cls.host}/{cls.version}/chat-completions/{cls.model}"

    @classmethod
    def auth_header(cls) -> str:
        """
        .env에 순수 키값만 저장하는 규칙을 지원한다.
        이미 'Bearer '가 포함된 경우 그대로, 아니면 자동으로 조합한다.
        """
        key = cls.api_key
        if not key:
            raise RuntimeError(
                "HCX_API_KEY가 비어 있습니다. .env 파일을 확인하세요."
            )
        if key.lower().startswith("bearer "):
            return key
        return f"Bearer {key}"


# =============================================================
# 2. 시스템 프롬프트
# =============================================================

SYSTEM_PROMPT = """
너는 심리상담사의 의사결정을 실시간으로 보조하는 'AI 헬퍼'다.
너는 상담사 대신 말하거나 내담자에게 직접 답하지 않는다.
너는 상담사가 다음 개입을 결정할 수 있도록 분석 정보를 제공한다.

[절대 규칙]
- 출력은 반드시 JSON 한 줄만. (설명/문장/마크다운/코드블록 금지)
- JSON은 반드시 파싱 가능해야 한다. 따옴표/쉼표 누락 금지.
- 필수 키: insight, emotions, intent, risk, suggestions (누락 금지)
- emotions는 문자열 리스트 2개 이상.
- risk.level은 "Normal" 또는 "Caution" 또는 "High" 중 하나.
- suggestions는 길이 3의 리스트, 각 원소는 {"type": "...", "rationale": "...", "direction": "..."} 형태.
- 진단/처방/의학적 단정 금지.

[안전 규칙]
- 자해/자살/타해/학대/응급 징후가 있으면 risk.level="High".
- High일 때는 안전 확인 개입이 필요함을 risk.message에 안내.
- 내담자 고통(우울/불안/무력감) 자체는 상담 거부로 단정하지 않는다.

[suggestions 작성 규칙 - 매우 중요]
suggestions는 상담사에게 전달하는 "개입 방향 힌트"다.
- 상담 대사(내담자에게 직접 할 말)를 쓰지 않는다.
- 상담사가 취할 수 있는 개입 전략/질문 방향/주의사항을 간결하게 쓴다.
- type: 개입 유형 (예: 공감 심화, 회피 탐색, 목표 재확인, 자원 탐색, 위험 모니터링)
- rationale: 이 개입이 필요한 이유 (내담자 발화에서 근거 제시)
- direction: 상담사가 취할 수 있는 구체적 방향 (1~2문장, 전략 서술)

[반드시 이 스키마 그대로]
{
  "insight": "내담자 발화 핵심 요약 (한 문장)",
  "emotions": ["감정1","감정2"],
  "intent": "내담자의 욕구/의도 추정 (단정 금지)",
  "risk": {
    "level": "Normal|Caution|High",
    "signals": ["근거1","근거2"],
    "message": "상담사에게 전달할 짧은 안내"
  },
  "suggestions": [
    {"type":"공감 심화","rationale":"근거","direction":"전략 방향"},
    {"type":"탐색","rationale":"근거","direction":"전략 방향"},
    {"type":"목표/다음단계","rationale":"근거","direction":"전략 방향"}
  ]
}

[확신이 없으면]
- risk.level은 "Caution"
- 나머지는 빈칸 없이 최대한 채워서 출력하라.
""".strip()


# =============================================================
# 3. Pydantic 스키마
# =============================================================

class HelperRequest(BaseModel):
    """
    POST /helper/suggestion 요청 바디.

    Fields:
        sess_id             : 상담 세션 ID
        counselor_id        : 상담사 ID
        last_client_text    : 내담자의 현재(가장 최근) 발화
        last_counselor_text : 상담사의 직전 발화 (선택)
        history             : 이전 대화 목록
                              [{"role": "counselor"|"client", "text": "..."}]
                              최근 HCX_HISTORY_WINDOW개 발화를 슬라이딩 윈도우로 사용
        context             : 추가 컨텍스트 (선택)
    """
    session_id:          int                            = Field(..., alias="sess_id", ge=1)
    counselor_id:        int                            = Field(..., ge=1)
    last_client_text:    str                            = Field(default="")
    last_counselor_text: str                            = Field(default="")
    history:             Optional[List[Dict[str, str]]] = None
    context:             Optional[Dict[str, Any]]       = None

    model_config = {"populate_by_name": True}


# =============================================================
# 4. 룰 기반 1차 필터 (HCX 호출 전 선별)
# =============================================================

_NEG_KEYWORDS: tuple = (
    "그만", "포기", "싫어", "힘들", "못하겠",
    "안 할래", "의미없", "죽고싶",
)
_HIGH_RISK_KEYWORDS: tuple = (
    "죽고싶", "자해", "사라지고싶", "없어지고싶", "끝내고싶",
)


def rule_check(text: str) -> Dict[str, Any]:
    """
    발화를 키워드 기반으로 1차 분류한다.

    Returns dict with keys:
        skip_hcx    (bool) : True이면 HCX 호출 없이 바로 반환
        churn_signal (int) : 이탈/위험 신호 여부 (0 or 1)
        type         (str) : NORMAL | CHURN_ALERT | HIGH_RISK
        risk_level   (str) : Normal | Caution | High
    """
    t = (text or "").strip()

    # 발화 없음 → HCX 호출 불필요
    if not t:
        return {
            "skip_hcx":     True,
            "churn_signal": 0,
            "type":         "NORMAL",
            "mode":         "RULE",
            "insight":      "발화 없음",
            "risk_level":   "Normal",
            "suggestion":   "내담자 발화가 없습니다. 라포 형성부터 시작하세요.",
        }

    # 고위험 키워드
    if any(k in t for k in _HIGH_RISK_KEYWORDS):
        return {
            "skip_hcx":     False,
            "churn_signal": 1,
            "type":         "HIGH_RISK",
            "mode":         "RULE",
            "risk_level":   "High",
        }

    # 부정 키워드
    if any(k in t for k in _NEG_KEYWORDS):
        return {
            "skip_hcx":     False,
            "churn_signal": 1,
            "type":         "CHURN_ALERT",
            "mode":         "RULE",
            "risk_level":   "Caution",
        }

    return {
        "skip_hcx":     False,
        "churn_signal": 0,
        "type":         "NORMAL",
        "mode":         "RULE",
        "risk_level":   "Normal",
    }


# =============================================================
# 5. HCX 클라이언트
# =============================================================

def _call_hcx(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 280,
) -> Optional[str]:
    """
    HyperCLOVA X API를 호출하고 응답 content를 반환한다.
    실패 시 RuntimeError를 발생시킨다.
    """
    url     = HCXConfig.endpoint()
    headers = {
        "Authorization":                 HCXConfig.auth_header(),
        "X-NCP-CLOVASTUDIO-REQUEST-ID":  HCXConfig.request_id,
        "Content-Type":                  "application/json; charset=utf-8",
    }
    payload = {
        "messages":    messages,
        "temperature": temperature,
        "maxTokens":   max_tokens,
    }

    res = requests.post(url, headers=headers, json=payload, timeout=HCXConfig.timeout)

    if not res.ok:
        raise RuntimeError(
            f"HCX HTTP 오류: {res.status_code} — {res.content.decode('utf-8', errors='replace')[:200]}"
        )

    # PowerShell/Windows 환경에서 한글 깨짐 방지 — raw bytes로 직접 파싱
    data    = json.loads(res.content.decode("utf-8"))
    content = None

    # v3 응답 구조 우선 탐색
    try:
        content = data["result"]["message"]["content"]
    except (KeyError, TypeError):
        pass

    # OpenAI 호환 구조 fallback
    if content is None:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, TypeError, IndexError):
            pass

    return content


# =============================================================
# 6. JSON 파싱 & 검증 유틸
# =============================================================

def _extract_json(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    HCX 응답 문자열에서 JSON 객체를 추출한다.
    마크다운 코드펜스(```json ... ```)도 처리한다.
    """
    if not raw:
        return None

    text = re.sub(r"```[a-zA-Z]*", "", str(raw)).replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _is_valid(obj: Any) -> bool:
    """
    필수 키와 타입을 검증한다.
    emotions 빈 리스트, suggestions 빈 리스트는 통과 허용한다.
    """
    if not isinstance(obj, dict):
        return False

    for key in ("insight", "emotions", "intent", "risk", "suggestions"):
        if key not in obj:
            return False

    if not isinstance(obj["emotions"], list) or len(obj["emotions"]) < 2:
        return False

    risk = obj.get("risk", {})
    if not isinstance(risk, dict):
        return False
    if risk.get("level") not in ("Normal", "Caution", "High"):
        return False

    suggestions = obj.get("suggestions")
    if not isinstance(suggestions, list):
        return False
    for s in suggestions:
        if not isinstance(s, dict) or "type" not in s:
            return False

    return True


# =============================================================
# 7. 서비스 레이어 — HCX 분석 오케스트레이션
# =============================================================

def _build_history_block(history: Optional[List[Dict[str, str]]]) -> str:
    """
    history에서 최근 HCX_HISTORY_WINDOW개 발화만 추출하여
    '[상담사] ...' / '[내담자] ...' 형식의 문자열로 변환한다.
    """
    if not history:
        return "(없음)"

    window = history[-HCXConfig.history_window:]
    lines  = [
        ("[상담사]" if h.get("role") == "counselor" else "[내담자]")
        + " "
        + h.get("text", "").strip()
        for h in window
    ]
    return "\n".join(lines) if lines else "(없음)"


def analyze_with_hcx(
    client_text: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    내담자 발화와 최근 대화 내역을 HCX에 전달하고 분석 결과를 반환한다.
    1차 시도 실패 시 temperature=0.0으로 1회 재시도한다.
    두 번 모두 실패하면 None을 반환한다.
    """
    history_block = _build_history_block(history)
    user_content  = (
        f"[이전 대화]\n{history_block}\n\n"
        f"[현재 내담자 발화]\n{client_text.strip()}"
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]

    for attempt, temperature in enumerate([0.2, 0.0], start=1):
        if attempt == 2:
            time.sleep(0.15)  # 재시도 전 짧은 대기

        try:
            raw = _call_hcx(messages, temperature=temperature)
        except RuntimeError as e:
            print(f"[HCX {attempt}차 호출 오류] {e}")
            continue

        print(f"[HCX {attempt}차 응답] {repr(raw)}")

        obj   = _extract_json(raw)
        valid = _is_valid(obj) if obj else False

        print(f"[HCX {attempt}차] 파싱={obj is not None}, 검증={valid}")

        if obj and valid:
            return obj

    return None


# =============================================================
# 8. Fallback 응답 생성
# =============================================================

def _fallback(reason: str = "") -> Dict[str, Any]:
    """HCX 분석 실패 시 반환할 기본 응답"""
    return {
        "mode":         "FALLBACK",
        "churn_signal": 0,
        "insight":      f"AI 분석 지연: {reason}" if reason else "AI 분석 지연",
        "emotions":     ["불명확", "파악불가"],
        "intent":       "대화 진행 중",
        "risk": {
            "level":   "Normal",
            "signals": [],
            "message": "현재 상태 정상. 상담을 이어가세요.",
        },
        "suggestions": [
            {"type": "공감 심화",     "rationale": "발화 파싱 실패", "direction": "내담자 감정 반영 탐색 필요"},
            {"type": "탐색",          "rationale": "발화 파싱 실패", "direction": "핵심 주제 재확인 질문 고려"},
            {"type": "목표/다음단계", "rationale": "발화 파싱 실패", "direction": "상담 속도 조율 및 안전 확인"},
        ],
        "type": "NORMAL",
    }


# =============================================================
# 9. FastAPI 라우터
# =============================================================

router = APIRouter(prefix="/helper", tags=["helper"])


@router.post("/suggestion")
def helper_suggestion(payload: HelperRequest) -> Dict[str, Any]:
    """
    내담자의 최근 발화를 분석하여 상담사에게 개입 제안 3개를 반환한다.

    흐름:
      1. 룰 기반 1차 필터 (키워드 검사)
      2. USE_HCX=0 이면 룰 결과만 반환 (개발/테스트 모드)
      3. USE_HCX=1 이면 HCX 분석 → 실패 시 Fallback
    """
    text = (payload.last_client_text or "").strip()
    rule = rule_check(text)

    # 발화 없음 등 HCX 호출이 불필요한 경우
    if rule.get("skip_hcx"):
        return rule

    # HCX 비활성화 모드 (개발/테스트)
    if not HCXConfig.use_hcx:
        rule["mode"] = "RULE_ONLY"
        return rule

    # HCX 분석 실행
    try:
        obj = analyze_with_hcx(text, payload.history)
    except Exception as e:
        return _fallback(str(e))

    if obj is None:
        return _fallback("AI 응답 내용 부족 (단순 인사 또는 파싱 실패)")

    # 위험 수준 통합 (룰 기반 신호와 HCX 신호 중 높은 쪽 적용)
    risk_level   = obj.get("risk", {}).get("level", "Normal")
    churn_signal = 1 if risk_level in ("Caution", "High") else 0
    churn_signal = max(churn_signal, rule.get("churn_signal", 0))

    return {
        "mode":        "HCX",
        "churn_signal": churn_signal,
        "type":        "CHURN_ALERT" if churn_signal else "NORMAL",
        "insight":     obj.get("insight",     ""),
        "emotions":    obj.get("emotions",    []),
        "intent":      obj.get("intent",      ""),
        "risk":        obj.get("risk",        {}),
        "suggestions": obj.get("suggestions", []),
    }
