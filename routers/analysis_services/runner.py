# routers/analysis_services/runner.py
import json
from typing import Any, Dict, List

import pymysql

from .session_repo import (
    load_dialog_text,
    load_msg_rows,
)

from .feature1 import analyze_feature1
from .feature2 import analyze_feature2
from .feature3 import analyze_feature3
from .feature4 import analyze_feature4


def _json_dumps_safe(obj: Any) -> str:
    """DB JSON 컬럼/텍스트 저장용 안전 직렬화"""
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return json.dumps({"_fallback": str(obj)}, ensure_ascii=False)


def insert_text_emotions(conn, emotion_items: List[Dict[str, Any]]) -> None:
    """
    text_emotion 테이블에 감정분석 결과를 저장한다.
    - msg_id 기준으로 기존 결과 삭제 후 재삽입 (중복 방지)
    - emotion_items 예시:
      [
        {
          "msg_id": 123,
          "label": "fear",
          "score": 0.82,
          "confidence": 0.76,
          "evidence": "불안 표현",
        },
        ...
      ]
    """
    if not emotion_items:
        return

    # msg_id 없는 항목 제거
    rows = [x for x in emotion_items if x.get("msg_id") is not None]
    if not rows:
        return

    msg_ids = [int(x["msg_id"]) for x in rows]

    with conn.cursor() as cur:
        # 1) 기존 감정결과 삭제 (재분석 대비)
        placeholders = ",".join(["%s"] * len(msg_ids))
        cur.execute(f"DELETE FROM text_emotion WHERE msg_id IN ({placeholders})", msg_ids)

        # 2) 재삽입
        sql = """
        INSERT INTO text_emotion (msg_id, label, score, meta)
        VALUES (%s, %s, %s, %s)
        """
        values = []
        for item in rows:
            label = str(item.get("label", "neutral")).strip().lower() or "neutral"
            score = item.get("score", 0.5)
            try:
                score = float(score)
            except Exception:
                score = 0.5

            # 0~1 범위 보정
            if score < 0:
                score = 0.0
            elif score > 1:
                score = 1.0

            meta_obj = {
                "confidence": item.get("confidence"),
                "evidence": item.get("evidence", ""),
                "source": "feature3",
            }

            values.append((
                int(item["msg_id"]),
                label,
                round(score, 4),
                _json_dumps_safe(meta_obj),
            ))

        cur.executemany(sql, values)


def upsert_sess_analysis(
    conn,
    *,
    sess_id: int,
    topic_id: int,
    summary: str,
    note: str = "",
) -> None:
    """
    sess_analysis 테이블 저장/갱신
    (기존 네 feature2 저장 로직 유지용)
    - 테이블/컬럼명은 네 프로젝트 명세에 맞춰 이미 맞춰져 있다고 가정
    """
    with conn.cursor() as cur:
        sql = """
        INSERT INTO sess_analysis (sess_id, topic_id, summary, note)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            topic_id = VALUES(topic_id),
            summary = VALUES(summary),
            note = VALUES(note)
        """
        cur.execute(
            sql,
            (
                int(sess_id),
                int(topic_id),
                summary or "",
                note,
            ),
        )


def upsert_quality(
    conn,
    *,
    sess_id: int,
    flow: float,
    score: float,
) -> None:
    """
    quality 테이블 저장/갱신 (세션당 1건)
    테이블 명세:
      - sess_id
      - flow (0~100)
      - score (0~100)
      - created_at (DB 기본값)

    전제:
      - quality.sess_id 에 UNIQUE KEY 존재 (명세상 세션당 1건)
    """
    # DECIMAL(5,2) 맞춤 + 범위 보정
    try:
        flow = float(flow)
    except Exception:
        flow = 50.0

    try:
        score = float(score)
    except Exception:
        score = 50.0

    flow = max(0.0, min(100.0, round(flow, 2)))
    score = max(0.0, min(100.0, round(score, 2)))

    with conn.cursor() as cur:
        sql = """
        INSERT INTO quality (sess_id, flow, score)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            flow = VALUES(flow),
            score = VALUES(score)
        """
        cur.execute(sql, (int(sess_id), flow, score))


def run_core_features(
    clova_client,
    *,
    sess_id: int,
    topic_id: int,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
) -> dict:
    """
    세션 대화를 불러와 핵심기능1/2/3/4를 실행하고,
    feature2(sess_analysis), feature3(text_emotion), feature4(quality) 결과를 DB에 저장한다.

    Returns:
      {
        "feature1": { ... },                 # 이탈신호 탐지
        "feature2": {summary_md, meta},      # 리포트/요약
        "emotion":  {"items":[...]},         # 감정분석 (문장 단위)
        "quality":  {"flow": ..., "score": ..., "meta": {...}}  # 품질분석 (세션 단위)
      }
    """
    # 1) 대화 로드 (별도 커넥션 사용)
    dialog_text = load_dialog_text(
        sess_id=sess_id,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )

    # 감정분석용 메시지 로드 (문장 단위)
    msg_rows = load_msg_rows(
        sess_id=sess_id,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )

    # 2) 기능 실행 (ClovaX)
    # feature1: 이탈신호
    f1 = analyze_feature1(clova_client, dialog_text)

    # feature2: 요약/리포트
    f2 = analyze_feature2(clova_client, dialog_text)

    # feature3: 감정분석 (내담자만 분석)
    client_msg_rows = [
        m for m in msg_rows
        if str(m.get("speaker", "")).strip().upper() == "CLIENT"
        and str(m.get("text", "")).strip()
    ]
    try:
        _test_r = clova_client.chat(
            system_text="너는 상담 메시지 감정분류기다. 반드시 JSON만 출력한다.",
            user_text='테스트: {"items":[{"idx":0,"label":"neutral","score":0.5}]}',
            temperature=0.0, timeout=30
        )
        print("[feature3 ClovaX 응답 구조]", list(_test_r.keys()))
        print("[feature3 ClovaX 응답 content]", str(_test_r)[:300])
    except Exception as _e:
        print("[feature3 테스트 실패]", _e)
    emotion_result = analyze_feature3(clova_client, client_msg_rows)

    # feature4: 품질분석 (세션 전체 대화 기준)
    q4 = analyze_feature4(clova_client, dialog_text)

    # 3) DB 저장 (하나의 트랜잭션)
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    try:
        # feature2 결과 저장 (sess_analysis)
        upsert_sess_analysis(
            conn,
            sess_id=sess_id,
            topic_id=topic_id,
            summary=f2.get("summary_md", ""),
            note="",
        )

        # feature3 결과 저장 (text_emotion)
        insert_text_emotions(conn, emotion_result.get("items", []))

        # feature4 결과 저장 (quality)
        upsert_quality(
            conn,
            sess_id=sess_id,
            flow=q4.get("flow", 50.0),
            score=q4.get("score", 50.0),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "feature1": f1,
        "feature2": f2,
        "emotion": emotion_result,
        "quality": q4,
    }