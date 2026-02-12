USE mindway;

SET FOREIGN_KEY_CHECKS=0;
TRUNCATE TABLE alert;
TRUNCATE TABLE quality;
TRUNCATE TABLE text_emotion;
TRUNCATE TABLE msg;
TRUNCATE TABLE sess;
TRUNCATE TABLE appt;
TRUNCATE TABLE client_topic;
TRUNCATE TABLE topic;
TRUNCATE TABLE client;
TRUNCATE TABLE counselor;
SET FOREIGN_KEY_CHECKS=1;

INSERT INTO counselor (id,email,pwd,name,role,active) VALUES (1,'c1@example.com','x','c1','USER',1);

-- status는 제약 때문에 반드시 이 3개 중 하나(안정/주의/개선필요)
INSERT INTO client (id,code,name,status,phone,active) VALUES (1,'CL001','u1','주의',NULL,1);

INSERT INTO topic (id,code,name,type,descr) VALUES (1,'T1','career','REGISTER','reg topic'),(2,'T2','anxiety','AI','ai topic');

INSERT INTO appt (id,client_id,counselor_id,at,status) VALUES (1,1,1,NOW(),'CONFIRMED');

INSERT INTO sess (id,uuid,counselor_id,client_id,appt_id,channel,progress,start_at,end_at,end_reason,sat,sat_note,ok_text,ok_voice,ok_face,created_at)
VALUES (1,'S-UUID-0001',1,1,1,'CHAT','IN_PROGRESS',NOW(),NULL,NULL,NULL,NULL,1,0,0,NOW());

INSERT INTO msg (id,sess_id,speaker,speaker_id,text,stt_conf,at) VALUES
(1,1,'CLIENT',1,'tired',0.0,NOW()),
(2,1,'COUNSELOR',1,'tell me more',0.0,NOW());

INSERT INTO quality (id,sess_id,flow,score,created_at) VALUES (1,1,2.0,3.5,NOW());
