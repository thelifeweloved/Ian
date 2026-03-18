# MindWay (비대면 상담 분석 보조 AI 리포트 서비스)

## 프로젝트 소개
비대면 상담 데이터를 기반으로 상담 흐름과 감정 변화를 분석하여  
상담사가 상담 과정을 구조적으로 이해하고, 상담 품질을 개선할 수 있도록 지원하는 시스템입니다.

---

## 문제 정의 (현실 기반)

비대면 상담 환경에서는 다음과 같은 구조적 문제가 존재합니다:

- 상담 중도 이탈 문제 (초기 상담 이후 이탈 증가)
- 상담 흐름을 실시간으로 파악하기 어려운 모니터링 한계
- 상담 데이터가 단순 저장에 머물러 분석 활용이 부족한 구조

👉 핵심 문제  
“상담 데이터는 존재하지만, 이를 해석하고 활용하는 체계가 부족하다”

---

## 해결 방법

MindWay는 상담 데이터를 “흐름 기반 구조”로 재해석하여 문제를 해결합니다.

- 상담 세션 데이터를 구조화하여 상태 변화 흐름으로 분석
- 텍스트 감정 분석 + 표정 기반 비언어 신호 결합
- 상담 흐름을 Action 단계(0~5)로 정의하여 상태 전이 분석
- AI 헬퍼를 통해 상담 개입 방향 제안

---

## 상담 흐름 분석 구조 (핵심 차별점)

MindWay는 상담 대화를 단순 텍스트가 아닌  
“상태 변화 흐름”으로 해석합니다.

- Action 0: 상담 시작 및 불편 표현 구간  
- Action 4: 관계 및 사고 전환이 발생하는 핵심 구간  
- Action 5: 고강도 정서 신호 구간  

👉 이를 통해 상담 흐름의 변화를 정량적으로 분석하고 시각화

---

## 핵심 성과 지표

| 항목 | 성능 |
|------|------|
| 상담 이탈 감지 | F1 Score 0.960 |
| 감정 분석 | Macro F1 0.890 |
| 상담 흐름 예측 | MAE 8.0 / R² 0.777 |
| 상담 품질 예측 | MAE 8.0 / R² 0.759 |
| 영상 감정 분석 | Accuracy 0.70 / ROC-AUC 0.87 |
| AI 헬퍼 | 평균 응답 4.4초 / 품질 4.21 / 제안 포함률 98% |

---

## 🤖 AI 헬퍼 (핵심 기여)

상담 상황을 실시간으로 분석하여  
상담사가 다음 개입을 판단할 수 있도록 지원하는 AI 시스템

- HyperCLOVA X 기반 응답 생성
- JSON 구조화 출력으로 일관성 확보
- 평균 응답 속도 4.4초
- 상담 흐름 및 감정 상태 기반 개입 방향 제안
- 상담 개입 방향 제안 포함률 98%

👉 단순 질의응답 챗봇이 아닌  
👉 상담 맥락을 이해하고 개입 방향을 제시하는 시스템

---

## UX/UI 설계 (데이터 기반 UI)

단순 화면 구현이 아닌  
**데이터를 기반으로 의사결정을 지원하는 UI 설계**

- 상담 진행 상태를 직관적으로 보여주는 KPI 대시보드
- 실시간 감정 변화 시각화 인디케이터
- 세션별 상담 리포트 구조 설계
- 상담 흐름 변화(Action) 시각화

👉 “보여주는 UI”가 아닌 **“해석을 돕는 UI” 설계**

---

## 담당 역할

- 프로젝트 전체 AI 분석 구조 및 모델 선정 기획
- 상담 흐름 / 감정 분석 / 이탈 감지 구조 설계
- FastAPI 기반 백엔드 API 설계 및 구현
- AI 헬퍼 시스템 설계 및 구현 (HyperCLOVA X 활용)
- DB 설계 및 데이터 구조 정의
- NCP 환경 서버 구축 및 배포
- UX/UI 설계 및 프론트엔드 화면 구현

