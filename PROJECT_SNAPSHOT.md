# 📌 MindWay PROJECT SNAPSHOT  
최종 업데이트: 2026-02-20

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
        MySQL (SMHRD External Server: 3307)

외부 AI 모듈:

✔ HyperCLOVA Speech — 내담자 음성 처리  
✔ HyperCLOVA X (HCX-DASH-002) — 상담사 AI 헬퍼  
✔ DeepFace — 표정 기반 감정 신호 분석 (데모 모드 중심)

---

## ✅ 기술 스택

### 🔹 Backend

🔹 Backend & DB
- Framework: FastAPI (Asynchronous API)

- ORM: SQLAlchemy (MySQL Connector: PyMySQL)

- Database: MySQL (External Server: 3307 Port) - counseling_db (명칭: mindway)

- Environment: .env 기반 보안 관리
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

### ✔ HyperCLOVA Speech (통합 핵심 엔진)

역할:

- 멀티모달 통합 처리: 내담자가 선택한 CHAT(키보드) 또는 VOICE(음성) 모드에 관계없이 모든 상담 발화를 단일 분석 파이프라인으로 통합함 
- 실시간 STT 및 메타데이터 추출: 음성 데이터의 실시간 텍스트 변환과 동시에, 발화의 길이, 속도, 톤의 변화를 즉시 데이터화함.
- 비언어적 지표의 정량화: 텍스트 너머의 침묵 시간(Pause), 응답 지연(Latency) 등을 수치로 변환하여 상담 흐름의 단절 가능성을 포착함.

목적: 
- 패턴 기반 분석 근거 마련: 발화 빈도 및 반복되는 패턴을 분석하여, 경험적 직관이 아닌 객관적 수치에 기반한 Action 0-5 단계 판정 근거를 생성함.
- Risk Score 엔진의 핵심 피드(Feed): 추출된 수치들을 MySQL(3307 포트)의 msg 및 alert 테이블과 연동하여 실시간 위험도 점수를 산출하는 기초 인풋으로 활용함.
- 상담 품질 가시화: 누적된 수치 데이터를 바탕으로 사후 리포트에서 상담 품질의 편차를 정량적으로 비교 분석할 수 있게 함.

---

### ✔ HyperCLOVA X (HCX-DASH-002) — 상담사 AI 헬퍼

역할:

- 상담 맥락 이해  
- 공감 중심 대응 전략 생성  
- 다음 발화 가이드 제공  
- 상담 흐름 안정화 지원  

특징:

✔ 휘발성: 추천 내용은 DB에 저장되지 않으며 실시간 상담 보조용으로만 활용
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

- 외부 AI(HCX) 실패 또는 API 지연 대비
- 최소한의 안정적인 공감/대응 응답 보장
- 시스템 복원력 및 서비스 연속성 확보

운영 원칙:

✔ 제거 금지 (시스템 안정성의 최후 보루)

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

모든 분석 및 위험도(Risk Score) 계산은 세션 단위로 수행된다

---

## ✅ FastAPI 주요 엔드포인트

### 🔹 기본 시스템 API

GET /health/db  
→ SMHRD 외부 서버(3307) 연결 상태 확인

GET /sessions  
→ 상담 세션 목록 조회

POST /messages  
→ 메시지 저장 + Speech 엔진 기반 수치화 + 위험 신호 탐지

---

### 🔹 세션 기반 API

GET /sessions/{sess_id}/dashboard  
→ 세션 메타 정보 + 통합 Risk Score

GET /sessions/{sess_id}/messages  
→ 대화 로그 조회

GET /sessions/{sess_id}/alerts  
→ 탐지된 위험 신호 리스트

---

### 🔹 통계 / 사후 분석 API

GET /stats/topic-dropout (주제별 이탈 분석)

- 내용: "가족 관계", "진로 고민" 등 특정 상담 주제(Topic)에 따른 이탈률 편차를 분석합니다.
- 목적: 상담사가 특정 주제를 다룰 때의 위험 구간을 식별하고 대응 가이드라인을 제공합니다.


