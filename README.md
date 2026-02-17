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
✅ 2. DB 실행 (최초 / 공통)
프로젝트 루트에서 실행:

docker-compose up -d
정상 확인:

docker ps
MySQL 컨테이너가 Up 상태면 성공.

✅ 3. DB 접속 확인 (선택)
컨테이너 이름 확인 후:

docker exec -it <mysql_container_name> mysql -u root -p
DB 확인:

SHOW DATABASES;
USE mindway;
SHOW TABLES;
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
❌ API 오류 / 404 발생
원인:

FastAPI에 해당 엔드포인트가 없음

uvicorn 실행 위치 불일치

해결:

Swagger 확인:

http://127.0.0.1:8000/docs

실행 위치 확인:

루트 main.py:

uvicorn main:app --reload
backend 폴더 구조:

uvicorn backend.main:app --reload
❌ DB 연결 실패
확인 순서:

Docker 컨테이너 상태 확인:

docker ps
.env DB 설정 확인

/health/db 호출 확인

❌ 대시보드 표가 비어 있음
원인:

seed 데이터 없음

sess 테이블 데이터 없음

해결:

mysql < seed.sql
✅ 10. Git 기본 작업
git add .
git commit -m "update"
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

