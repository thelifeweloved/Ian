/* =========================================================
  mindway init.sql
  - Docker MySQL 초기화 시 자동 실행(/docker-entrypoint-initdb.d)
  - utf8mb4 + KST(+09:00)
  - 14 tables (FK 순서 안전)
========================================================= */

SET NAMES utf8mb4;
SET time_zone = '+09:00';

CREATE DATABASE IF NOT EXISTS mindway;
USE mindway;

/* =========================
  1) counselor
========================= */
CREATE TABLE IF NOT EXISTS counselor (
  id BIGINT NOT NULL AUTO_INCREMENT,
  email VARCHAR(50) NOT NULL,
  pwd VARCHAR(255) NOT NULL,
  name VARCHAR(50) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'USER',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_counselor_email (email)
) COMMENT='counselor';

/* =========================
  2) client
  - status: VARCHAR + CHECK (복붙/ENUM 문제 회피)
========================= */
CREATE TABLE IF NOT EXISTS client (
  id BIGINT NOT NULL AUTO_INCREMENT,
  code VARCHAR(30) NOT NULL,
  name VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL,
  phone VARCHAR(20) NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_client_code (code),
  KEY ix_client_name (name),
  CONSTRAINT ck_client_status CHECK (status IN ('안정','주의','개선필요'))
) COMMENT='client';

/* =========================
  3) topic
  - type: VARCHAR + CHECK
========================= */
CREATE TABLE IF NOT EXISTS topic (
  id BIGINT NOT NULL AUTO_INCREMENT,
  code VARCHAR(20) NOT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(20) NOT NULL,
  descr TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_topic_code (code),
  KEY ix_topic_name (name),
  KEY ix_topic_type (type),
  CONSTRAINT ck_topic_type CHECK (type IN ('REGISTER','AI'))
) COMMENT='topic';