GET /stats/client-grade-dropout (내담자 그룹별 분석)

- 내용: 내담자의 상태 등급(client.status)에 따른 이탈 분포를 파악합니다.
- 목적: 고위험군 내담자에게 최적화된 상담 배정 및 관리 전략을 수립합니다.

GET /stats/missed-alerts (탐지 누락 분석)

- 내용: 이탈(DROPOUT)은 발생했으나 alert 기록이 없는 예외 케이스를 추출합니다.
- 목적: Rule-based 엔진의 키워드 사전을 고도화하고 시스템의 탐지 정확도를 높이는 피드백 데이터로 활용합니다.

GET /stats/quality-trend (품질 추이 분석 - 신규)

- 내용: 일별/주별 상담 만족도(sat)와 Risk Score의 상관관계 및 변화 추이를 추적합니다.
- 목적: 상담 시스템 운영의 안정화 단계를 시각화하고 서비스 품질의 상향 평준화를 도모합니다.

GET /stats/channel-dropout (채널별 성과 분석)

- 내용: CHAT(텍스트)과 VOICE(음성) 채널 간의 이탈률 및 상담 효율성을 비교합니다.
- 목적: 각 채널에 특화된 HyperCLOVA Speech 엔진 최적화 및 상담 인터페이스 개선 근거를 마련합니다.

GET /stats/monthly-growth (운영 성과 리포트)

- 내용: 월별 총 상담 건수, 이탈 방지 성공률 등 주요 지표의 성장세를 집계합니다.
- 목적: 서비스 운영 성과를 정량적으로 증명하고 향후 자원 배정의 판단 근거로 활용합니다.

GET /appointments (예약 현황 연동 - 신규)

- 내용: 오늘 예정된 상담 리스트와 내담자 정보를 가져옵니다.
- 목적: 상담사가 대시보드 하나만 켜두고도 오늘 업무 스케줄과 과거 분석 이력을 한눈에 보게 하여 업무 연속성을 높입니다.

---

### 🔹 AI 헬퍼 API (실시간 대화 가이드)
상담 중 내담자의 발화 맥락을 파악하여 상담사가 다음에 사용할 수 있는 최적의 대응 문구를 추천합니다. 이 데이터는 상담 보조 목적으로만 사용되며 DB에 별도로 저장되지 않는 휘발성 가이드입니다.

POST /helper/suggestion

입력(Request Body):

- sess_id: 현재 분석 중인 상담 세션 ID 
- counselor_id: 도움을 받는 상담사 식별자
- last_client_text: 내담자의 마지막 발화 내용 (맥락 파악용)
- last_counselor_text: 상담사의 마지막 발화 내용 (흐름 유지용)
- context (optional): 이전 대화 요약 또는 상담 주제 등 추가 참고 정보

출력(Response Body):

- mode: RULE (키워드 기반 기본 응답) | HCX (HyperCLOVA X 생성형 응답)
- suggestion: 상담사에게 제안하는 실시간 추천 발화 스크립트
- finishReason: 응답 생성 종료 사유 (예: stop, length 등)

---

## ✅ 위험 신호 탐지 로직 (통합 분석 엔진 연동)

현재 방식:

✅ 위험 신호 탐지 로직 (통합 분석 엔진 중심)
현재 방식:

✔ 언어적 핵심 탐지: 사전 정의된 NEG_KEYWORD 매칭을 통한 직접적인 부정 의사 식별

✔ 정량적 패턴 분석: HyperCLOVA Speech 엔진이 산출한 발화 패턴(응답 지연 시간, 발화 빈도 변동) 수치 결합

✔ 비언어적 보조 지표: msg.emoji 및 DeepFace 수치를 통한 분석 신뢰도 보강 (단독 점수 산정 지양)

예시 키워드:

- 그만  
- 힘들  
- 포기  
- 싫어  
- 못하겠  
- 의미없  