---

## 주요 기능

- 상담 세션 흐름 분석 및 시각화
- 텍스트 기반 감정 분석
- 표정 기반 비언어 신호 분석 (DeepFace)
- 상담 결과 리포트 생성
- AI 헬퍼 기반 상담 개입 제안

---

## 트러블슈팅

- 세션 상태 불일치 문제  
  → 예약/종료 상태 동기화 구조 재설계

- WebSocket 연결 불안정  
  → heartbeat 기반 연결 안정화

- 감정 분석 노이즈  
  → confidence threshold 필터링 적용

---

## 시스템 아키텍처

- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI
- AI: HyperCLOVA X, DeepFace
- Database: MySQL
- Infra: Docker, NCP

---

# MindWay — 개발 환경 가이드

심리상담 지원 플랫폼 MindWay의 공통 개발 환경 저장소입니다.
팀원 전체가 동일한 DB / API / 프론트엔드 환경에서 실행할 수 있도록 구성되어 있습니다.

---

##  기술 스택

| 구분 | 기술 |
|------|------|
| Database | Docker + MySQL (SMHRD 외부 서버, Port 3307) |
| Backend | FastAPI |
| Frontend | HTML / CSS / JavaScript |
| 텍스트 분석 | HyperCLOVA X |
| 표정 분석 | DeepFace |
| AI 헬퍼 | HyperCLOVA X (HCX-DASH-002) |
---

##  사전 설치

| 도구 | 확인 명령어 |
|------|------------|
| Docker Desktop | `docker --version` |
| Python 3.10 이상 | `python --version` |
| Git | `git --version` |

---

##  환경 설정

프로젝트 루트의 `.env.example`을 복사해 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

`.env` 필수 항목:

```dotenv
# DB
DB_HOST=<SMHRD 외부 서버 주소>
DB_PORT=3307
DB_USER=...
DB_PASSWORD=...
DB_NAME=mindway

# AI 헬퍼
USE_HCX=1
HCX_HOST=https://clovastudio.stream.ntruss.com
HCX_MODEL=HCX-DASH-002
HCX_API_KEY=...
HCX_REQUEST_ID=mindway-helper-local
HCX_TIMEOUT=20
HCX_HISTORY_WINDOW=8
```

> ⚠️ `.env` 파일은 절대 커밋하지 않습니다.

---

##  실행 순서

### 1. DB 실행 (로컬 테스트 시에만)

```bash
docker-compose up -d
docker ps   # MySQL 컨테이너 Up 상태 확인
```

---

### 2. FastAPI 실행

```bash
# 가상환경 생성 (최초 1회)
python -m venv .venv

# 가상환경 활성화
source .venv/Scripts/activate   # Windows
source .venv/bin/activate        # macOS / Linux

# 패키지 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload
```

정상 확인:
- Swagger Docs → http://127.0.0.1:8000/docs
- DB 상태 → http://127.0.0.1:8000/health/db

---

### 3. 프론트엔드 실행

VS Code Live Server 등으로 `frontend/` 폴더를 열거나, 아래 명령어로 실행합니다.

```bash
cd frontend
python -m http.server 5500
```

접속: http://127.0.0.1:5500

---

##  DB 초기화

### 스키마 적용

```bash
docker exec -i <mysql_container_name> mysql -u root -p mindway < schema_final_perfect.sql
```

### 시연용 데이터 입력

```bash
docker exec -i <mysql_container_name> mysql -u root -p mindway < seed.sql
```

> seed 데이터가 없으면 대시보드 목록이 비어 있을 수 있습니다.

---

##  주요 API

### 설계 원칙
- REST 기반 구조로 프론트엔드와 명확한 역할 분리
- 세션 상태(ACTIVE / CLOSED) 기반 접근 제어로 데이터 무결성 확보
- AI 분석은 세션 종료 시점에 트리거하여 실시간 부하 최소화

