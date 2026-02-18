# 📌 MindWay PROJECT SNAPSHOT  
최종 업데이트: 2026-02-17

---

## ✅ 프로젝트 개요

**프로젝트명**  
MindWay – 상담 이탈 신호 탐지 & 상담 품질 분석 시스템

**핵심 목적**

본 프로젝트는 상담 과정에서 발생하는 텍스트 / 음성 / 비언어 신호를 기반으로:

✔ 상담 이탈(Dropout) 위험 조기 탐지  
✔ 상담사 의사결정 보조 (AI 헬퍼)  
✔ 사후 분석 기반 상담 품질 개선 지원  

을 목표로 설계된 데이터 기반 상담 지원 시스템이다.

MindWay는 상담사를 대체하는 시스템이 아니라,  
상담사의 판단을 보조하는 **분석 중심 의사결정 지원 도구**를 지향한다.

MindWay는 상담 과정 데이터를 기반으로
이탈 직전 신호를 구조적으로 분석하고,
상담 품질 향상을 위한 의사결정 정보를 제공하는
대시보드 중심 분석 시스템이다.

---

## ✅ 현재 시스템 아키텍처

[ Client / Counselor UI (Streamlit) ]  
                │  
                ▼  
        FastAPI Backend (main.py)  
                │  
                ▼  
            MySQL (Docker)

외부 AI 모듈:

✔ HyperCLOVA Speech — 내담자 음성 처리  
✔ HyperCLOVA X (HCX-DASH-002) — 상담사 AI 헬퍼  
✔ DeepFace — 표정 기반 감정 신호 분석 (데모 모드 중심)

---

## ✅ 기술 스택

### 🔹 Backend

- FastAPI  
- SQLAlchemy  
- PyMySQL  
- Uvicorn  

---

### 🔹 Frontend (Prototype UI)

- Streamlit  
- Plotly  

---

### 🔹 Database

- MySQL (Docker Compose)  

---

### 🔹 AI / 분석 모듈

- HyperCLOVA Speech (Voice Interface)  
- HyperCLOVA X (HCX-DASH-002)  
- DeepFace (Emotion Demo Engine)  
- Rule-based Safety Engine (Fallback 안정성 계층)

---

## ✅ AI 모듈 역할 정의

### ✔ HyperCLOVA Speech (내담자 음성 처리)

역할:

- 음성 상담 지원  
- Speech-to-Text(STT)  
- Text-to-Speech(TTS) 확장 가능  

목적:

음성 입력을 텍스트 분석 파이프라인으로 변환하여  
위험 탐지 / 분석 / 헬퍼 로직과 통합

Voice → Speech → Text

---

### ✔ HyperCLOVA X (HCX-DASH-002) — 상담사 AI 헬퍼

역할:

- 상담 맥락 이해  
- 공감 중심 대응 전략 생성  
- 다음 발화 가이드 제공  
- 상담 흐름 안정화 지원  

특징:

✔ 생성형 AI 기반  
✔ 상담사 의사결정 보조 전용  
✔ 자동 진단 / 판단 기능 없음  

---

### ✔ DeepFace (표정 분석 모듈)

역할:

- 표정 기반 감정 신호 추정  
- 감정 라벨 + 점수 제공  
- 상담 보조 지표 시각화  

운영 원칙:

✔ 내담자 동의 기반  
✔ 데모 모드 중심  
✔ 최종 판단 데이터로 사용하지 않음  

---

### ✔ Rule-based Safety Engine (Fallback)

역할:

- 외부 AI 실패 대비  
- 최소 안정 응답 보장  
- 시스템 복원력 확보  

운영 원칙:

✔ 제거 금지  

---

## ✅ DB 핵심 구조

주요 테이블:

- counselor  
- client  
- sess (상담 세션)  
- msg (대화 로그)  
- alert (위험 신호)

관계 구조:

sess 1:N msg  
sess 1:N alert  

모든 분석 및 위험도 계산은 세션 단위로 동작한다.

---

## ✅ FastAPI 주요 엔드포인트

### 🔹 기본 시스템 API

GET /health/db  
→ DB 연결 상태 확인

GET /sessions  
→ 상담 세션 목록 조회

POST /messages  
→ 메시지 저장 + 위험 신호 탐지

---

### 🔹 세션 기반 API

GET /sessions/{sess_id}/dashboard  
→ 세션 정보 + Risk Score

GET /sessions/{sess_id}/messages  
→ 대화 로그 조회

GET /sessions/{sess_id}/alerts  
→ 위험 신호 조회

---

### 🔹 통계 / 사후 분석 API

GET /stats/topic-dropout  
GET /stats/client-grade-dropout  
GET /stats/missed-alerts  
GET /stats/time-dropout  
GET /stats/channel-dropout  
GET /stats/monthly-growth  

---

### 🔹 AI 헬퍼 API

POST /helper/suggestion

입력:

- sess_id  
- counselor_id  
- last_client_text  
- last_counselor_text  
- context (optional)

출력:

- mode: RULE | HCX  
- suggestion: string  
- finishReason  

---

## ✅ 위험 신호 탐지 로직

현재 방식:

✔ Rule-based keyword detection  
✔ NEG_KEYWORD 중심 탐지  

예시 키워드:

- 그만  
- 힘들  
- 포기  
- 싫어  
- 못하겠  
- 의미없  

탐지 시:

✔ alert 기록  
✔ Risk Score 반영  
✔ UI 위험도 변화  

---

## ✅ Risk Score 정의

Risk Score = alert.score 평균값

특징:

✔ 세션 단위  
✔ 실시간 누적형  
✔ 상담사 화면 시각화 지표  

---

## ✅ 상담사 AI 헬퍼 전략

동작 모드:

1. HCX 모드 (Primary)  
   → HyperCLOVA X 응답 사용

2. RULE 모드 (Fallback)  
   → HCX 실패 시 자동 전환

---

## ✅ 환경 변수 (.env)

필수 변수:

HCX_API_KEY  
HCX_MODEL_ID  
HCX_HOST  

DB_HOST  
DB_PORT  
DB_NAME  
DB_USER  
DB_PASSWORD  

주의:

✔ .env Git 업로드 금지  
✔ .gitignore 포함 필수  

---

## ✅ 실행 절차 (로컬 개발 기준)

### 1️⃣ Database 실행

docker-compose up -d

---

### 2️⃣ Backend 실행

uvicorn main:app --reload

Swagger:

http://127.0.0.1:8000/docs

---

### 3️⃣ Frontend 실행

streamlit run dashboard.py

---

## ✅ 현재 안정 상태

✔ 세션 조회 정상  
✔ 메시지 저장 정상  
✔ alert 기록 정상  
✔ Risk Score 계산 정상  
✔ RULE 엔진 정상  
✔ HyperCLOVA X 연동 정상  

---

## ⚠ 향후 작업 예정

### 🔸 음성 모듈

- HyperCLOVA Speech 실시간 연결  
- STT 파이프라인 안정화  

---

### 🔸 표정 분석

- DeepFace 카메라 연동  
- 감정 점수 저장 구조  

---

### 🔸 AI 헬퍼 고도화

- 프롬프트 전략 개선  
- 위험 단계별 대응 분기  
- 상담 유형별 전략 모델링  

---

## ✅ 프로젝트 설계 철학

MindWay는:

✔ 상담사를 대체하지 않는다  
✔ 자동 판단 시스템이 아니다  
✔ 신호 기반 의사결정 보조 시스템이다  

---

## ✅ 유지보수 시 주의사항

1. 테이블 구조 변경 시 API 영향 확인  
2. Streamlit ↔ FastAPI 경로 동기화 필수  
3. HCX 모델 ID 변경 시 즉시 반영  
4. RULE fallback 제거 금지  

---

## ✅ 최종 요약

MindWay는 상담 데이터를 기반으로  
상담 이탈 위험 신호를 탐지하고,  
AI 헬퍼를 통해 상담사의 대응 품질을 보조하는  
데이터 기반 상담 지원 분석 시스템이다.

---
## 📊 Dashboard Analysis Specification (Table-Driven)

본 섹션은 MindWay 대시보드에 표시되는 모든 분석 결과를
DB 테이블 구조(sessions / msg / alert)를 기준으로 정의한다.

대시보드의 모든 수치 및 시각화는 모델 결과가 아닌 저장 데이터 기반으로 계산되며,
해석 가능성과 운영 안정성을 최우선 설계 원칙으로 한다.

✅ 1. 대시보드 핵심 목적

MindWay 대시보드는 단순 통계 화면이 아니라
상담 운영 의사결정을 지원하는 분석 인터페이스이다.

대시보드가 답해야 하는 핵심 질문:

현재 상담 운영 상태는 안정적인가?

이탈 위험은 어디에서 발생하고 있는가?

어떤 신호가 이탈 직전에 나타나는가?

개선 우선순위는 무엇인가?

✅ 2. 데이터 기준 테이블

분석에 사용되는 핵심 테이블:

sess → 상담 세션 단위 정보

msg → 대화 흐름 / 발화 로그

alert → 위험 신호 / 탐지 이벤트

관계 구조:

sess 1:N msg
sess 1:N alert

✅ 3. KPI 계산 정의 (상단 상황판)
✔ 총 세션 수

기준 테이블: sess

정의:

총 상담 세션 개수 (기간 필터 적용 가능)

SQL 개념:

COUNT(sess.id)

✔ 이탈 세션 수

기준 테이블: sess

정의:

end_reason = 'DROPOUT'

SQL 개념:

COUNT(CASE WHEN end_reason='DROPOUT' THEN 1 END)

✔ 이탈률 (Dropout Rate)

정의:

dropout_sessions / total_sessions × 100

특징:

✔ 운영 성과 지표
✔ 대시보드 최상위 핵심 수치

✔ 평균 Risk Score

기준 테이블: alert

정의:

세션별 alert.score 평균값의 평균 또는 선택 세션 기준 평균

