# services/session_repo.py
# DB에서 상담 대화 로더 "분석에 넣을 원문 대화텍스트를 DB에서 뽑아오는 역할"
import pymysql

def load_dialog_text(
    sess_id: int,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str
) -> str:
    conn = pymysql.connect(
        host=host, port=port, user=user, password=password,
        database=database, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn.cursor() as cur:
        cur.execute("""
            SELECT sender_type, text
            FROM msg
            WHERE sess_id=%s
            ORDER BY at ASC, id ASC
        """, (sess_id,))
        rows = cur.fetchall()
    conn.close()

    return "\n".join([f"{r['sender_type']}: {r['text']}" for r in rows])
# services/session_repo.py (추가 함수 예시)

def load_msg_rows(sess_id: int, host: str, port: int, user: str, password: str, database: str):
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, sender_type, text
                FROM msg
                WHERE sess_id=%s
                ORDER BY at ASC, id ASC
            """, (sess_id,))
            rows = cur.fetchall()
    finally:
        conn.close()

    out = []
    for i, r in enumerate(rows):
        text = (r.get("text", "") or "").strip()
        if not text:
            continue
        out.append({
            "idx": i,
            "msg_id": r["id"],
            "speaker": r.get("sender_type", "UNKNOWN"),
            "text": r.get("text", "") or "",
        })
    return out