### API 목록

| 메서드 | 경로 | 설명 | 비고 |
|--------|------|------|------|
| GET | `/health/db` | DB 연결 상태 확인 | 배포 환경 모니터링용 |
| GET | `/sessions` | 세션 목록 조회 | 이탈 신호 강도 순 정렬 |
| GET | `/sessions/{sess_id}/dashboard` | 세션 상세 리포트 조회 | 감정·흐름·이탈 신호 통합 제공 |
| GET | `/sessions/{sess_id}/messages` | 대화 내역 조회 | 신호 탐지 구간 발화 로그 포함 |
| GET | `/stats/topic-dist` | 고민 유형 분포 통계 | 대시보드 KPI용 |
| POST | `/appt` | 예약 생성 | 중복 예약 방지 UNIQUE KEY 적용, 기존 예약 재사용 로직 구현 |
| POST | `/sessions/{sess_id}/close` | 세션 종료 + HCX 분석 트리거 | 종료 시점에 AI 분석 자동 실행 |
| POST | `/api/sessions/{sess_id}/analysis` | 세션 AI 분석 실행 | HyperCLOVA X 연동, 결과 DB 저장 |
| POST | `/helper/suggestion` | AI 헬퍼 실시간 제안 | 상담 중 맥락 기반 문구 자동 추천, 클릭 한 번으로 입력창 반영 |

---

### 핵심 API 상세

#### 1. 세션 종료 + AI 분석 자동 트리거
`POST /sessions/{sess_id}/close`

세션 종료 시점에 HyperCLOVA X 분석 파이프라인을 자동으로 실행합니다.  
종료와 분석을 단일 엔드포인트로 처리하여 프론트엔드의 추가 호출 없이 리포트가 생성됩니다.  
내부적으로 이탈 신호 감지(feature1) → 상담 요약 및 토픽 분류(feature2) → 감정 분석(feature3) → 품질 평가(feature4) 순으로 파이프라인이 실행되며, 결과는 각각 `alert` / `sess_analysis` / `text_emotion` / `quality` 테이블에 저장됩니다.
```json
// Response
{
  "ok": true,
  "result": {
    "feature1_alert_rows": [
      {
        "sess_id": 1,
        "msg_id": 42,
        "type": "CONTINUITY_SIGNAL",
        "status": "DETECTED",
        "score": 0.82,
        "rule": "QUIT_INTENT"
      }
    ],
    "feature2": {
      "summary": "내담자는 취업 실패와 관련된 스트레스를 경험하고 있으며...",
      "topic_id": 3
    },
    "emotion": {
      "items": [
        { "msg_id": 42, "label": "sad", "score": 0.51 },
        { "msg_id": 45, "label": "confusion", "score": 0.63 }
      ]
    },
    "quality": {
      "flow": 63.0,
      "score": 70.5,
      "meta": {
        "reason": "회피성 단답 2회 반복으로 흐름이 눈에 띄게 흔들림",
        "raw": { "flow": 63, "score": 70.5, "reason": "..." }
      }
    }
  }
}
```

#### 2. 세션 AI 분석 별도 실행
`POST /api/sessions/{sess_id}/analysis`

세션 종료 후 분석을 재실행하거나 수동으로 트리거할 때 사용합니다.  
내부적으로 `run_core_features` 파이프라인을 호출하며, 트랜잭션은 `get_db()` 의존성이 관리합니다.  
HyperCLOVA X API 호출 실패 시 429 응답에 대해 최대 3회 재시도(15초 간격)를 수행합니다.
```json
// Response
{
  "ok": true,
  "result": {
    "feature1_alert_rows": [ ... ],
    "feature2": { "summary": "...", "topic_id": 3 },
    "emotion": { "items": [ ... ] },
    "quality": { "flow": 75.0, "score": 80.0, "meta": { "reason": "..." } }
  }
}
```
#### 3. AI 헬퍼 실시간 제안
`POST /helper/suggestion`