탐지 시:

✔ alert 기록 (Table: alert) : alert 테이블에 탐지 규칙명과 엔진 산출 기반 위험 점수(score) 저장
- 명세서 매칭: alert 테이블의 rule 컬럼에 탐지 규칙명이, score 컬럼에 HyperCLOVA Speech 엔진이 산출한 정량적 점수가 정확히 저장됩니다.
- 기술적 실체: 단순히 텍스트를 저장하는 것이 아니라, 엔진의 분석 결과값(score)을 DB화하여 사후 분석(GET /stats/...)의 기초 데이터로 활용하는 구조입니다.

✔ Risk Score 반영 (Logic: sess 기반) : 해당 세션의 실시간 누적 위험 지수 업데이트
- 명세서 매칭: 특정 sess_id를 외래키(FK)로 가지는 모든 alert 레코드의 score 평균값을 계산하는 구조와 일치합니다.
- 기술적 실체: sess 1 : N alert 관계를 통해, 세션이 진행될수록 실시간으로 업데이트되는 누적형 지표임을 데이터 모델링으로 이미 증명하고 있습니다.

✔ UI 위험도 변화 (Frontend: Streamlit): 상담사 대시보드의 게이지 및 타임라인에 분석 결과 즉시 시각화
- 명세서 매칭: 02_counselor_dashboard.py와 04_session_analysis.py에서 GET /sessions/{sess_id}/dashboard API를 호출하여 이 수치를 즉시 시각화합니다.
- 기술적 실체: alert.at(타임스탬프) 데이터를 사용하여 대시보드 타임라인 그래프에 위험 구간을 마킹하는 로직까지 완벽하게 설계되어 있습니다.
---

## ✅ Risk Score 정의 및 다각적 분석

기본 공식 : Risk Score = alert.score 평균값
세션 내 발생한 모든 위험 신호 점수의 평균을 산출합니다.

✔ 시간적 추이 분석 (alert.at) 
- Risk Score 시계열 변화: 상담 초반 대비 후반부의 점수 상승 곡선을 분석하여 '이탈 직전 임계점'을 파악합니다.

✔ 채널별 비교 분석 (sess.channel)
- 채널별 위험 패턴: CHAT과 VOICE 중 어떤 채널에서 평균 Risk Score가 더 높게 나타나는지 비교하여 채널별 최적화 전략을 수립합니다.

✔ 상태별 가중치 (client.status)
- 내담자 등급별 보정: 고위험군 내담자의 경우, 동일한 alert 발생 시에도 Risk Score에 가중치를 부여하여 더 민감하게 탐지합니다.

✔ 품질 상관도 분석 (sess.sat)
- 이탈 예측 타당성 검증: 실제 만족도(sat)가 0(불만족)인 세션의 평균 Risk Score가 실제로 높았는지 대조하여 탐지 엔진의 정확도를 검증합니다.

포인트:

✔ 데이터 기반의 설득력: 단순히 "위험해요"라고 말하는 게 아니라, "이 내담자는 평소보다 응답 지연(at)이 길어지고 부정적 단어(NEG_KEYWORD)가 반복되어 Risk Score가 0.8까지 올랐습니다"라고 명세서 근거를 들어 설명할 수 있습니다.

✔ 전략적 시각화: 이 다각적 분석 결과들을 대시보드의 '사후 분석 API'(GET /stats/...)와 연결하면, 우리 시스템의 비즈니스 가치를 확실히 보여줄 수 있습니다.

✔ 명세서의 컬럼들을 Risk Score와 엮어내면 정말 완성도 높은 데이터 분석 프로젝트가 될 것으로 기대합니다.
예를 들어(이안 의견) :
1. 언어적 위험도 산출 (msg.text & alert.rule)
- 데이터 연동: msg.text 내 NEG_KEYWORD 매칭 결과를 alert 테이블에 기록합니다.

