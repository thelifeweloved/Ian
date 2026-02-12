from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime

class SessionItem(BaseModel):
    id: int
    uuid: str
    counselor_id: int
    client_id: int
    appt_id: Optional[int] = None
    channel: str
    progress: str
    start_at: datetime
    end_at: Optional[datetime] = None
    end_reason: Optional[str] = None
    sat: Optional[bool] = None
    sat_note: Optional[str] = None
    ok_text: bool
    ok_voice: bool
    ok_face: bool
    created_at: datetime

class MessageItem(BaseModel):
    id: int
    sess_id: int
    speaker: str
    speaker_id: Optional[int] = None
    text: Optional[str] = None
    emoji: Optional[str] = None
    file_url: Optional[str] = None
    stt_conf: float
    at: datetime

class AlertItem(BaseModel):
    id: int
    sess_id: int
    msg_id: int
    type: str
    status: str
    score: Optional[float] = None
    rule: Optional[str] = None
    action: Optional[str] = None
    at: datetime

class QualityItem(BaseModel):
    id: int
    sess_id: int
    flow: float
    score: float
    created_at: datetime

class SessAnalysisItem(BaseModel):
    id: int
    sess_id: int
    topic_id: int
    summary: str
    note: str
    created_at: datetime
