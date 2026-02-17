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