- Risk Score 반영:
• "그만", "힘들어" 등 직접 이탈어 발생 시 alert.score 상향 (예: 0.8)
• 패턴 분석: 동일 세션 내 부정어 반복 빈도가 높을수록 실시간 평균 Risk Score가 가파르게 상승하도록 설계합니다.

2. 비언어적 보조 분석 (msg.emoji & msg.file_url)
- 데이터 연동: 내담자가 선택한 이모지(emoji)와 공유된 파일(file_url)의 성격을 분석합니다.

- Risk Score 보정:
• 이모지 불일치: 텍스트는 긍정적이나 이모지가 😭, 😠일 경우, Risk Score에 '잠재적 위험 가중치'를 부여하여 상담사에게 경고를 보냅니다.
• 참조 자료 유무: file_url을 통해 고위험군 진단지 등이 공유된 세션은 기본 Risk Score 시작점을 높게 설정합니다.

3. 흐름 및 채널 분석 (msg.at & sess.channel)
- 데이터 연동: 메시지 발생 시점(at)과 상담 모드(channel: CHAT/VOICE)를 결합합니다.

- Risk Score 고도화:
• 응답 지연(Latency): HyperCLOVA Speech 엔진이 분석한 평균 응답 간격보다 지연이 길어질수록 '소통 단절'로 판단하여 점수를 점진적으로 올립니다.
• 채널 특성: VOICE 상담 시의 음성 떨림이나 침묵 구간 수치를 Risk Score에 실시간으로 통합 피드합니다.

4. 이력 및 성과 연동 (client.status & sess.sat)
- 데이터 연동: 내담자의 등급(status)과 이전 세션의 만족도(sat)를 참조합니다.

- Risk Score 예측력:
• 과거 불만족 이력: 이전에 만족도(sat)가 0이었던 내담자는 동일한 위험 신호에도 더 높은 Risk Score를 산출하여 밀착 관리를 유도합니다.
• 등급별 임계치: status가 높은 고위험군은 Risk Score가 일정 수준 도달 시 즉시 Rule-based Safety Engine이 개입하도록 설정합니다.
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

## ✅ 실행 절차 (ThinkBIG_main 루트 기준)

### 1️⃣ Database 실행

SMHRD 외부 서버를 활용하므로 별도의 로컬 Docker 실행 없이 .env 파일의 접속 정보(Port 3307)만 확인합니다.

---

### 2️⃣ Backend 실행

# 루트 폴더에서 패키지 경로를 포함하여 실행
uvicorn main:app --reload

Swagger:

http://127.0.0.1:8000/docs

---

### 3️⃣ Frontend 실행

streamlit run dashboard.py

---


## ⚠ 향후 작업 예정

### 🔸 음성 및 통합 엔진 고도화

- HyperCLOVA Speech 실시간 연결 최적화 및 발화 지연(Latency) 수치 정밀화
- CHAT/VOICE 통합 시나리오에 따른 데이터 구조 고도화  

---

### 🔸 표정 분석

- DeepFace 카메라 연동을 통한 비언어적 감정 수치 보조 지표 추가 (데모 중심)
- 감정 점수 저장 구조  

---

### 🔸 AI 헬퍼 고도화

- 대화 톤앤매너 가이드 (Style Transfer):

전략: 상담사가 내담자에게 부드럽고 공감적인 어조로 다가갈 수 있도록 추천 문구의 정중함과 공감 수준을 조정합니다.

목적: 상담사가 상황에 적합한 어휘를 빠르게 선택할 수 있도록 언어적 선택지를 넓혀줍니다.

- 상담 흐름 지원 (Context-Helper):

전략: Speech 엔진이 분석한 이전 대화의 주요 키워드를 바탕으로, 대화가 끊기지 않도록 '다음 질문'이나 '맞장구' 문구를 제안합니다.

목적: 상담사의 인지적 부하를 줄여 내담자와의 정서적 교감에 더 집중할 수 있게 합니다.

- 시스템 안전 가이드라인 (Guardrails):