상담 중 내담자의 최근 발화와 슬라이딩 윈도우 기반 대화 내역을 분석하여  
상담사에게 읽기용 분석 정보(`suggestions`)와 클릭 즉시 전송 가능한 응답 초안(`reply_candidates`) 3개를 함께 제공합니다.  
룰 기반 1차 필터(키워드 감지) → HyperCLOVA X 분석 순으로 처리하며,  
두 결과의 위험 수준 중 높은 쪽을 최종 반영합니다. HCX 호출 실패 시 룰 기반 응답으로 자동 fallback됩니다.
```json
// Request
{
  "sess_id": 1,
  "counselor_id": 3,
  "last_client_text": "솔직히 이 상담이 의미가 있는지 모르겠어요. 매번 똑같은 것 같고",
  "last_counselor_text": "지난주에 말씀하신 직장 상황은 좀 어떠세요?",
  "history": [
    {"role": "counselor", "text": "오늘 어떻게 오셨어요?"},
    {"role": "client", "text": "그냥 왔어요. 별로 할 말이 없는 것 같기도 하고요"}
  ]
}

// Response
{
  "mode": "HCX",
  "churn_signal": 1,
  "type": "CHURN_ALERT",
  "insight": "내담자가 상담 효과에 회의를 느끼며 반복되는 패턴에 지쳐있는 상태로 보임",
  "emotions": ["무기력", "회의감"],
  "intent": "변화에 대한 욕구가 있으나 기대가 낮아진 상태일 가능성(단정 금지)",
  "risk": {
    "level": "Caution",
    "signals": ["상담 의미 의문 표현", "반복 패턴 언급"],
    "message": "이탈로 단정하지 말고, 부담/기대/저항 지점을 안전하게 확인하세요."
  },
  "suggestions": [
    {
      "type": "회피/이탈 탐색",
      "rationale": "상담 의미에 대한 회의 표현",
      "direction": "상담에 대한 기대/부담/저항 지점을 안전하게 탐색"
    },
    {
      "type": "공감 심화",
      "rationale": "매번 똑같다는 반복감 표현",
      "direction": "감정 반영 후 가장 변화 없다고 느끼는 지점을 구체 상황으로 좁혀 확인"
    },
    {
      "type": "목표/다음단계",
      "rationale": "동기 저하 가능성",
      "direction": "이번 대화에서 최소한 얻고 싶은 것 1가지를 합의하고 작게 진행"
    }
  ],
  "reply_candidates": [
    {
      "text": "매번 똑같다는 느낌이 드실 때 가장 지치는 부분이 어떤 건지, 조금 더 이야기해 주실 수 있을까요?",
      "why": "반복감의 구체적 지점을 파악하여 탐색 방향 설정"
    },
    {
      "text": "상담이 의미 없다는 느낌이 언제부터 드셨는지, 어떤 순간에 그 생각이 가장 크게 느껴지셨나요?",
      "why": "회의감의 촉발 시점 및 맥락 구체화"
    },
    {
      "text": "지금 이 상담에서 단 한 가지라도 달라졌으면 하는 게 있다면 어떤 건지 여쭤봐도 될까요?",
      "why": "변화 욕구 및 최소 목표 탐색"
    }
  ]
}
```
#### 4. 표정 기반 감정 분석
`POST /deepface/analyze`

DeepFace + RetinaFace를 활용하여 내담자의 표정을 실시간으로 분석합니다.  
EMA(지수 이동 평균, α=0.55)를 적용해 프레임 간 노이즈를 줄이고,  
서비스용 3단계 라벨(positive / neutral / caution)로 변환하여 제공합니다.  
confidence 0.48 미만이거나 1·2위 라벨 차이가 0.10 미만이면 neutral로 fallback 처리합니다.
```json
// Response
{
  "status": "success",
  "dominant": "caution",
  "score": 0.72,
  "scores": {
    "angry": 0.41, "disgust": 0.12, "fear": 0.09,
    "happy": 0.03, "sad": 0.28, "surprise": 0.01, "neutral": 0.06
  },
  "dist3": {
    "positive": 0.04,
    "neutral": 0.06,
    "caution": 0.90
  },
  "ui": { "label": "caution", "score": 0.72 },
  "reason": "ok",
  "meta": {
    "quality": "ok",
    "engine": "deepface",
    "detector": "retinaface",
    "aligned": true,
    "latency_ms": 340
  }
}
```

