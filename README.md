# 📅 수련회 행사 체크리스트 관리 시스템 (Event Planning & Retreat App)

이 프로젝트는 교회 전교인 수련회 또는 다양한 단체 행사를 준비할 때 필요한 업무 및 체크리스트를 체계적으로 관리할 수 있는 **웹 기반 체크리스트 관리 애플리케이션**입니다. 

파이썬(Flask)과 경량 데이터베이스(SQLite3)를 사용하여 가볍고 빠르게 작동하며, 로컬 환경은 물론 Docker 컨테이너 환경에서도 즉시 실행할 수 있습니다.

---

## ✨ 주요 기능

1. **행사(Event) 관리 및 자동 복사**:
   - 새로운 행사를 등록할 수 있습니다.
   - 새 행사 등록 시, **기존 탬플릿(기본 55개 체크리스트 항목)**의 항목들을 자동으로 복사하여 세팅할 수 있는 옵션을 제공합니다.
2. **실시간 체크리스트 관리**:
   - 행사별로 진행되어야 하는 세부 업무(총무, 버스 예약, 숙소 배정, 간식, 음향 등 55개 필수 항목 기본 포함)를 추적할 수 있습니다.
   - 각 항목의 담당자(Assignee), 체크 포인트(Check point), 특이사항(Remark)을 한눈에 파악할 수 있습니다.
3. **업무 상태 토글 및 삭제**:
   - 업무가 완료되었을 때 체크박스를 선택하여 실시간으로 완료 상태를 전환(Toggle)할 수 있습니다.
   - 불필요한 체크리스트 항목은 동적으로 삭제 가능합니다.
4. **반응형 웹 UI**:
   - 데스크톱뿐만 아니라 모바일에서도 간편하게 확인하고 업데이트할 수 있도록 미려한 디자인의 반응형 웹 화면을 제공합니다.

---

## 🛠 기술 스택

- **Backend**: Python 3.11+, Flask
- **Database**: SQLite3 (경량 파일 데이터베이스, 별도 DBMS 설치 불필요)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (AJAX 기반)
- **Container**: Docker (Slim-debian 기반 경량 이미지)

---

## 📂 프로젝트 구조

```text
eventPlanning/
├── retreat_app/
│   ├── app.py           # Flask 메인 애플리케이션 (API 라우트 및 DB 초기화)
│   ├── test_app.py      # 비즈니스 로직 및 API 유닛 테스트 코드
│   ├── checklist.db     # SQLite 로컬 데이터베이스 (자동 생성됨)
│   └── templates/
│       └── index.html   # 메인 웹 페이지 대시보드 (HTML/CSS/JS 통합)
├── Dockerfile           # 도커 컨테이너 빌드 파일
├── requirements.txt     # 파이썬 라이브러리 의존성 파일
├── .gitignore           # 버전 관리에서 제외할 파일 목록 (.db, 캐시 등)
└── README.md            # 본 안내서 파일
```

---

## 🚀 실행 안내

### 방법 1: 로컬 PC에서 직접 실행 (Python 환경)

#### 1. 의존성 패키지 설치
로컬 PC에 Python이 설치되어 있어야 합니다. 터미널 또는 명령 프롬프트(CMD)에서 아래 명령어를 실행하여 필요한 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

#### 2. 애플리케이션 실행
설치가 완료되면 Flask 서버를 실행합니다.
```bash
python retreat_app/app.py
```
- 서버가 정상 구동되면 자동으로 `checklist.db` 파일이 생성되고 기본 행사("2026 하계수련회") 및 55개의 기본 업무 체크리스트가 시딩(Seeding)됩니다.

#### 3. 웹 브라우저 접속
브라우저를 열고 다음 주소로 접속합니다.
```text
http://localhost:5000
```

---

### 방법 2: Docker 컨테이너를 통한 실행

도커가 설치되어 있다면 복잡한 파이썬 환경 설정 없이 명령어 두 번으로 즉시 안정적으로 실행 가능합니다.

#### 1. Docker 이미지 빌드
프로젝트 루트 폴더에서 아래 명령을 실행하여 이미지를 빌드합니다.
```bash
docker build -t event-planning .
```

#### 2. Docker 컨테이너 실행
빌드 완료 후 아래 명령어로 컨테이너를 구동합니다. (포트 5000번 매핑)
```bash
docker run -d -p 5000:5000 --name event-app event-planning
```

#### 3. 웹 브라우저 접속
```text
http://localhost:5000
```

---

## 🧪 테스트 코드 실행

애플리케이션의 동작과 API가 안정적인지 유닛 테스트를 통해 검증할 수 있습니다.

```bash
python -m unittest retreat_app/test_app.py
```
- 테스트 실행 시 데이터 무결성을 검증하기 위해 별도의 `test_checklist.db` 파일이 임시로 사용된 후 안전하게 삭제됩니다.
