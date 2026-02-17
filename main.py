from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from db import get_db

load_dotenv()

app = FastAPI(title="Mindway Post-Analysis API", version="1.0.1")


# =========================================================
# Request Model
# =========================================================
class MessageCreate(BaseModel):
    sess_id: int = Field(..., ge=1)
    speaker: str = Field(..., pattern="^(COUNSELOR|CLIENT|SYSTEM)$")
    speaker_id: Optional[int] = Field(None, ge=1)
    text: Optional[str] = None
    emoji: Optional[str] = None
    file_url: Optional[str] = None
    stt_conf: float = Field(0.0, ge=0.0, le=1.0)


# =========================================================
# Logic
# =========================================================
def detect_dropout_signal(message: Optional[str]) -> Optional[Dict[str, Any]]:
    if not message:
        return None
    msg = message.strip()
    score = 0.0
    rules = []

    if any(kw in msg for kw in ["그만", "힘들", "포기", "싫어"]):
        score += 0.5
        rules.append("NEG_KEYWORD")

    if score >= 0.5:
        return {
            "type": "RISK_WORD",
            "status": "DETECTED",
            "score": round(min(score, 1.0), 2),
            "rule": "|".join(rules)[:50],
        }
    return None


# =========================================================
# Helpers
# =========================================================
def _rows(db: Session, sql: str, params: Dict[str, Any]):
    return db.execute(text(sql), params).mappings().all()


# =========================================================
# Health
# =========================================================
@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    v = db.execute(text("SELECT 1")).scalar()
    return {"db": "ok", "ping": v}