전략: 프롬프트 설정을 통해 AI가 어떠한 형태의 의학적 진단, 심리적 판정, 단정적 조언도 하지 않도록 철저히 제한합니다.

운영 원칙: 모든 추천 문구는 상담사의 검토 후에만 사용될 수 있는 '초안'임을 명시합니다.

- 위험 징후 대응 보조:

전략: Risk Score가 감지된 세션에서 상담사가 당황하지 않고 대화를 이어갈 수 있도록, 매뉴얼에 기반한 표준 대응 예시를 우선 노출합니다.  


---

## ✅ 프로젝트 설계 철학

MindWay는 기술이 상담사를 대체하는 것이 아니라, 기술이 상담사를 보호하고 보조하는 시스템을 지향합니다.

✔ 상담사 주권 존중: AI는 상담사를 대신해 판단하거나 진단하지 않으며, 오직 상담사가 더 나은 판단을 내릴 수 있도록 정량적 근거만을 제공합니다.

✔ 비진단적 분석: 본 시스템은 심리적 판정을 내리는 '자동 진단 시스템'이 아니며, 발화 패턴과 키워드를 기반으로 한 데이터 분석 플랫폼입니다.

✔ 신호 기반 보조: 모든 추천과 수치는 상담사가 내담자의 상태를 빠르게 인지하도록 돕는 의사결정 보조 신호로만 기능합니다.

---

## ✅ 유지보수 시 주의사항

1. 테이블 구조 변경 시 API 영향 확인  
2. Streamlit ↔ FastAPI 경로 동기화 필수  
3. HCX 모델 ID 변경 시 즉시 반영  
4. RULE fallback 제거 금지  

---

## ✅ 최종 요약

MindWay는 상담 전 과정을 정량화하여 이탈 신호를 추적하고, 대시보드 중심의 사후 분석 기능을 제공하는 데이터 기반 상담 품질 관리 시스템입니다.

- 대시보드 중심 운영: 모든 상담 데이터는 MySQL(3307 포트)에 실시간 적재되며, 상담사는 대시보드를 통해 세션별 Risk Score와 이탈 징후를 한눈에 관제합니다.

- 데이터 기반 사후 분석 및 품질 개선: 상담 종료 후, HyperCLOVA Speech 엔진이 수치화한 발화 패턴과 통계 API를 활용하여 이탈 원인을 정밀 분석하고 상담 품질 향상을 위한 객관적 근거를 제시합니다. DeepFace 감정 분석 데이터는 분석의 객관성을 높이기 위해 필요 시 보조적으로 참고하여 인사이트를 보강합니다.

- 선택적 보조 도구: 실시간 AI 헬퍼는 대화의 흐름을 지원하기 위한 휘발성 기능으로 존재하며, 시스템의 주 목적은 Speech 데이터 중심의 기록과 그 분석적 가치를 증명하는 데 있습니다.

---



📊 Dashboard Analysis Specification (Table-Driven)
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
분석에 사용되는 핵심 테이블 (SMHRD 외부 서버 - 3307 포트):

sess → 상담 세션 단위 정보 (channel, sat 등 포함)

msg → 대화 흐름 / 발화 로그 (emoji, at 등 포함)

alert → 위험 신호 / 탐지 이벤트 (rule, score 등 포함)

관계 구조:

sess 1:N msg

sess 1:N alert

✅ 3. KPI 계산 정의 (상단 상황판)
✔ 총 세션 수

기준 테이블: sess

정의: 총 상담 세션 개수 (기간 필터 적용 가능)

SQL 개념: COUNT(sess.id)

✔ 이탈 세션 수

기준 테이블: sess

정의: end_reason = 'DROPOUT'인 세션 수

SQL 개념: COUNT(CASE WHEN end_reason='DROPOUT' THEN 1 END)

✔ 이탈률 (Dropout Rate)

정의: dropout_sessions / total_sessions × 100

특징: 운영 성과 지표 및 대시보드 최상위 핵심 수치

