# services/feature2.py
# 핵심기능2 : 상담리포트 생성 (요약 + 화면용 메타)
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

    raise ValueError("feature2 JSON 파싱 실패:\n" + content[:300])

# 2) 프롬프트 (기존 유지)
def build_prompt(dialog_text: str) -> str:
    return f"""
아래 상담 대화를 바탕으로 '핵심기능2' 리포트를 생성하라.

[출력 규칙]
- 반드시 JSON만 출력 (다른 글/설명/코드블록 금지)
- JSON 키는 정확히 아래 2개만:
  1) summary_md: 문자열 (마크다운 리포트 본문)
  2) meta: 객체 (화면 구성용 구조화 데이터)

[meta 객체 필수 키]
- keywords: 문자열 배열(5~12개)
- key_points: 문자열 배열(3~7개)
- counselor_guides: 문자열 배열(3~6개)
- client_state: 짧은 문장 1개

[상담 대화]
{dialog_text}
""".strip()

# 3) 핵심 기능 2 실행 (출력 안정성 보강)
def analyze_feature2(clova_client, dialog_text: str) -> dict:
    r = clova_client.chat(
        system_text="너는 상담 종료 후 상담사를 돕는 리포트 생성 도우미다. 반드시 JSON만 출력한다.",
        user_text=build_prompt(dialog_text),
        temperature=0.0  # JSON 형식 안정성 ↑
    )
    content = r["result"]["message"]["content"]

    # ✅ JSON 파싱 실패해도 서버가 500으로 죽지 않게 안전장치
    try:
        data = extract_json(content)
    except Exception:
        return {
            "summary_md": content.strip(),
            "meta": {
                "parse_error": True,
                "raw_preview": content[:300],
            },
        }

    # ✅ 정상 파싱된 경우만 필수키 검증
    if "summary_md" not in data or "meta" not in data:
        raise ValueError("기능2 결과 필수키 누락(summary_md/meta)")

    meta = data["meta"]
    for k in ("keywords", "key_points", "counselor_guides", "client_state"):
        if k not in meta:
            raise ValueError(f"기능2 meta 필수키 누락: {k}")

    return data