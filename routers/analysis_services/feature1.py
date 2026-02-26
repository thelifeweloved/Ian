# services/feature1.py
# 핵심기능1 : "이탈/종결 신호" 점수화 + 사유
import json, re

# 1) JSON 파싱 보강 (앞뒤 텍스트 섞여도 복구)
def extract_json(content: str) -> dict:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return json.loads(m.group(1))

    first = content.find("{")
    last = content.rfind("}")
    if first != -1 and last != -1 and last > first:
        return json.loads(content[first:last+1])

    raise ValueError("feature1 JSON 파싱 실패:\n" + content[:300])

def build_prompt(dialog_text: str) -> str:
    return f"""
아래 상담 대화를 보고 '핵심기능1(이탈/종결 신호 감지)' 결과를 생성하라.

[출력 규칙]
- 반드시 JSON "단 1개"만 출력한다. (설명/문장/코드블록/마크다운 금지)
- 키는 정확히 아래 3개만 사용한다:
  1) signal_score: 0~1 실수
  2) signal_level: "LOW" | "MID" | "HIGH" 중 하나
  3) reasons: 문자열 배열(2~4개)

[판정 절차(순서 고정)]
1) 신호 찾기:
   - 이탈/종결 의사(그만, 끝, 중단, 더 못하겠음, 연락거부 등)
   - 거리두기/회피(오늘은 여기까지만, 다음에, 모르겠어요 반복 등)
   - 참여도 저하(단답·침묵·응답지연이 '연속 구간'으로 나타남)
2) 강도 판단:
   - 명시적 중단/거부는 강도가 가장 높다.
   - 회피/거리두기는 반복될수록 강도가 올라간다.
   - 참여도 저하는 '단발'이 아니라 '반복/연속 구간'일 때만 의미가 커진다.
3) 점수 산정(signal_score):
   - 0.00: 신호 없음
   - 0.20: 단발성 피곤/불만/짧은 답 1회(흐름 유지)
   - 0.45: 회피/거리두기 1~2회 또는 참여 저하가 눈에 띔(MID 하단)
   - 0.60: 회피/단답/지연이 2회 이상 반복되거나 연속 구간으로 나타남(MID 상단)
   - 0.80: 중단 의사 거의 확실(명시적 표현/강한 거부)
   - 0.95: 즉시 종결/단절 선언 수준
4) 레벨 결정(signal_level): 아래 경계값을 절대 준수한다.
   - LOW: 0.00 ~ 0.39
   - MID: 0.40 ~ 0.69
   - HIGH: 0.70 ~ 1.00
   ※ signal_level은 반드시 signal_score 범위와 일치해야 한다.

[근거 작성 규칙(reasons)]
- reasons는 2~4개만 작성한다.
- '관찰된 발화/패턴'만 근거로 쓴다. (추측/해석/진단 금지)
- 가능하면 내담자 발화를 우선 근거로 사용한다.
- 각 reason은 "무엇이 관찰됐는지 + 간단한 맥락"으로 짧게 쓴다.

[애매 케이스 처리]
- 단발성 단답/피곤함/짜증 표현 1회는 LOW로 유지한다.
- 단답/침묵/지연이 '반복되거나 연속 구간'으로 나타날 때만 MID 이상을 고려한다.
- 명시적 중단/종결 발화가 있으면 HIGH를 우선 고려한다.

[상담 대화]
{dialog_text}
""".strip()

# 3) 핵심 기능 1 (임계값 보정 + MID 알림 포함)
def analyze_feature1(clova_client, dialog_text: str) -> dict:
    r = clova_client.chat(
        system_text="너는 상담 종료 후 상담사를 돕는 분석 도우미다. 반드시 JSON만 출력한다.",
        user_text=build_prompt(dialog_text),
        temperature=0.0
    )
    content = r["result"]["message"]["content"]
    data = extract_json(content)

    for k in ("signal_score", "signal_level", "reasons"):
        if k not in data:
            raise ValueError(f"기능1 결과 필수키 누락: {k}")

    # --- 재현율 라이트 개선 ---
    score = float(data["signal_score"])
    level = data["signal_level"]

    # 0.5 이상이면 경보로 간주 + MID도 경보
    is_alert = (score >= 0.5) or (level in ("MID", "HIGH"))

    return {
        "signal_score": round(score, 3),
        "signal_level": "HIGH" if is_alert else level,
        "reasons": data["reasons"]
    }