# =========================================================
# Sessions
# =========================================================
@app.get("/sessions")
def list_sessions(limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    sql = f"""
        SELECT *
        FROM sess
        ORDER BY id DESC
        LIMIT {int(limit)}
    """
    result = _rows(db, sql, {})
    return {"items": jsonable_encoder(result), "count": len(result)}


# =========================================================
# Messages (Write)
# =========================================================
@app.post("/messages")
def create_message(payload: MessageCreate, db: Session = Depends(get_db)):
    try:
        # 세션 존재 체크(없으면 FK/에러 대신 404로)
        sess_exists = db.execute(
            text("SELECT 1 FROM sess WHERE id = :sid"),
            {"sid": payload.sess_id},
        ).scalar()
        if not sess_exists:
            raise HTTPException(status_code=404, detail="sess_id not found")

        res = db.execute(text("""
            INSERT INTO msg (sess_id, speaker, speaker_id, text, emoji, file_url, stt_conf, at)
            VALUES (:sid, :speaker, :speaker_id, :text, :emoji, :file_url, :stt_conf, NOW())
        """), {
            "sid": payload.sess_id,
            "speaker": payload.speaker,
            "speaker_id": payload.speaker_id,
            "text": payload.text,
            "emoji": payload.emoji,
            "file_url": payload.file_url,
            "stt_conf": payload.stt_conf
        })

        msg_id = res.lastrowid
        detection = None

        if payload.speaker == "CLIENT":
            detection = detect_dropout_signal(payload.text)
            if detection:
                db.execute(text("""
                    INSERT INTO alert (sess_id, msg_id, type, status, score, rule, at)
                    VALUES (:sid, :mid, :type, :status, :score, :rule, NOW())
                """), {
                    "sid": payload.sess_id,
                    "mid": msg_id,
                    "type": detection["type"],
                    "status": detection["status"],
                    "score": detection["score"],
                    "rule": detection["rule"]
                })

        db.commit()
        return {"status": "saved", "msg_id": msg_id, "detection": detection}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================
# Streamlit 필수 API 3개
# - /sessions/{id}/dashboard
# - /sessions/{id}/messages
# - /sessions/{id}/alerts
# =========================================================
@app.get("/sessions/{sess_id}/dashboard")
def session_dashboard(sess_id: int, db: Session = Depends(get_db)):
    sess = db.execute(text("""
        SELECT
            id, uuid, counselor_id, client_id, appt_id,
            channel, progress, start_at, end_at, end_reason,
            sat, sat_note, ok_text, ok_voice, ok_face, created_at
        FROM sess
        WHERE id = :sid
    """), {"sid": sess_id}).mappings().first()

    if not sess:
        raise HTTPException(status_code=404, detail="sess_id not found")

    risk_score = db.execute(text("""
        SELECT COALESCE(AVG(score), 0)
        FROM alert
        WHERE sess_id = :sid
    """), {"sid": sess_id}).scalar()

    return {
        "session": jsonable_encoder(sess),
        "risk_score": float(risk_score or 0.0)
    }


@app.get("/sessions/{sess_id}/messages")
def session_messages(
    sess_id: int,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    sql = f"""
        SELECT
            id, sess_id, speaker, speaker_id, text, emoji, file_url, stt_conf, at
        FROM msg
        WHERE sess_id = :sid
        ORDER BY at DESC
        LIMIT {int(limit)}
    """
    result = db.execute(text(sql), {"sid": sess_id}).mappings().all()
    return {"items": jsonable_encoder(list(result))}


@app.get("/sessions/{sess_id}/alerts")
def session_alerts(sess_id: int, db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT
            id, sess_id, msg_id, type, status, score, rule, action, at
        FROM alert
        WHERE sess_id = :sid
        ORDER BY at DESC
        LIMIT 200
    """), {"sid": sess_id}).mappings().all()
    return {"items": jsonable_encoder(list(result))}


# =========================================================
# Dashboard Support APIs (Streamlit이 호출하는 통계들)
# =========================================================
@app.get("/stats/topic-dropout")
def topic_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    result = _rows(db, """
        SELECT
            s.channel AS channel,
            COUNT(*) AS total,
            (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(*),0)) * 100 AS dropout_rate
        FROM sess s
        WHERE s.counselor_id = :cid
        GROUP BY s.channel
        ORDER BY dropout_rate DESC
    """, {"cid": counselor_id})
    return {"items": jsonable_encoder(result)}


@app.get("/stats/client-grade-dropout")
def client_grade_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    result = _rows(db, """
        SELECT
            c.status AS client_grade,
            COUNT(*) AS total
        FROM client c
        JOIN sess s ON s.client_id = c.id
        WHERE s.counselor_id = :cid
        GROUP BY c.status
        ORDER BY total DESC
    """, {"cid": counselor_id})
    return {"items": jsonable_encoder(result)}


@app.get("/stats/missed-alerts")
def stats_missed_alerts(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT
            s.id AS sess_id,
            s.uuid,
            s.start_at,
            s.end_at,
            TIMESTAMPDIFF(MINUTE, s.start_at, s.end_at) AS duration_min
        FROM sess s
        WHERE s.counselor_id = :cid
          AND s.end_reason = 'DROPOUT'
          AND (SELECT COUNT(*) FROM alert a WHERE a.sess_id = s.id) = 0
        ORDER BY s.start_at DESC
        LIMIT 200
    """), {"cid": counselor_id}).mappings().all()
    return {"items": jsonable_encoder(list(result))}


@app.get("/stats/time-dropout")
def stats_time_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT
            HOUR(s.start_at) AS hour,
            COUNT(*) AS total,
            (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(*),0)) * 100 AS dropout_rate
        FROM sess s
        WHERE s.counselor_id = :cid
        GROUP BY HOUR(s.start_at)
        ORDER BY hour ASC
    """), {"cid": counselor_id}).mappings().all()
    return {"items": jsonable_encoder(list(result))}


@app.get("/stats/channel-dropout")
def stats_channel_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT
            s.channel AS channel,
            COUNT(*) AS total,
            (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(*),0)) * 100 AS dropout_rate
        FROM sess s
        WHERE s.counselor_id = :cid
        GROUP BY s.channel
        ORDER BY dropout_rate DESC
    """), {"cid": counselor_id}).mappings().all()
    return {"items": jsonable_encoder(list(result))}


@app.get("/stats/monthly-growth")
def stats_monthly_growth(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT
            DATE_FORMAT(s.start_at, '%Y-%m') AS month,
            COUNT(*) AS total,
            (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(*),0)) * 100 AS dropout_rate
        FROM sess s
        WHERE s.counselor_id = :cid
        GROUP BY DATE_FORMAT(s.start_at, '%Y-%m')
        ORDER BY month ASC
    """), {"cid": counselor_id}).mappings().all()
    return {"items": jsonable_encoder(list(result))}
