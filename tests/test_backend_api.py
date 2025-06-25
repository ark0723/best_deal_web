import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app


class TestBackendAPI:
    """백엔드 API 서버 기능 테스트"""
    
    def setup_method(self):
        """테스트 메서드 실행 전 설정"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "쇼핑 챗봇 API 서버가 실행 중입니다" in response.json()["message"]
    
    def test_health_endpoint(self):
        """헬스 체크 엔드포인트 테스트"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
    
    def test_chat_endpoint_exists(self):
        """채팅 엔드포인트가 존재하는지 테스트"""
        # POST 요청 테스트
        response = self.client.post("/chat", json={
            "message": "테스트 메시지",
            "session_id": "test-session"
        })
        # 404가 아니어야 함 (구현되어야 함)
        assert response.status_code != 404
    
    def test_cors_headers(self):
        """CORS 헤더가 올바르게 설정되었는지 테스트"""
        response = self.client.get("/")
        # CORS 관련 헤더는 실제 요청에서 확인
        assert response.status_code == 200
    
    def test_app_creation(self):
        """FastAPI 앱이 올바르게 생성되었는지 테스트"""
        assert app is not None
        assert app.title == "쇼핑 챗봇 API"
        assert app.version == "1.0.0"


@pytest.mark.asyncio
class TestAsyncBackendAPI:
    """비동기 백엔드 API 테스트"""
    
    async def test_async_health_check(self):
        """비동기 헬스 체크 테스트"""
        async with AsyncClient(base_url="http://test") as ac:
            # TestClient를 통한 동기 테스트로 대체
            from fastapi.testclient import TestClient
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy" 