✔ 평균 Risk Score

기준 테이블: alert

정의: 세션별 alert.score 평균값의 전체 평균

개념: AVG(alert.score)

✅ 4. Risk Score 모델 정의
Risk Score는 AI 추론값이 아니라 탐지된 신호 기반 운영 지표로 정의된다.

정의: Risk Score(sess) = AVG(alert.score WHERE alert.sess_id = sess.id)

점수 범위: 0.00 ~ 1.00

특징: 설명 가능성, DB 기반 재현성, 심사 안정성 확보

✅ 5. 이탈 직전 신호(Window-Based)
이탈 분석은 전체 세션이 아니라 종료 직전 구간(Window) 중심으로 수행한다.

✔ 직전 구간 정의

운영 정의: Last N Turns 방식 (MVP 기준 마지막 5~10개 msg 레코드)

선정 이유: 시간 로그 오차 최소화 및 구현 안정성/재현성 확보

✅ 6. Signal Feature 그룹
이탈 직전 신호는 다음 3계층으로 분류한다.

🧩 A. 언어 신호 (msg.text 기반)

테이블: msg

탐지 방식: Rule-based keyword detection (NEG_KEYWORD)

예시: 그만 / 힘들 / 포기 / 의미없 / 못하겠 / 안 할래 등

🧩 B. 대화 흐름 신호 (msg.at 기반)

분석 대상: 발화 시간 간격(at), 턴 비율, 발화 길이 변화

대표 지표: 응답 지연 증가, 내담자 발화 길이 급감, CLIENT 턴 비중 감소

활용: HyperCLOVA Speech 엔진이 산출한 정량적 패턴 분석

🧩 C. 행동 / 상태 신호 (sess & msg 보조)

분석 대상: channel(CHAT/VOICE), progress, end_reason, sat(만족도 1/0)

보조 지표: msg.emoji (비언어적 단서), DeepFace (필요 시 표정 데이터 참고)

✅ 7. 대시보드 핵심 시각화 구성
✔ ① 등급 / 유형별 이탈 분포: sess + client.status 기준 그룹별 문제 식별

✔ ② 채널별 이탈 비교: sess.channel 기준 CHAT vs VOICE 성과 비교

✔ ③ 시간대별 이탈률: sess.start_at 기준 운영 스케줄링 개선 근거 제공

✔ ④ 알림 없는 이탈 (Missed Alerts): end_reason='DROPOUT'이나 alert.count=0인 사례 추출 (로직 고도화용)

✔ ⑤ 월별 운영 추이: sess.start_at 기준 서비스 안정성 및 성과 시각화

✅ 8. 이탈 직전 신호 시각화 구조
✔ 직전 구간 타임라인: msg.at + msg.speaker 기반 턴 흐름 및 응답 공백 시각화

✔ 신호 탐지 근거 패널: alert.rule, alert.score, msg.text 매칭 정보 표시 (블랙박스 회피)

✔ 위험도 변화 흐름: alert.score 시간 순 정렬을 통한 누적 패턴 및 품질 저하 구간 설명

✅ 9. 설계 철학 (Dashboard 관점)
MindWay 대시보드는 운영 해석 시스템으로 정의된다.

모델 의존 최소화 및 규칙 기반 설명 가능성 확보

상담사 의사결정 보조 목적 (자동 판단 / 진단 기능 배제)

✅ 10. 핵심 결론
MindWay의 최종 산출물은 이탈 직전 신호 구조화와 Risk Score 기반 분석 인터페이스이다.

AI 모듈(Speech / HCX / DeepFace)은 분석 시스템을 강화하고 정량적 데이터를 공급하는 입력/보조 계층으로 정의된다.

# 2026.02.18 (업데이트 사항)
✔ API 엔드포인트 목록 최신화

추가: GET /appointments (오늘의 예약 리스트 - 업무 연속성 확보)

추가: GET /stats/quality-trend (세션 품질 및 만족도(sat) 추이 분석)