---

### 주요 트러블슈팅 (API 관련)

| 문제 | 원인 | 해결 |
|------|------|------|
| 예약 데이터 중복 생성 | 예약 생성 API에 중복 검증 로직 부재 | DB에 `UNIQUE KEY(client_id, counselor_id, at)` 제약 추가 + 예약 전 중복 조회 로직 구현 |
| 세션 종료 후에도 메시지 저장 | 세션 상태 검증 없이 메시지 INSERT 허용 | 메시지 저장 전 `sess.progress` 상태 검증, ACTIVE 상태에서만 저장 허용 |
| WebSocket 1006 오류 (배포 환경) | Nginx가 WebSocket Upgrade 헤더를 전달하지 않음 | `proxy_http_version 1.1` + Upgrade·Connection 헤더 설정, `/ws/` 전용 프록시 경로 분리 |

---

##  자주 발생하는 오류

### API 404 오류
실행 위치가 올바른지 확인합니다.
```bash
# 루트 폴더 기준 실행
uvicorn main:app --reload
```
http://127.0.0.1:8000/docs 에서 API 목록을 확인하세요.

---

### DB 연결 실패
1. `docker ps` — MySQL 컨테이너 Up 상태인지 확인 (로컬 사용 시)
2. `.env`의 `DB_PORT=3307` 확인
3. http://127.0.0.1:8000/health/db 응답에 `"db": "ok"` 확인

---

### 대시보드가 비어 있음
seed.sql이 입력됐는지 확인합니다.
```bash
docker exec -i <mysql_container_name> mysql -u root -p mindway < seed.sql
```

---


---

##  주요 파일 구조

```
mindway/
├── main.py                  # FastAPI 엔트리포인트
├── db.py                    # DB 연결 및 설정
├── routers/
│   ├── api.py               # API 라우팅
│   ├── helper.py            # AI 헬퍼 (HCX 기반)
│   ├── deepface.py          # 표정 분석 로직
│   └── analysis/            # 텍스트 분석 및 데이터 처리
├── frontend_test/           # 프론트엔드 화면 및 클라이언트 UI 파일
│   ├── Main.html            # 상담사 메인 대시보드
│   ├── SessionDetail.html   # 세션 상세 리포트
│   ├── Chat_counselor.html  # 상담사 채팅
│   ├── Chat_client.html     # 내담자 채팅
│   ├── Login_client.html    # 내담자 로그인 / 예약
│   ├── Login_counselor.html # 상담사 로그인
│   ├── Landing.html         # 랜딩 페이지
│   ├── config.js            # 프론트엔드 설정
│   └── Logo.png             # 서비스 로고
├── deploy/
│   └── nginx/
│       └── fastapi_proxy    # Nginx 리버스 프록시 설정
├── docker-compose.yml       # DB 컨테이너 구성
├── deploy.sh                # 서버 배포 스크립트
├── run.bat                  # Windows 실행 스크립트
├── requirements.txt         # 로컬 개발용 패키지 목록
├── requirements.server.txt  # 서버 배포용 패키지 목록
├── schema_final_perfect.sql # 최종 DB 스키마
├── seed.sql                 # 시연용 데이터
├── seed_min.sql             # 최소 테스트 데이터
└── .env.example             # 환경 변수 예시 파일
```

---

##  Git 작업

```bash
git add .
git commit -m "이안 : 변경 내용 간략히"
git push origin main
```

> LF / CRLF 경고는 대부분 무시 가능합니다.
