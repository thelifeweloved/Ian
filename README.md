# MindWay — 개발 환경 가이드

심리상담 지원 플랫폼 MindWay의 공통 개발 환경 저장소입니다.
팀원 전체가 동일한 DB / API / 프론트엔드 환경에서 실행할 수 있도록 구성되어 있습니다.

---

##  기술 스택

| 구분 | 기술 |
|------|------|
| Database | Docker + MySQL (SMHRD 외부 서버, Port 3307) |
| Backend | FastAPI (각 팀원 로컬, Port 8000) |
| Frontend | HTML / JS (각 팀원 로컬, Port 5500) |
| AI 분석 | HyperCLOVA X (HCX-DASH-002) |

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

> 팀 공용 SMHRD 외부 서버를 사용하는 경우 이 단계는 건너뜁니다.

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

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health/db` | DB 연결 상태 확인 |
| GET | `/sessions` | 세션 목록 |
| GET | `/sessions/{sess_id}/dashboard` | 세션 상세 |
| GET | `/sessions/{sess_id}/messages` | 대화 내역 |
| POST | `/appt` | 예약 생성 (즉시 CONFIRMED) |
| POST | `/helper/suggestion` | AI 헬퍼 제안 |
| POST | `/sessions/{sess_id}/close` | 세션 종료 + HCX 분석 트리거 |
| GET | `/stats/topic-dist` | 고민 유형 분포 통계 |

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

##  팀 개발 규칙

- DB 스키마 임의 변경 금지 — ENUM / CHECK 수정 시 팀 공유 필수
- API 경로 변경 시 프론트엔드 동시 수정
- seed.sql 변경 시 팀 공지
- `.env` 파일 커밋 금지

---

##  주요 파일 구조

```
mindway/
├── main.py              # FastAPI 엔트리포인트
├── helper.py            # AI 헬퍼 (HCX 연동)
├── runner.py            # 세션 종료 후 HCX 분석 실행
├── requirements.txt
├── .env.example
├── schema_final_perfect.sql
├── seed.sql
└── frontend/
    ├── Main.html            # 상담사 메인 대시보드
    ├── SessionDetail.html   # 세션 상세 리포트
    ├── Chat_counselor.html  # 상담사 채팅
    ├── Chat_client.html     # 내담자 채팅
    ├── Login_client.html    # 내담자 로그인 / 예약
    └── Login_counselor.html # 상담사 로그인
```

---

##  Git 작업

```bash
git add .
git commit -m "이안 : 변경 내용 간략히"
git push origin main
```

> LF / CRLF 경고는 대부분 무시 가능합니다.