개념:

AVG(alert.score)

✅ 4. Risk Score 모델 정의

Risk Score는 AI 추론값이 아니라
탐지된 신호 기반 운영 지표로 정의된다.

정의:

Risk Score(sess) = AVG(alert.score WHERE alert.sess_id = sess.id)
alert.score의 범위가 0.00 ~ 1.00

특징:

✔ 설명 가능
✔ DB 기반 재현 가능
✔ 모델 교체와 무관
✔ 심사 안정성 확보

✅ 5. 이탈 직전 신호(Window-Based)

이탈 분석은 전체 세션이 아니라
종료 직전 구간(Window) 중심으로 수행한다.

✔ 직전 구간 정의

운영 정의:

Last N Turns 방식 (MVP 기준)

예: 마지막 5~10개 msg 레코드

선정 이유:

✔ 시간 로그 오차 영향 최소화
✔ 구현 안정성 높음
✔ 재현 가능성 확보

✅ 6. Signal Feature 그룹

이탈 직전 신호는 다음 3계층으로 분류한다.

🧩 A. 언어 신호 (msg.text 기반)

테이블:

msg

분석 대상:

msg.text

탐지 방식:

Rule-based keyword detection

예시 신호:

부정 표현: 그만 / 힘들 / 포기 / 의미없 / 못하겠

단절 표현: 안 할래 / 끝내고 싶다

위기 표현: 죽고 싶다 (고위험 별도 처리)

대시보드 활용:

✔ 신호 빈도
✔ 직전 구간 집중도

🧩 B. 대화 흐름 신호 (msg.at 기반)

테이블:

msg

분석 대상:

발화 시간 간격

턴 비율 변화

발화 길이 변화

대표 지표:

✔ 응답 지연 증가
✔ 내담자 발화 길이 급감
✔ 상담사 질문 대비 응답 감소
✔ CLIENT 턴 비중 감소

대시보드 활용:

✔ 패턴 기반 이탈 설명
✔ 품질 저하 구간 식별

🧩 C. 행동 / 상태 신호 (sess 기반)

테이블:

sess

분석 대상:

channel

progress

end_reason

sat (만족도(sat)는 1(만족) 또는 0(불만족)으로 기록)

대표 지표:

✔ 채널별 이탈률
✔ 특정 종료 유형 집중도

✅ 7. 대시보드 핵심 시각화 구성
✔ ① 등급 / 유형별 이탈 분포

기준:

sess + client.status

목적:

✔ 어떤 그룹에서 문제가 발생하는지 즉시 인지

✔ ② 채널별 이탈 비교

기준:

sess.channel

목적:

✔ Speech / Text 채널 운영 성과 비교
✔ 시스템 개선 포인트 도출

✔ ③ 시간대별 이탈률

기준:

sess.start_at

목적:

✔ 상담 운영 스케줄링 개선 근거 제공

✔ ④ 알림 없는 이탈 (Missed Alerts)

기준:

sess LEFT JOIN alert

조건:

end_reason='DROPOUT' AND alert.count=0

목적:

✔ 탐지 로직 고도화 필요성 증명
✔ 시스템 가치 강조

✔ ⑤ 월별 운영 추이

기준:

sess.start_at

목적:

✔ 서비스 안정성 / 성과 시각화
✔ 심사 대응 차트

✅ 8. 이탈 직전 신호 시각화 구조

상세 대시보드 / 세션 분석 화면에서 제공.

✔ 직전 구간 타임라인

데이터:

msg.at + msg.speaker

표현 방식:

✔ 턴 흐름 시각화
✔ 응답 공백 구간 강조

✔ 신호 탐지 근거 패널

데이터:

alert.rule / alert.score / msg.text

표현 방식:

✔ 어떤 규칙이 발동되었는지 표시
✔ 블랙박스 모델 구조 회피

✔ 위험도 변화 흐름

데이터:

alert.score 시간 순 정렬

목적:

✔ 위험 신호 누적 패턴 확인
✔ 상담 품질 저하 구간 설명

✅ 9. 설계 철학 (Dashboard 관점)

MindWay 대시보드는 예측 시스템이 아니라
운영 해석 시스템으로 정의된다.

✔ 모델 의존 최소화
✔ 규칙 기반 설명 가능성 확보
✔ 상담사 의사결정 보조 목적
✔ 자동 판단 / 진단 기능 배제

✅ 10. 핵심 결론

MindWay의 최종 산출물은 AI 응답이 아니라:

✔ 이탈 직전 신호 구조화
✔ Risk Score 기반 위험도 지표
✔ 상담 품질 개선 의사결정 정보
✔ 대시보드 중심 분석 인터페이스

이다.

AI 모듈(Speech / HCX / DeepFace)은
분석 시스템을 강화하는 입력/보조 계층으로 정의된다.

# 2026.02.18

✔ API 엔드포인트 목록 최신화
추가: GET /appointments (오늘의 예약 리스트), GET /stats/quality-trend (세션 품질 추이)