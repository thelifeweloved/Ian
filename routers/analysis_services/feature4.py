# routers/analysis_services/feature4.py
import json
import re
from typing import Any, Dict


def extract_json(content: str) -> dict:
    """
    모델 응답에서 JSON만 안전하게 추출한다.
    - ```json ... ``` 형태
    - 일반 텍스트 안의 { ... } 형태
    """
    # 코드블록 JSON 우선
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return json.loads(m.group(1))

    # 일반 문자열에서 첫 { ~ 마지막 } 추출
    first = content.find("{")
    last = content.rfind("}")
    if first != -1 and last != -1 and last > first:
        return json.loads(content[first:last + 1])

    raise ValueError("JSON 파싱 실패")


def clamp_score_0_100(x: Any, default: float = 50.0) -> float:
    """
    점수를 0~100 범위 float로 보정한다.
    DECIMAL(5,2)에 맞게 소수 둘째자리 반올림.
    """
    try:
        v = float(x)
    except Exception:
        v = default

    if v < 0:
        v = 0.0
    elif v > 100:
        v = 100.0

    return round(v, 2)


def build_prompt(dialog_text: str) -> str:
    """
    세션 전체 대화를 보고 flow(흐름 점수), score(종합 품질 점수)를 평가하도록 하는 프롬프트.
    """
    return f"""
다음은 상담 세션 전체 대화이다. 세션 품질을 평가하라.

[평가 항목]
- flow: 대화 흐름 점수 (0~100)
  - 질문/응답 연결의 자연스러움
  - 맥락 유지 여부
  - 반복/단절 정도
- score: 세션 품질 종합 점수 (0~100)
  - flow를 포함하여 상담 전반의 품질을 종합 평가
  - 공감/반응의 적절성, 탐색, 정리/진행의 균형 등을 반영

[평가 기준]
- 점수는 0~100 범위 숫자로 작성한다.
- 소수점 사용 가능 (예: 78.5)
- 대화가 너무 짧거나 정보가 부족하면 중립적으로 평가한다. (예: 45~60 범위)
- 근거는 짧고 객관적으로 작성한다.
- 과도하게 단정하거나 공격적인 표현은 피한다.

[출력 규칙]
- 반드시 JSON만 출력 (다른 글/설명/코드블록 금지)
- 키는 정확히 아래만 사용:
  1) flow
  2) score
  3) reason

[출력 JSON 형식]
{{
  "flow": 76.5,
  "score": 81.0,
  "reason": "대화 흐름은 전반적으로 자연스럽고 공감 및 탐색이 비교적 균형 있게 이루어짐"
}}

[상담 세션 대화 원문]
{dialog_text}
""".strip()


def analyze_feature4(clova_client, dialog_text: str) -> Dict[str, Any]:
    """
    세션 전체 대화를 기반으로 품질 분석(flow, score)을 수행한다.

    Args:
        clova_client: ClovaXClient 인스턴스 (chat(system_text, user_text, ...) 지원)
        dialog_text: 세션 전체 대화 문자열

    Returns:
        {
          "flow": float,   # 0~100
          "score": float,  # 0~100
          "meta": {
            "reason": str,
            "raw": dict | None
          }
        }

    실패 시에도 fallback 값을 반환하여 서비스 흐름이 끊기지 않게 함.
    """
    text = (dialog_text or "").strip()

    # 대화가 비어 있으면 안전하게 중립값 반환
    if not text:
        return {
            "flow": 50.0,
            "score": 50.0,
            "meta": {
                "reason": "대화 내용이 없어 기본값으로 처리됨",
                "raw": None,
            },
        }

    # 너무 짧은 대화는 신뢰도 낮으므로 중립적 fallback(혹은 모델 호출 가능)
    # 여기서는 모델은 호출하되, 결과가 깨지면 중립값 반환하도록 둠.
    try:
        res = clova_client.chat(
            system_text="너는 상담 세션 품질 평가기다. 반드시 유효한 JSON만 출력한다.",
            user_text=build_prompt(text),
            temperature=0.0,
            timeout=90,
        )
        content = res["result"]["message"]["content"]

        data = extract_json(content)

        flow = clamp_score_0_100(data.get("flow"), default=50.0)
        score = clamp_score_0_100(data.get("score"), default=50.0)
        reason = str(data.get("reason", "")).strip()[:300]

        # 비어 있으면 기본 문구
        if not reason:
            reason = "세션 품질 분석 결과가 생성됨"

        return {
            "flow": flow,
            "score": score,
            "meta": {
                "reason": reason,
                "raw": data,
            },
        }

    except Exception as e:
        # 모델 응답 파싱 실패/네트워크 오류 등 fallback
        return {
            "flow": 50.0,
            "score": 50.0,
            "meta": {
                "reason": f"quality_parse_or_call_error: {type(e).__name__}",
                "raw": None,
            },
        }