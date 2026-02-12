USE mindway;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE file;
TRUNCATE TABLE sess_analysis;
TRUNCATE TABLE text_emotion;
TRUNCATE TABLE client_topic;
TRUNCATE TABLE alert;
TRUNCATE TABLE quality;
TRUNCATE TABLE face;
TRUNCATE TABLE stt;
TRUNCATE TABLE msg;
TRUNCATE TABLE sess;
TRUNCATE TABLE appt;
TRUNCATE TABLE topic;
TRUNCATE TABLE client;
TRUNCATE TABLE counselor;

SET FOREIGN_KEY_CHECKS = 1;

/* 1) counselor */
INSERT INTO counselor (id, email, pwd, name, role, active)
VALUES (1, 'c1@example.com', 'hashed_pwd_1', '상담사1', 'USER', TRUE);

/* 2) client */
INSERT INTO client (id, code, name, status, phone, active)
VALUES (1, 'CL001', '내담자1', '주의', '010-1234-5678', TRUE);

/* 3) topic */
INSERT INTO topic (id, code, name, type, descr)
VALUES
(1, 'T_REG_01', '진로 고민', 'REGISTER', '가입 시 선택하는 고민 유형'),
(2, 'T_AI_01',  '불안/걱정', 'AI',       'AI 분석 토픽(불안 관련)');

/* 4) appt */
INSERT INTO appt (id, client_id, counselor_id, at, status)
VALUES (1, 1, 1, NOW() + INTERVAL 1 DAY, 'CONFIRMED');

/* 5) sess */
INSERT INTO sess (
  id, uuid, counselor_id, client_id, appt_id, channel, progress,
  start_at, end_at, end_reason, sat, sat_note, ok_text, ok_voice, ok_face, created_at
)
VALUES
(1, 'S-UUID-0001', 1, 1, 1, 'CHAT', 'IN_PROGRESS',
 NOW() - INTERVAL 5 MINUTE, NULL, NULL, NULL, NULL, TRUE, FALSE, FALSE, NOW() - INTERVAL 5 MINUTE);

/* 6) msg (상담사/내담자 텍스트 모두 저장됨) */
INSERT INTO msg (id, sess_id, speaker, speaker_id, text, emoji, file_url, stt_conf, at)
VALUES
(1, 1, 'CLIENT',    1, '요즘 너무 불안하고 잠이 잘 안 와요.', NULL, NULL, 0.0, NOW() - INTERVAL 280 SECOND),
(2, 1, 'COUNSELOR', 1, '불안이 커진 계기가 있었을까요? 최근 상황을 조금 더 말해줘도 좋아요.', NULL, NULL, 0.0, NOW() - INTERVAL 260 SECOND),
(3, 1, 'CLIENT',    1, '회사 일이 너무 힘들고, 계속 못할 것 같아요.', NULL, NULL, 0.0, NOW() - INTERVAL 240 SECOND),
(4, 1, 'COUNSELOR', 1, '그렇게 느끼는 건 자연스러워요. 최근 가장 부담됐던 순간을 하나만 골라볼까요?', NULL, NULL, 0.0, NOW() - INTERVAL 210 SECOND),
(5, 1, 'CLIENT',    1, '그냥… 모르겠어요. 아무것도 하기 싫어요.', NULL, NULL, 0.0, NOW() - INTERVAL 60 SECOND);

/* 7) text_emotion */
INSERT INTO text_emotion (id, msg_id, label, score, meta, created_at)
VALUES
(1, 1, 'anxiety', 0.82, JSON_OBJECT('model','demo','ver','1.0'), NOW() - INTERVAL 279 SECOND),
(2, 3, 'sadness', 0.76, JSON_OBJECT('model','demo','ver','1.0'), NOW() - INTERVAL 239 SECOND),
(3, 5, 'depression', 0.90, JSON_OBJECT('model','demo','ver','1.0'), NOW() - INTERVAL 59 SECOND);

/* 8) alert (초기 1건) */
INSERT INTO alert (id, sess_id, msg_id, type, status, score, rule, action, at)
VALUES
(1, 1, 5, 'NEG_SPIKE', 'OPEN', 0.90, 'EMO_NEG_0.85', '공감 + 구체 질문으로 재참여 유도', NOW() - INTERVAL 50 SECOND);

/* 9) quality (세션당 1건) */
INSERT INTO quality (id, sess_id, flow, score, created_at)
VALUES (1, 1, 2.5, 3.8, NOW() - INTERVAL 10 SECOND);

/* 10) sess_analysis */
INSERT INTO sess_analysis (id, sess_id, topic_id, summary, note, created_at)
VALUES
(1, 1, 2, '내담자는 업무 스트레스로 인한 불안/무기력 표현이 증가함.', '원인 탐색 질문으로 대화 유지.', NOW() - INTERVAL 5 SECOND);

/* 11) client_topic */
INSERT INTO client_topic (id, client_id, topic_id, prio, created_at)
VALUES (1, 1, 1, 1, NOW() - INTERVAL 1 DAY);

/* 12) file */
INSERT INTO file (id, counselor_id, client_id, sess_id, name, size, ext, status, uploaded_at, deleted_at)
VALUES (1, 1, 1, 1, 'note.txt', 123, 'txt', 'UPLOADED', NOW() - INTERVAL 1 HOUR, NULL);