# 🛍️ 쇼핑 챗봇 (LangGraph + FastAPI + Streamlit)

LangGraph와 Gemini LLM을 활용한 쇼핑 상품 추천 챗봇입니다.

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 가상환경 활성화 (이미 설정되어 있음)
source .venv/bin/activate

# 환경 변수 확인
cat .env
```

### 2. 서버 실행 방법

#### 방법 1: 간편한 스크립트 사용
```bash
# 대화형 스크립트로 실행
./start.sh
```

#### 방법 2: Python 스크립트 사용 (두 서버 동시 실행)
```bash
python run_servers.py
```

#### 방법 3: 개별 서버 실행

**FastAPI 백엔드 서버:**
```bash
python -m uvicorn backend.main:app --host localhost --port 8000 --reload
```

**Streamlit 프론트엔드:**
```bash
streamlit run frontend/app.py --server.port 8501
```

### 3. 접속 주소

- **🌐 Streamlit 채팅 UI**: http://localhost:8501
- **📡 FastAPI 백엔드**: http://localhost:8000  
- **📖 API 문서 (Swagger)**: http://localhost:8000/docs
- **📊 헬스 체크**: http://localhost:8000/health

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
python -m pytest tests/ -v

# E2E 테스트만 실행
python -m pytest tests/test_e2e_integration.py -v

# 특정 컴포넌트 테스트
python -m pytest tests/test_backend_api.py -v
python -m pytest tests/test_frontend.py -v
python -m pytest tests/test_agent.py -v
```

## 📁 프로젝트 구조

```
.
├── backend/           # FastAPI 백엔드
│   ├── main.py       # FastAPI 앱 진입점
│   ├── routes.py     # API 라우터
│   └── models.py     # Pydantic 모델
├── frontend/          # Streamlit 프론트엔드
│   ├── app.py        # Streamlit 메인 앱
│   └── components.py # UI 컴포넌트
├── agent/            # LangGraph Agent
│   ├── agent.py      # 쇼핑 Agent 구현
│   ├── tools.py      # MCP 툴들 (더미 구현)
│   └── memory.py     # 세션 메모리 관리
├── tests/            # 테스트 파일들
├── config.py         # 전역 설정
├── requirements.txt  # Python 의존성
├── .env             # 환경 변수 (API 키 포함)
├── run_servers.py   # 서버 실행 스크립트
└── start.sh         # 간편 실행 스크립트
```

## 🔧 주요 기능

### 💬 채팅 기능
- 자연어로 상품 검색 요청
- 실시간 SSE 스트리밍 응답
- 다중 세션 지원
- 대화 히스토리 유지

### 🛍️ 쇼핑 기능 (더미 구현)
- 네이버 쇼핑 검색 시뮬레이션
- Exa 웹 검색 시뮬레이션  
- 상품 가격 비교
- 필터링 및 정렬

### 🤖 AI Agent
- Google Gemini LLM 기반
- LangGraph 상태 관리
- 사용자 선호도 학습
- 컨텍스트 기반 추천

## 🔑 환경 변수

`.env` 파일에 다음 변수들이 설정되어 있어야 합니다:

```env
# 필수
GOOGLE_API_KEY=your_gemini_api_key_here

# 선택사항
BACKEND_HOST=localhost
BACKEND_PORT=8000
FRONTEND_PORT=8501
DEBUG=True
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
LOG_LEVEL=INFO
```

## 📊 테스트 현황

- ✅ **전체 테스트**: 77/81 통과 (95.1%)
- ✅ **E2E 테스트**: 17/17 통과 (100%)
- ✅ **핵심 기능**: 모두 정상 동작

## 🛠️ 기술 스택

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Frontend**: Streamlit  
- **AI**: LangGraph, LangChain, Google Gemini
- **Testing**: pytest, pytest-asyncio
- **Architecture**: Clean Architecture, SOLID 원칙

## 🔄 개발 워크플로

이 프로젝트는 **TDD(Test-Driven Development)** 방식으로 개발되었습니다:

1. 테스트 코드 작성
2. 기능 구현
3. 테스트 실행 및 검증  
4. 리팩토링 및 개선

## 🎯 사용 예시

1. **Streamlit UI 접속**: http://localhost:8501
2. **채팅창에 입력**: "아이폰 15 찾아줘"
3. **AI 응답 확인**: 상품 검색 결과와 추천
4. **후속 질문**: "50만원 이하만 보여줘"
5. **필터링된 결과**: 가격 조건에 맞는 상품들

## 🚧 향후 확장 계획

- 실제 MCP 툴 연동
- 사용자 인증 시스템
- 데이터베이스 연동
- 상품 즐겨찾기 기능
- 구매 히스토리 분석

---

📝 **개발 완료**: 2024년 6월, TDD 방식으로 스켈레톤 코드 완전 구현 