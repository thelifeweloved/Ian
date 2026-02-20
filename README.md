# MindWay DB & API Environment

MindWay 프로젝트 공통 개발 환경 저장소입니다.  
팀원 전체가 동일한 DB / API / 대시보드 환경에서 실행 및 개발할 수 있도록 구성되어 있습니다.

본 프로젝트 환경:

- Docker + MySQL (Database)
- FastAPI (Backend API)
- Streamlit (Dashboard UI)

---

## ✅ 1. 필수 설치 (모든 팀원)

각 팀원 PC에 반드시 설치:

- Docker Desktop
- Python 3.10 이상 (권장 3.11)
- Git (권장)
- (Windows) Git Bash 또는 PowerShell

설치 확인:

```bash
docker --version
python --version
git --version

🛠️ 환경 설정 (중요: 외부 서버 연동)
팀원 전체가 동일한 데이터를 바라보기 위해 SMHRD 외부 DB 서버 설정을 우선합니다.

프로젝트 루트의 .env.example 파일을 복사하여 .env 파일을 생성합니다.

🛠️ 데이터 확인 및 입력
Schema: schema_final_perfect.sql을 기준으로 합니다.

Seed 데이터: 통계 분석 및 Action 0-4-5 단계 시연을 위해 seed.sql 입력을 권장합니다.

✅ 2. DB 실행 (최초 / 공통)
프로젝트 루트에서 실행:

docker-compose up -d
정상 확인:

docker ps
MySQL 컨테이너가 Up 상태면 성공.

(로컬 테스트가 필요한 경우에만 docker-compose up -d를 실행합니다.)

✅ 3. DB 접속 확인 (선택)
컨테이너 이름 확인 후:

docker exec -it <mysql_container_name> mysql -u root -p
DB 확인:

SHOW DATABASES;
USE mindway;
SHOW TABLES;

우리 프로젝트는 분산 서버 환경을 지향합니다.

- Database: SMHRD 외부 서버 (Port: 3307)
- Backend: 각 팀원 로컬에서 실행 (Port: 8000)
- Frontend: 각 팀원 로컬에서 실행 (Port: 8501)

✅ 4. seed 데이터 입력 (권장)
시연 / 테스트 / 통계 확인용:

docker exec -i <mysql_container_name> mysql -u root -p mindway < seed.sql
seed 데이터가 없으면 세션 목록이 비어 있을 수 있습니다.

✅ 5. FastAPI 실행
가상환경 생성 (권장):

python -m venv .venv
가상환경 활성화:

Windows:

source .venv/Scripts/activate
macOS / Linux:

source .venv/bin/activate
패키지 설치:

pip install -r requirements.txt
서버 실행:

uvicorn main:app --reload
접속 확인:

Swagger Docs → http://127.0.0.1:8000/docs

DB Health Check → http://127.0.0.1:8000/health/db


✅ 6. Streamlit 대시보드 실행
새 터미널에서 실행:

streamlit run dashboard.py
접속:

http://localhost:8501

✅ 7. 주요 API 목록 (대시보드 연동)
기본 API:

GET /health/db

GET /sessions

POST /messages

세션 상세 API:

GET /sessions/{sess_id}/dashboard

GET /sessions/{sess_id}/messages

GET /sessions/{sess_id}/alerts

사후 분석 API:

GET /stats/topic-dropout

GET /stats/client-grade-dropout

GET /stats/missed-alerts

GET /stats/time-dropout

GET /stats/channel-dropout

GET /stats/monthly-growth

✅ 8. 빠른 시연 가이드
Streamlit 접속

세션 선택

상담 시뮬레이터 → CLIENT 선택

입력:

너무 힘들어요 그만하고 싶어요
전송 → alerts 생성 확인

Risk Score / 사후 분석 표 확인

✅ 9. 자주 발생하는 문제 해결
❌ API 오류 / 404 Not Found 발생
원인: 루트 폴더(ThinkBIG_main)에서 실행 시 하위 폴더 경로를 누락했거나 엔드포인트가 정의되지 않음

해결 1 (실행 위치: ThinkBIG_main 기준):

FastAPI 실행: uvicorn counseling_project.main:app --reload

Streamlit 실행: streamlit run counseling_project/frontend/app_ui.py

해결 2 (경로 확인):

Swagger Docs: http://127.0.0.1:8000/docs 접속 후 API 목록 확인

DB Health: http://127.0.0.1:8000/health/db 호출 시 404가 뜨면 main.py 내 해당 경로 정의 확인

❌ DB 연결 실패 (Connection Error)
원인: SMHRD 외부 서버 포트(3307) 미설정 또는 도커 컨테이너 미작동

확인 순서:

컨테이너 상태: docker ps 명령어로 MySQL 컨테이너가 Up 상태인지 확인 (로컬 DB 사용 시)

환경 변수: .env 파일의 DB_PORT가 3307로 설정되어 있는지 확인 (외부 서버 접속 필수)

접속 테스트: /health/db 호출 시 응답에 "db": "ok"가 뜨는지 확인

❌ 대시보드 표가 비어 있음 (No Data)
원인: sess 테이블 데이터 부재 또는 초기화 스크립트 미실행

해결:

데이터 주입: mysql -u [USER] -p mindway < seed.sql (루트 폴더에 파일이 있으므로 counseling_project/ 경로를 뺍니다.)

세션 생성: streamlit run counseling_project/frontend/pages/01_client_chat_ui.py 실행 후 테스트 대화 입력

✅ 10. Git 기본 작업
git add .
git commit -m "update" ("" 내용은 본인이 수정한 내용 이름 붙여서 상세 기재)
git push origin main
LF / CRLF 경고는 대부분 무시 가능.

✅ 11. 팀 개발 규칙
DB 스키마 임의 변경 금지

ENUM / CHECK 변경 시 팀 공유 필수

API 경로 변경 시 dashboard.py 동시 수정

seed.sql 변경 시 공지

✅ 12. 권장 실행 순서
1️⃣ Docker DB 실행
2️⃣ FastAPI 실행
3️⃣ Streamlit 실행

🚀 정상 실행 기준
/docs 접속 가능

세션 목록 표시

메시지 전송 가능

alerts 생성 가능

통계 API 오류 없음

