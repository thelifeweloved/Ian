# services/feature3_emotion.py
# 감정분석 기능 (메시지 단위) -> text_emotion 저장용 결과 생성
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

# DB 저장 기준 라벨(소문자 통일)
ALLOWED_LABELS = {"happiness", "anger", "sadness", "fear", "neutral"}


def extract_json(content: str) -> dict:
    # 코드블록 JSON 우선 파싱 (비탐욕 .*? 로 안정성 개선)
    m = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if m:
        return json.loads(m.group(1))

    # 일반 텍스트 안의 JSON 추출
    first = content.find("{")
    last = content.rfind("}")
    if first != -1 and last != -1 and last > first:
        return json.loads(content[first:last + 1])

    raise ValueError("feature3_emotion JSON 파싱 실패:\n" + content[:300])


def clamp01(x: Any, default: float = 0.5) -> float:
    try:
        v = float(x)
    except Exception:
        return default
    if v < 0:
        return 0.0
    if v > 1:
        return 1.0
    return round(v, 4)


def normalize_label(label: Any) -> str:
    """
    모델이 대/소문자, 약어, 구버전 라벨을 섞어 반환해도
    최종적으로 DB 저장 표준(소문자 5종)으로 정규화한다.
    """
    # ✅ 핵심 수정: upper() -> lower()
    s = str(label).strip().lower()

    # 약어/구버전/동의어 -> 표준 라벨(소문자)
    alias = {
        # 기존 quality류 라벨/약어가 섞여 들어와도 최대한 안전하게 매핑
        "pos": "happiness",
        "positive": "happiness",

        "neu": "neutral",
        "neutral": "neutral",

        "neg": "sadness",   # 일반적인 부정은 sadness로 보수 매핑 (팀 기준에 맞춰 조정 가능)
        "negative": "sadness",

        "watch": "fear",
        "caution": "fear",
        "alert": "fear",
        "risk": "fear",     # 구버전 호환

        # 감정 동의어/변형
        "happy": "happiness",
        "joy": "happiness",

        "angry": "anger",
        "mad": "anger",

        "sad": "sadness",
        "depressed": "sadness",

        "anxiety": "fear",
        "anxious": "fear",
        "worry": "fear",
        "worried": "fear",
        "afraid": "fear",
        "scared": "fear",
    }

    s = alias.get(s, s)

    if s not in ALLOWED_LABELS:
        return "neutral"
    return s


def build_prompt(messages: List[Dict[str, Any]]) -> str:
    """
    messages 예시:
    [
      {"idx":0, "msg_id":123, "speaker":"CLIENT", "text":"..."},
      ...
    ]
    """
    rows = []
    for m in messages:
        idx = int(m["idx"])
        speaker = str(m.get("speaker", "UNKNOWN")).strip()
        text = str(m.get("text", "")).strip().replace("\n", " ")
        rows.append(f"{idx}\t{speaker}\t{text}")
    tsv_body = "\n".join(rows)

    return f"""
다음은 상담 대화 메시지 목록이다. 각 메시지의 감정 라벨을 분류하라.

[라벨 정의 - 정확히 5개만 사용]
- happiness: 안도, 감사, 희망, 안정감, 수용, 협조, 의욕 등 긍정 정서
- anger: 짜증, 분노, 불만, 공격적 표현, 강한 반발
- sadness: 슬픔, 우울감, 무기력, 상실감, 의기소침함
- fear: 불안, 걱정, 긴장, 두려움, 압박감, 초조함
- neutral: 사실 전달/정보 응답 중심, 감정 강도 낮음 또는 감정 판별이 어려운 경우

[분류 원칙]
- 반드시 위 5개 라벨 중 하나만 선택한다.
- 감정이 혼합된 경우, 문장 내에서 가장 두드러지는 감정을 1개 선택한다.
- 상담사 발화는 특별한 정서 표현이 없으면 neutral로 분류한다.
- 짧은 응답(예: "네", "음", "그래요")은 문맥상 감정이 분명하지 않으면 neutral로 분류한다.
- "걱정된다", "불안하다", "떨린다", "무섭다", "압박된다" 등은 fear 우선으로 본다.
- "지친다", "허무하다", "의욕이 없다", "우울하다", "슬프다" 등은 sadness 우선으로 본다.
- "짜증난다", "화난다", "억울하다", "열받는다" 등은 anger 우선으로 본다.

[출력 규칙]
- 반드시 JSON만 출력 (다른 글/설명/코드블록 금지)
- 입력의 모든 idx를 빠짐없이 반환
- score/confidence는 0.0~1.0 범위 숫자
- evidence는 짧은 문장 1개 (핵심 근거만 간단히)
- idx는 입력값과 동일한 정수여야 한다
- label은 반드시 소문자 5개(happiness/anger/sadness/fear/neutral) 중 하나

[출력 JSON 형식]
{{
  "items": [
    {{
      "idx": 0,
      "label": "fear",
      "score": 0.82,
      "confidence": 0.76,
      "evidence": "불안과 압박감을 직접 표현함"
    }}
  ]
}}

[입력 메시지 TSV: idx<TAB>speaker<TAB>text]
{tsv_body}
""".strip()


def analyze_feature3(clova_client, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns:
    {
      "items": [
        {
          "idx": 0,
          "msg_id": 123,              # 입력에 있으면 유지
          "label": "fear",            # ✅ 소문자 표준 라벨
          "score": 0.82,
          "confidence": 0.76,
          "evidence": "...",
          "meta": {...}
        },
        ...
      ]
    }
    """
    if not messages:
        return {"items": []}

    r = clova_client.chat(
        system_text="너는 상담 메시지 감정분류기다. 반드시 JSON만 출력한다.",
        user_text=build_prompt(messages),
        temperature=0.0,
        timeout=90,
    )
    content = r["result"]["message"]["content"]

    try:
        data = extract_json(content)
        raw_items = data.get("items", [])
        if not isinstance(raw_items, list):
            raise ValueError("items가 리스트가 아님")
    except Exception:
        # 파싱 실패 시 fallback (소문자 라벨 통일)
        return {
            "items": [
                {
                    "idx": int(m["idx"]),
                    "msg_id": m.get("msg_id"),
                    "label": "neutral",
                    "score": 0.5,
                    "confidence": 0.2,
                    "evidence": "parse_error",
                    "meta": {"parse_error": True, "raw_preview": content[:300]},
                }
                for m in messages
            ]
        }

    # 모델 출력 idx별 정규화
    by_idx: Dict[int, Dict[str, Any]] = {}
    for item in raw_items:
        try:
            idx = int(item.get("idx"))
        except Exception:
            continue

        by_idx[idx] = {
            "idx": idx,
            "label": normalize_label(item.get("label")),
            "score": clamp01(item.get("score"), default=0.5),
            "confidence": clamp01(item.get("confidence"), default=0.5),
            "evidence": str(item.get("evidence", ""))[:200],
        }

    normalized_items: List[Dict[str, Any]] = []
    for m in messages:
        idx = int(m["idx"])
        base = by_idx.get(idx)
        if base is None:
            base = {
                "idx": idx,
                "label": "neutral",
                "score": 0.5,
                "confidence": 0.3,
                "evidence": "missing_from_model_output",
                "meta": {"parse_error": True, "reason": "missing_idx"},
            }
        else:
            base["meta"] = {"source": "clovax_llm"}

        if "msg_id" in m:
            base["msg_id"] = m["msg_id"]
        normalized_items.append(base)

    return {"items": normalized_items}