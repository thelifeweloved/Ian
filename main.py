import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
from db import get_db
# 하이퍼 클로바 X AI 상담 도우미 연결 (routers/helper.py)
from routers.helper import router as helper_router

# 1. 앱 초기화 및 미들웨어 설정
load_dotenv()
app = FastAPI(title="Mindway Post-Analysis API", version="1.1.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(helper_router)

# =========================================================
# 2. Pydantic Models (400 Bad Request 방지용 필수 수정)
# =========================================================
class LoginRequest(BaseModel):
    email: str
    pwd: str

class ClientLoginRequest(BaseModel):
    phone: str
    code: str

class SignupRequest(BaseModel):
    role: str
    name: str
    # client는 pwd 없음 (명세서 기준)
    email: Optional[str] = None
    phone: Optional[str] = None
    pwd: Optional[str] = None  # counselor일 때만 사용

class MessageCreate(BaseModel):
    sess_id: int = Field(..., ge=1)
    speaker: str = Field(..., pattern="^(COUNSELOR|CLIENT|SYSTEM)$")
    speaker_id: Optional[int] = Field(None, ge=1)
    text: Optional[str] = None
    emoji: Optional[str] = None
    file_url: Optional[str] = None
    stt_conf: float = Field(0.0, ge=0.0, le=1.0)

# =========================================================
# 3. Helpers & Logic
# =========================================================
def detect_dropout_signal(message: Optional[str]) -> Optional[Dict[str, Any]]:
    if not message:
        return None
    msg = message.strip()
    score = 0.0
    rules = []
    action = ""

    if any(kw in msg for kw in ["그만", "힘들", "포기", "싫어", "의미없"]):
        score += 0.5
        rules.append("NEG_KEYWORD")
        action = "내담자의 정서적 소진 신호가 감지되었습니다. 지지와 공감이 필요합니다."

    if score >= 0.5:
        return {
            "type": "CONTINUITY_SIGNAL",
            "status": "DETECTED",
            "score": round(min(score, 1.0), 2),
            "rule": "|".join(rules)[:50],
            "action": action
        }
    return None

# =========================================================
# 4. Auth (명세서 기준: client는 pwd 없음)
# =========================================================

@app.post("/auth/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        role = (payload.role or "").strip().lower()

        if role == "counselor":
            # 상담사 가입: email/pwd/name 필수
            if not payload.email:
                raise HTTPException(status_code=400, detail="상담사는 이메일이 필수입니다.")
            if not payload.pwd:
                raise HTTPException(status_code=400, detail="상담사는 비밀번호가 필수입니다.")

            sql = "INSERT INTO counselor (email, pwd, name) VALUES (:email, :pwd, :name)"
            params = {"email": payload.email, "pwd": payload.pwd, "name": payload.name}

        elif role == "client":
            # 내담자 등록: phone/name 필수, pwd 없음
            if not payload.phone:
                raise HTTPException(status_code=400, detail="내담자는 전화번호가 필수입니다.")

            clean_phone = "".join(filter(str.isdigit, payload.phone))
            client_code = f"CL-{uuid.uuid4().hex[:8].upper()}"

            sql = """
                INSERT INTO client (code, name, phone, status, active)
                VALUES (:code, :name, :phone, '안정', TRUE)
            """
            params = {"code": client_code, "name": payload.name, "phone": clean_phone}

        else:
            raise HTTPException(status_code=400, detail="role은 counselor 또는 client 여야 합니다.")

        db.execute(text(sql), params)
        db.commit()
        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"DEBUG DB ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=f"가입 처리 중 오류 발생: {str(e)}")


@app.post("/login")
def counselor_login(payload: LoginRequest, db: Session = Depends(get_db)):
    # 상담사 로그인 (email + pwd)
    sql = "SELECT id, name FROM counselor WHERE email = :email AND pwd = :pwd"
    counselor = db.execute(text(sql), {"email": payload.email, "pwd": payload.pwd}).mappings().first()

    if counselor:
        return {
            "status": "success",
            "role": "counselor",
            "counselor_id": counselor["id"],
            "counselor_name": counselor["name"]
        }

    raise HTTPException(status_code=401, detail="계정 정보가 일치하지 않습니다.")


@app.post("/client/login")
def client_login(payload: ClientLoginRequest, db: Session = Depends(get_db)):
    # 내담자 입장 (phone + code)  ※ pwd 없음
    clean_phone = "".join(filter(str.isdigit, payload.phone or ""))
    clean_code = (payload.code or "").strip()

    if not clean_phone:
        raise HTTPException(status_code=400, detail="전화번호가 필요합니다.")
    if not clean_code:
        raise HTTPException(status_code=400, detail="내담자 코드가 필요합니다.")

    row = db.execute(text("""
        SELECT id, name, code
        FROM client
        WHERE phone = :phone AND code = :code AND active = TRUE
        LIMIT 1
    """), {"phone": clean_phone, "code": clean_code}).mappings().first()

    if not row:
        raise HTTPException(status_code=401, detail="전화번호/코드가 일치하지 않습니다.")

    return {
        "status": "success",
        "role": "client",
        "client_id": row["id"],
        "client_name": row["name"],
        "client_code": row["code"]
    }

class ClientStartSessionRequest(BaseModel):
    client_id: int = Field(..., ge=1)
    counselor_id: int = Field(..., ge=1)

@app.post("/client/start-session")
def client_start_session(payload: ClientStartSessionRequest, db: Session = Depends(get_db)):
    # 1) 진행중(미종료) 세션 재사용: progress가 ACTIVE/WAITING 이고 end_at이 비어있으면 재사용
    existing = db.execute(text("""
        SELECT id
        FROM sess
        WHERE client_id = :clid
          AND counselor_id = :coid
          AND (end_at IS NULL)
          AND (progress IN ('WAITING','ACTIVE'))
        ORDER BY id DESC
        LIMIT 1
    """), {"clid": payload.client_id, "coid": payload.counselor_id}).scalar()

    if existing:
        return {"status": "success", "sess_id": int(existing), "reused": True}

    # 2) 없으면 새로 생성 (schema 기준: uuid 필수)
    new_uuid = str(uuid.uuid4())
    res = db.execute(text("""
        INSERT INTO sess (uuid, counselor_id, client_id, channel, progress)
        VALUES (:uuid, :coid, :clid, 'CHAT', 'ACTIVE')
    """), {"uuid": new_uuid, "coid": payload.counselor_id, "clid": payload.client_id})

    db.commit()
    return {"status": "success", "sess_id": int(res.lastrowid), "reused": False}

@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        v = db.execute(text("SELECT 1")).scalar()
        return {"db": "ok", "ping": v, "port": 3307}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Connection Error: {str(e)}")

# =========================================================
# 5. Core APIs (기존 기능 100% 보존 - 수정 없음)
# =========================================================
@app.get("/sessions")
def list_sessions(counselor_id: Optional[int] = Query(None, ge=1), limit: int = Query(50), db: Session = Depends(get_db)):
    sql = """
        SELECT s.*, c.name AS client_name, c.status AS client_status
        FROM sess s JOIN client c ON c.id = s.client_id
        WHERE (:cid IS NULL OR s.counselor_id = :cid)
        ORDER BY s.id DESC LIMIT :l
    """
    result = db.execute(text(sql), {"cid": counselor_id, "l": limit}).mappings().all()
    return {"items": jsonable_encoder(result)}

@app.post("/messages")
def create_message(payload: MessageCreate, db: Session = Depends(get_db)):
    try:
        res = db.execute(text("""
            INSERT INTO msg (sess_id, speaker, speaker_id, text, emoji, file_url, stt_conf, at)
            VALUES (:sid, :speaker, :speaker_id, :text, :emoji, :file_url, :stt_conf, NOW())
        """), {
            "sid": payload.sess_id, "speaker": payload.speaker, 
            "speaker_id": None if payload.speaker == "SYSTEM" else payload.speaker_id,
            "text": payload.text, "emoji": payload.emoji, "file_url": payload.file_url, "stt_conf": payload.stt_conf
        })

        msg_id = res.lastrowid
        detection = None

        if payload.speaker == "CLIENT":
            detection = detect_dropout_signal(payload.text)
            if detection:
                db.execute(text("""
                    INSERT INTO alert (sess_id, msg_id, type, status, score, rule, action, at)
                    VALUES (:sid, :mid, :type, :status, :score, :rule, :action, NOW())
                """), {
                    "sid": payload.sess_id, "mid": msg_id, "type": detection["type"],
                    "status": detection["status"], "score": detection["score"],
                    "rule": detection["rule"], "action": detection["action"]
                })

        db.commit()
        return {"status": "saved", "msg_id": msg_id, "detection": detection}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sessions/{sess_id}/dashboard")
def session_dashboard(sess_id: int, db: Session = Depends(get_db)):
    sess_sql = """
        SELECT s.*, c.name AS client_name, c.status AS client_status
        FROM sess s JOIN client c ON c.id = s.client_id WHERE s.id = :sid
    """
    sess = db.execute(text(sess_sql), {"sid": sess_id}).mappings().first()
    if not sess: raise HTTPException(status_code=404, detail="sess_id not found")

    risk_score = float(db.execute(text("SELECT COALESCE(AVG(score), 0) FROM alert WHERE sess_id = :sid"), {"sid": sess_id}).scalar() or 0.0)
    
    topic_analysis = db.execute(text("""
        SELECT t.name as topic_name, sa.summary, sa.note
        FROM sess_analysis sa JOIN topic t ON sa.topic_id = t.id WHERE sa.sess_id = :sid
    """), {"sid": sess_id}).mappings().all()

    return {
        "session": jsonable_encoder(sess),
        "risk_score": risk_score,
        "topic_analysis": jsonable_encoder(topic_analysis),
        "risk_label": "HIGH" if risk_score >= 0.7 else "MID" if risk_score >= 0.4 else "LOW"
    }

@app.get("/sessions/{sess_id}/messages")
def session_messages(sess_id: int, limit: int = Query(200, ge=1), db: Session = Depends(get_db)):
    sql = "SELECT id, sess_id, speaker, speaker_id, text, emoji, file_url, stt_conf, at FROM msg WHERE sess_id = :sid ORDER BY at DESC LIMIT :l"
    result = db.execute(text(sql), {"sid": sess_id, "l": limit}).mappings().all()
    return {"items": jsonable_encoder(list(result))}

@app.get("/sessions/{sess_id}/alerts")
def session_alerts(sess_id: int, limit: int = Query(200, ge=1, le=500), db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM alert WHERE sess_id = :sid ORDER BY at DESC LIMIT :l"), {"sid": sess_id, "l": limit}).mappings().all()
    return {"items": jsonable_encoder(list(result))}

@app.get("/appointments")
def get_appointments(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    sql = "SELECT a.id, c.name AS client_name, a.at, a.status, c.status AS client_grade FROM appt a JOIN client c ON a.client_id = c.id WHERE a.counselor_id = :cid ORDER BY a.at ASC"
    return {"items": jsonable_encoder(list(db.execute(text(sql), {"cid": counselor_id}).mappings().all()))}

# =========================================================
# 6. Stats APIs (기존 통계 기능 100% 보존)
# =========================================================
@app.get("/stats/topic-dropout")
def topic_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    sql = """
        SELECT t.name AS topic_name, COUNT(s.id) AS total,
               (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(s.id), 0)) * 100 AS dropout_rate,
               AVG(s.sat) * 100 AS avg_sat_rate
        FROM topic t JOIN sess_analysis sa ON t.id = sa.topic_id JOIN sess s ON sa.sess_id = s.id
        WHERE s.counselor_id = :cid GROUP BY t.id ORDER BY dropout_rate DESC
    """
    return {"items": jsonable_encoder(list(db.execute(text(sql), {"cid": counselor_id}).mappings().all()))}

@app.get("/stats/quality-trend")
def quality_trend(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    sql = """
        SELECT DATE(s.start_at) AS date_label, AVG(s.sat) * 100 AS avg_sat_rate, AVG(a.score) AS avg_risk_score
        FROM sess s LEFT JOIN alert a ON s.id = a.sess_id
        WHERE s.counselor_id = :cid GROUP BY DATE(s.start_at) ORDER BY DATE(s.start_at) ASC
    """
    result = db.execute(text(sql), {"cid": counselor_id}).mappings().all()
    formatted = [{"date_label": r["date_label"].strftime('%m-%d'), "avg_sat_rate": float(r["avg_sat_rate"] or 0), "avg_risk_score": float(r["avg_risk_score"] or 0)} for r in result]
    return {"items": jsonable_encoder(formatted)}

@app.get("/stats/client-grade-dropout")
def client_grade_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    sql = "SELECT c.status AS client_grade, COUNT(*) AS total FROM client c JOIN sess s ON s.client_id = c.id WHERE s.counselor_id = :cid GROUP BY c.status ORDER BY total DESC"
    return {"items": jsonable_encoder(list(db.execute(text(sql), {"cid": counselor_id}).mappings().all()))}

@app.get("/stats/time-dropout")
def stats_time_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    sql = "SELECT HOUR(s.start_at) AS hour, COUNT(*) AS total, (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(*),0)) * 100 AS dropout_rate FROM sess s WHERE s.counselor_id = :cid GROUP BY hour ORDER BY hour ASC"
    return {"items": jsonable_encoder(list(db.execute(text(sql), {"cid": counselor_id}).mappings().all()))}

@app.get("/stats/channel-dropout")
def stats_channel_dropout(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    sql = "SELECT s.channel, COUNT(*) AS total, (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(*),0)) * 100 AS dropout_rate, AVG(s.sat) * 100 AS avg_sat_rate FROM sess s WHERE s.counselor_id = :cid GROUP BY s.channel ORDER BY dropout_rate DESC"
    return {"items": jsonable_encoder(list(db.execute(text(sql), {"cid": counselor_id}).mappings().all()))}

@app.get("/stats/monthly-growth")
def stats_monthly_growth(counselor_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    sql = "SELECT DATE_FORMAT(s.start_at, '%Y-%m') AS month, COUNT(*) AS total, (COUNT(CASE WHEN s.end_reason='DROPOUT' THEN 1 END) / NULLIF(COUNT(*),0)) * 100 AS dropout_rate FROM sess s WHERE s.counselor_id = :cid GROUP BY month ORDER BY month ASC"
    return {"items": jsonable_encoder(list(db.execute(text(sql), {"cid": counselor_id}).mappings().all()))}