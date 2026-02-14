-- =====================================================
-- 테이블 명세서 최종 완벽 버전
-- 작성일: 2026.02.14
-- 작성자: 정이안
-- 과제명: 상담사를 위한 상담 이탈 품질 분석 기반 AI 리포트 서비스
-- =====================================================
-- 제미나이 정리 + 명세서 인덱스 전부 복구
-- =====================================================

-- 1. 상담사 테이블 (counselor)
CREATE TABLE IF NOT EXISTS counselor (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    email      VARCHAR(50) NOT NULL,
    pwd        VARCHAR(255) NOT NULL,
    name       VARCHAR(50) NOT NULL,
    role       ENUM('ADMIN', 'USER') NOT NULL DEFAULT 'USER',
    active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_counselor_email (email),
    CONSTRAINT ck_counselor_role CHECK (role IN ('ADMIN', 'USER'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='상담사';

-- 2. 내담자 테이블 (client)
CREATE TABLE IF NOT EXISTS client (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    code       VARCHAR(30) NOT NULL,
    name       VARCHAR(50) NOT NULL,
    status     ENUM('안정', '주의', '개선필요') NOT NULL DEFAULT '안정',
    phone      VARCHAR(20) NULL,
    active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_client_code (code),
    KEY ix_client_name (name),
    KEY ix_client_status_active (status, active),
    CONSTRAINT ck_client_status CHECK (status IN ('안정', '주의', '개선필요'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='내담자';

-- 3. 주제/고민유형 정의 테이블 (topic)
CREATE TABLE IF NOT EXISTS topic (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    code       VARCHAR(20) NOT NULL,
    name       VARCHAR(255) NOT NULL,
    type       ENUM('REGISTER', 'AI') NOT NULL,
    descr      TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_topic_code (code),
    KEY ix_topic_name (name),
    KEY ix_topic_type (type),
    CONSTRAINT ck_topic_type CHECK (type IN ('REGISTER', 'AI'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='주제';

-- 4. 상담 예약 테이블 (appt)
CREATE TABLE IF NOT EXISTS appt (
    id           BIGINT NOT NULL AUTO_INCREMENT,
    client_id    BIGINT NOT NULL,
    counselor_id BIGINT NULL,
    at           TIMESTAMP NOT NULL,
    status       ENUM('REQUESTED', 'CONFIRMED', 'CANCELLED', 'COMPLETED') NOT NULL DEFAULT 'REQUESTED',
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_appt_client_time (client_id, at),
    KEY ix_appt_counselor_time (counselor_id, at),
    KEY ix_appt_status (status),
    CONSTRAINT fk_appt_client 
        FOREIGN KEY (client_id) REFERENCES client(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_appt_counselor 
        FOREIGN KEY (counselor_id) REFERENCES counselor(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_appt_status CHECK (status IN ('REQUESTED', 'CONFIRMED', 'CANCELLED', 'COMPLETED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='예약';

-- 5. 상담 세션 테이블 (sess)
CREATE TABLE IF NOT EXISTS sess (
    id            BIGINT NOT NULL AUTO_INCREMENT,
    uuid          VARCHAR(50) NOT NULL,
    counselor_id  BIGINT NOT NULL,
    client_id     BIGINT NOT NULL,
    appt_id       BIGINT NULL,
    channel       ENUM('CHAT', 'VOICE') NOT NULL DEFAULT 'CHAT',
    progress      ENUM('WAITING', 'ACTIVE', 'CLOSED') NOT NULL DEFAULT 'WAITING',
    start_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_at        TIMESTAMP NULL,
    end_reason    ENUM('NORMAL', 'DROPOUT', 'TECH', 'UNKNOWN') NULL COMMENT '세션 종료 사유',
    sat           BOOLEAN NULL COMMENT '1=만족, 0=불만족, NULL=무응답',
    sat_note      VARCHAR(255) NULL COMMENT '만족도 한줄 이유(선택)',
    ok_text       BOOLEAN NOT NULL DEFAULT TRUE,
    ok_voice      BOOLEAN NOT NULL DEFAULT FALSE,
    ok_face       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_sess_uuid (uuid),
    KEY ix_sess_counselor_start (counselor_id, start_at),
    KEY ix_sess_client_start (client_id, start_at),
    KEY ix_sess_channel_progress (channel, progress),
    KEY ix_sess_progress (progress),
    KEY ix_sess_end_reason (end_reason),
    CONSTRAINT fk_sess_counselor 
        FOREIGN KEY (counselor_id) REFERENCES counselor(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_sess_client 
        FOREIGN KEY (client_id) REFERENCES client(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_sess_appt 
        FOREIGN KEY (appt_id) REFERENCES appt(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_sess_channel CHECK (channel IN ('CHAT', 'VOICE')),
    CONSTRAINT ck_sess_progress CHECK (progress IN ('WAITING', 'ACTIVE', 'CLOSED')),
    CONSTRAINT ck_sess_end_reason CHECK (end_reason IS NULL OR end_reason IN ('NORMAL', 'DROPOUT', 'TECH', 'UNKNOWN')),
    CONSTRAINT ck_sess_time CHECK (end_at IS NULL OR end_at >= start_at),
    CONSTRAINT ck_sess_sat CHECK (sat IS NULL OR sat IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='상담 세션';

-- 6. 메시지 테이블 (msg)
CREATE TABLE IF NOT EXISTS msg (
    id          BIGINT NOT NULL AUTO_INCREMENT,
    sess_id     BIGINT NOT NULL,
    speaker     ENUM('COUNSELOR', 'CLIENT', 'SYSTEM') NOT NULL,
    speaker_id  BIGINT NULL,
    text        TEXT NULL,
    emoji       TEXT NULL,
    file_url    TEXT NULL,
    stt_conf    DECIMAL(3,2) NOT NULL DEFAULT 0.00 COMMENT 'STT 신뢰도 0.00~1.00',
    at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_msg_id_sess (id, sess_id) COMMENT 'alert 테이블 복합 FK 지원용',
    KEY ix_msg_sess_time (sess_id, at),
    KEY ix_msg_speaker (speaker, speaker_id),
    CONSTRAINT fk_msg_sess 
        FOREIGN KEY (sess_id) REFERENCES sess(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_msg_speaker CHECK (speaker IN ('COUNSELOR', 'CLIENT', 'SYSTEM')),
    CONSTRAINT ck_msg_stt_conf CHECK (stt_conf BETWEEN 0.00 AND 1.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='채팅/시스템 메시지';

-- 7. STT 음성 구간 테이블 (stt)
CREATE TABLE IF NOT EXISTS stt (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    sess_id    BIGINT NOT NULL,
    speaker    ENUM('COUNSELOR', 'CLIENT') NOT NULL,
    s_ms       INT UNSIGNED NOT NULL COMMENT '시작(ms)',
    e_ms       INT UNSIGNED NOT NULL COMMENT '종료(ms)',
    text       TEXT NOT NULL,
    conf       DECIMAL(3,2) NOT NULL DEFAULT 0.00 COMMENT '신뢰도 0.00~1.00',
    meta       JSON NOT NULL COMMENT '모델명, 버전, 샘플링레이트 등',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_stt_sess_time (sess_id, s_ms, e_ms),
    KEY ix_stt_speaker (speaker),
    KEY ix_stt_conf (conf),
    CONSTRAINT fk_stt_sess 
        FOREIGN KEY (sess_id) REFERENCES sess(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_stt_speaker CHECK (speaker IN ('COUNSELOR', 'CLIENT')),
    CONSTRAINT ck_stt_time CHECK (e_ms > s_ms),
    CONSTRAINT ck_stt_conf CHECK (conf BETWEEN 0.00 AND 1.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='STT 음성 구간';

-- 8. 표정 점수(보조) 테이블 (face)
CREATE TABLE IF NOT EXISTS face (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    sess_id    BIGINT NOT NULL,
    at         TIMESTAMP NOT NULL COMMENT '샘플 시각',
    label      VARCHAR(30) NULL COMMENT '대표 감정 라벨',
    score      DECIMAL(3,2) NULL COMMENT '대표 점수 0.00~1.00',
    dist       JSON NOT NULL COMMENT '감정별 확률 분포',
    meta       JSON NOT NULL COMMENT '모델명, 버전, 샘플링 설정 등',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_face_sess_time (sess_id, at),
    CONSTRAINT fk_face_sess 
        FOREIGN KEY (sess_id) REFERENCES sess(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_face_score CHECK (score IS NULL OR score BETWEEN 0.00 AND 1.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='표정 점수(보조)';

-- 9. 내담자 고민유형 매핑 테이블 (client_topic)
CREATE TABLE IF NOT EXISTS client_topic (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    client_id  BIGINT NOT NULL,
    topic_id   BIGINT NOT NULL,
    prio       TINYINT NOT NULL DEFAULT 1 COMMENT '우선순위',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='내담자 고민유형';

-- 10. 이탈 신호/조치 테이블 (alert)
CREATE TABLE IF NOT EXISTS alert (
    id      BIGINT NOT NULL AUTO_INCREMENT,
    sess_id BIGINT NOT NULL,
    msg_id  BIGINT NOT NULL,
    type    VARCHAR(20) NOT NULL COMMENT 'DELAY/SHORT/NEG_SPIKE/RISK_WORD',
    status  ENUM('DETECTED', 'RESOLVED') NOT NULL DEFAULT 'DETECTED',
    score   DECIMAL(3,2) NULL COMMENT '신호 강도(0.00~1.00)',
    rule    VARCHAR(50) NULL COMMENT '탐지 룰/모델 코드',
    action  TEXT NULL COMMENT '상담사 지원 문구/가이드',
    at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_alert_sess_time (sess_id, at),
    KEY ix_alert_type_status (type, status),
    KEY ix_alert_status (status),
    CONSTRAINT fk_alert_sess 
        FOREIGN KEY (sess_id) REFERENCES sess(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_alert_msg_same_sess 
        FOREIGN KEY (msg_id, sess_id) REFERENCES msg(id, sess_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_alert_status CHECK (status IN ('DETECTED', 'RESOLVED')),
    CONSTRAINT ck_alert_score CHECK (score IS NULL OR score BETWEEN 0.00 AND 1.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='이탈 신호/조치';

-- 11. 세션 품질 분석 테이블 (quality)
CREATE TABLE IF NOT EXISTS quality (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    sess_id    BIGINT NOT NULL,
    flow       DECIMAL(5,2) NOT NULL COMMENT '흐름 점수 0.00~100.00',
    score      DECIMAL(5,2) NOT NULL COMMENT '품질 점수 0.00~100.00',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_quality_sess (sess_id),
    CONSTRAINT fk_quality_sess 
        FOREIGN KEY (sess_id) REFERENCES sess(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_quality_flow CHECK (flow BETWEEN 0.00 AND 100.00),
    CONSTRAINT ck_quality_score CHECK (score BETWEEN 0.00 AND 100.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='품질 분석';

-- 12. 업로드 파일 테이블 (file)
CREATE TABLE IF NOT EXISTS file (
    id           BIGINT NOT NULL AUTO_INCREMENT,
    counselor_id BIGINT NOT NULL,
    client_id    BIGINT NOT NULL,
    sess_id      BIGINT NULL,
    name         TEXT NOT NULL,
    size         INT UNSIGNED NOT NULL DEFAULT 0,
    ext          VARCHAR(30) NOT NULL,
    status       ENUM('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'UPLOADED',
    uploaded_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at   TIMESTAMP NULL COMMENT 'Soft Delete용',
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
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_file_status CHECK (status IN ('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='업로드 파일';

-- 13. 텍스트 정서 분석 테이블 (text_emotion)
CREATE TABLE IF NOT EXISTS text_emotion (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    msg_id     BIGINT NOT NULL,
    label      VARCHAR(30) NOT NULL COMMENT '정서 라벨',
    score      DECIMAL(3,2) NOT NULL DEFAULT 0.00 COMMENT '점수 0.00~1.00',
    meta       JSON NOT NULL COMMENT '모델명, 버전 등',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_text_emotion_msg_time (msg_id, created_at),
    KEY ix_text_emotion_label (label),
    CONSTRAINT fk_text_emotion_msg 
        FOREIGN KEY (msg_id) REFERENCES msg(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_text_emotion_score CHECK (score BETWEEN 0.00 AND 1.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='텍스트 정서 분석';

-- 14. 토픽별 세션 분석 테이블 (sess_analysis)
CREATE TABLE IF NOT EXISTS sess_analysis (
    id         BIGINT NOT NULL AUTO_INCREMENT,
    sess_id    BIGINT NOT NULL,
    topic_id   BIGINT NOT NULL,
    summary    TEXT NOT NULL COMMENT 'AI 요약',
    note       TEXT NOT NULL COMMENT '상담사 의견',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='세션 분석';

-- =====================================================
-- 완료!
-- 본 스크립트는 테이블 명세서(2026.02.14)를 100% 반영한 최종 버전입니다.
-- - 제미나이의 깔끔한 정리 + 명세서의 모든 인덱스 복구
-- - 모든 CHECK 제약조건, FK, UNIQUE 제약 포함
-- - 성능 최적화를 위한 인덱스 전부 포함
-- =====================================================