/* =========================
  4) appt
========================= */
CREATE TABLE IF NOT EXISTS appt (
  id BIGINT NOT NULL AUTO_INCREMENT,
  client_id BIGINT NOT NULL,
  counselor_id BIGINT NULL,
  at TIMESTAMP NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'REQUESTED',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_appt_client_time (client_id, at),
  KEY ix_appt_counselor_time (counselor_id, at),
  KEY ix_appt_status (status),
  CONSTRAINT fk_appt_client
    FOREIGN KEY (client_id) REFERENCES client(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_appt_counselor
    FOREIGN KEY (counselor_id) REFERENCES counselor(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='appt';

/* =========================
  5) sess
========================= */
CREATE TABLE IF NOT EXISTS sess (
  id BIGINT NOT NULL AUTO_INCREMENT,
  uuid VARCHAR(50) NOT NULL,
  counselor_id BIGINT NOT NULL,
  client_id BIGINT NOT NULL,
  appt_id BIGINT NULL,
  channel VARCHAR(10) NOT NULL DEFAULT 'CHAT',
  progress VARCHAR(20) NOT NULL,
  start_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  end_at TIMESTAMP NULL,
  end_reason VARCHAR(10) NULL,
  sat BOOLEAN NULL,
  sat_note VARCHAR(255) NULL,
  ok_text BOOLEAN NOT NULL DEFAULT TRUE,
  ok_voice BOOLEAN NOT NULL DEFAULT FALSE,
  ok_face BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_sess_uuid (uuid),
  KEY ix_sess_counselor_start (counselor_id, start_at),
  KEY ix_sess_client_start (client_id, start_at),
  KEY ix_sess_channel_progress (channel, progress),
  CONSTRAINT ck_sess_channel CHECK (channel IN ('CHAT','VOICE')),
  CONSTRAINT ck_sess_end_reason CHECK (end_reason IS NULL OR end_reason IN ('NORMAL','DROPOUT','TECH','UNKNOWN')),
  CONSTRAINT fk_sess_counselor
    FOREIGN KEY (counselor_id) REFERENCES counselor(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_sess_client
    FOREIGN KEY (client_id) REFERENCES client(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_sess_appt
    FOREIGN KEY (appt_id) REFERENCES appt(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='sess';

/* =========================
  6) msg
========================= */
CREATE TABLE IF NOT EXISTS msg (
  id BIGINT NOT NULL AUTO_INCREMENT,
  sess_id BIGINT NOT NULL,
  speaker VARCHAR(20) NOT NULL,
  speaker_id BIGINT NULL,
  text TEXT NULL,
  emoji TEXT NULL,
  file_url TEXT NULL,
  stt_conf DECIMAL(5,4) NOT NULL DEFAULT 0.0,
  at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_msg_id_sess (id, sess_id),
  KEY ix_msg_sess_time (sess_id, at),
  KEY ix_msg_speaker (speaker, speaker_id),
  CONSTRAINT ck_msg_speaker CHECK (speaker IN ('COUNSELOR','CLIENT','SYSTEM')),
  CONSTRAINT fk_msg_sess
    FOREIGN KEY (sess_id) REFERENCES sess(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='msg';

/* =========================
  7) stt
========================= */
CREATE TABLE IF NOT EXISTS stt (
  id BIGINT NOT NULL AUTO_INCREMENT,
  sess_id BIGINT NOT NULL,
  speaker VARCHAR(20) NOT NULL,
  s_ms INT UNSIGNED NOT NULL,
  e_ms INT UNSIGNED NOT NULL,
  text TEXT NOT NULL,
  conf DECIMAL(5,4) NOT NULL DEFAULT 0.0,
  meta JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_stt_sess_time (sess_id, s_ms, e_ms),
  KEY ix_stt_speaker (speaker),
  CONSTRAINT ck_stt_speaker CHECK (speaker IN ('COUNSELOR','CLIENT')),
  CONSTRAINT fk_stt_sess
    FOREIGN KEY (sess_id) REFERENCES sess(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='stt';

/* =========================
  8) face
========================= */
CREATE TABLE IF NOT EXISTS face (
  id BIGINT NOT NULL AUTO_INCREMENT,
  sess_id BIGINT NOT NULL,
  at TIMESTAMP NOT NULL,
  label VARCHAR(30) NULL,
  score DECIMAL(5,4) NULL,
  dist JSON NOT NULL,
  meta JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_face_sess_time (sess_id, at),
  CONSTRAINT fk_face_sess
    FOREIGN KEY (sess_id) REFERENCES sess(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='face';

/* =========================
  9) quality
========================= */
CREATE TABLE IF NOT EXISTS quality (
  id BIGINT NOT NULL AUTO_INCREMENT,
  sess_id BIGINT NOT NULL,
  flow DECIMAL(4,1) NOT NULL,
  score DECIMAL(4,1) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_quality_sess (sess_id),
  CONSTRAINT fk_quality_sess
    FOREIGN KEY (sess_id) REFERENCES sess(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='quality';

/* =========================
  10) alert
========================= */
CREATE TABLE IF NOT EXISTS alert (
  id BIGINT NOT NULL AUTO_INCREMENT,
  sess_id BIGINT NOT NULL,
  msg_id BIGINT NOT NULL,
  type VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL,
  score DECIMAL(5,4) NULL,
  rule VARCHAR(50) NULL,
  action TEXT NULL,
  at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_alert_sess_time (sess_id, at),
  KEY ix_alert_type_status (type, status),
  CONSTRAINT ck_alert_type CHECK (type IN ('DELAY','SHORT','NEG_SPIKE','RISK_WORD')),
  CONSTRAINT fk_alert_sess
    FOREIGN KEY (sess_id) REFERENCES sess(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_alert_msg_same_sess
    FOREIGN KEY (msg_id, sess_id) REFERENCES msg(id, sess_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='alert';

/* =========================
  11) client_topic
========================= */
CREATE TABLE IF NOT EXISTS client_topic (
  id BIGINT NOT NULL AUTO_INCREMENT,
  client_id BIGINT NOT NULL,
  topic_id BIGINT NOT NULL,
  prio TINYINT NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_client_topic (client_id, topic_id),
  KEY ix_client_topic_prio (client_id, prio),
  CONSTRAINT fk_client_topic_client
    FOREIGN KEY (client_id) REFERENCES client(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_client_topic_topic
    FOREIGN KEY (topic_id) REFERENCES topic(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='client_topic';

/* =========================
  12) text_emotion
========================= */
CREATE TABLE IF NOT EXISTS text_emotion (
  id BIGINT NOT NULL AUTO_INCREMENT,
  msg_id BIGINT NOT NULL,
  label VARCHAR(30) NOT NULL,
  score DECIMAL(5,4) NOT NULL DEFAULT 0.0,
  meta JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_text_emotion_msg_time (msg_id, created_at),
  KEY ix_text_emotion_label (label),
  CONSTRAINT fk_text_emotion_msg
    FOREIGN KEY (msg_id) REFERENCES msg(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='text_emotion';

/* =========================
  13) sess_analysis
========================= */
CREATE TABLE IF NOT EXISTS sess_analysis (
  id BIGINT NOT NULL AUTO_INCREMENT,
  sess_id BIGINT NOT NULL,
  topic_id BIGINT NOT NULL,
  summary TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_sess_topic (sess_id, topic_id),
  KEY ix_sess_analysis_time (sess_id, created_at),
  CONSTRAINT fk_sess_analysis_sess
    FOREIGN KEY (sess_id) REFERENCES sess(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_sess_analysis_topic
    FOREIGN KEY (topic_id) REFERENCES topic(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='sess_analysis';

/* =========================
  14) file
========================= */
CREATE TABLE IF NOT EXISTS file (
  id BIGINT NOT NULL AUTO_INCREMENT,
  counselor_id BIGINT NOT NULL,
  client_id BIGINT NOT NULL,
  sess_id BIGINT NULL,
  name TEXT NOT NULL,
  size INT UNSIGNED NOT NULL DEFAULT 0,
  ext VARCHAR(30) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_file_sess (sess_id),
  KEY ix_file_client_time (client_id, uploaded_at),
  KEY ix_file_counselor_time (counselor_id, uploaded_at),
  CONSTRAINT fk_file_counselor
    FOREIGN KEY (counselor_id) REFERENCES counselor(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_file_client
    FOREIGN KEY (client_id) REFERENCES client(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_file_sess
    FOREIGN KEY (sess_id) REFERENCES sess(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) COMMENT='file';
