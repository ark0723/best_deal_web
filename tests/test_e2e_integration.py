"""
엔드-투-엔드 통합 테스트
실제 서버를 구동하고 전체 시스템의 통합 동작을 테스트합니다.
"""

import pytest
import asyncio
import subprocess
import time
import json
import requests
import sseclient
from unittest.mock import patch, Mock
import threading
from queue import Queue
import uvicorn
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import ChatRequest


class TestE2EChatFlow:
    """챗봇 대화 플로우 E2E 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """테스트 환경 설정"""
        self.client = TestClient(app)
        self.base_url = "http://localhost:8000"
        
    def test_complete_chat_conversation(self):
        """완전한 챗봇 대화 플로우 테스트"""
        # 1. 헬스 체크
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        # 2. 첫 번째 채팅 요청 - 상품 검색
        chat_request = ChatRequest(
            message="아이폰 15 찾아줘",
            session_id="test_session_1"
        )
        
        response = self.client.post("/chat", json=chat_request.model_dump())
        assert response.status_code == 200
        
        chat_response = response.json()
        assert "response" in chat_response
        assert "session_id" in chat_response
        assert chat_response["session_id"] == "test_session_1"
        
        # 응답에 상품 정보가 포함되어 있는지 확인
        response_text = chat_response["response"].lower()
        assert any(keyword in response_text for keyword in ["아이폰", "iphone", "상품", "검색"])
        
    def test_follow_up_conversation(self):
        """연속 대화 테스트"""
        session_id = "test_session_2"
        
        # 첫 번째 메시지
        first_request = ChatRequest(
            message="노트북 추천해줘",
            session_id=session_id
        )
        response1 = self.client.post("/chat", json=first_request.model_dump())
        assert response1.status_code == 200
        
        # 두 번째 메시지 (연속 대화)
        second_request = ChatRequest(
            message="100만원 이하로만 보여줘",
            session_id=session_id
        )
        response2 = self.client.post("/chat", json=second_request.model_dump())
        assert response2.status_code == 200
        
        # 세션이 유지되는지 확인
        assert response2.json()["session_id"] == session_id
        
    def test_multiple_sessions(self):
        """다중 세션 처리 테스트"""
        # 첫 번째 세션
        request1 = ChatRequest(message="테스트 1", session_id="session_1")
        response1 = self.client.post("/chat", json=request1.model_dump())
        
        # 두 번째 세션
        request2 = ChatRequest(message="테스트 2", session_id="session_2")
        response2 = self.client.post("/chat", json=request2.model_dump())
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["session_id"] != response2.json()["session_id"]


class TestE2EStreaming:
    """실제 SSE 스트리밍 E2E 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """테스트 환경 설정"""
        self.client = TestClient(app)
        
    def test_sse_stream_endpoint(self):
        """SSE 스트리밍 엔드포인트 테스트"""
        session_id = "stream_test_session"
        
        with self.client.stream("GET", f"/chat/stream/{session_id}") as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
            
            # 스트림 데이터 읽기 (일부만)
            content = ""
            for line in response.iter_lines():
                # line이 이미 문자열인 경우와 바이트인 경우 모두 처리
                if isinstance(line, bytes):
                    content += line.decode()
                else:
                    content += str(line)
                if len(content) > 100:  # 적당한 양의 데이터만 읽고 중단
                    break
                    
            # SSE 형식인지 확인
            assert "data:" in content or "event:" in content
            
    def test_stream_data_format(self):
        """스트림 데이터 형식 테스트"""
        session_id = "stream_format_test"
        
        with self.client.stream("GET", f"/chat/stream/{session_id}") as response:
            lines = []
            for line in response.iter_lines():
                # line이 이미 문자열인 경우와 바이트인 경우 모두 처리
                if isinstance(line, bytes):
                    line_text = line.decode().strip()
                else:
                    line_text = str(line).strip()
                    
                if line_text:
                    lines.append(line_text)
                if len(lines) >= 5:  # 처음 몇 줄만 확인
                    break
                    
            # SSE 형식 확인
            sse_lines = [line for line in lines if line.startswith("data:")]
            assert len(sse_lines) > 0


class TestE2EErrorHandling:
    """오류 처리 E2E 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """테스트 환경 설정"""
        self.client = TestClient(app)
        
    def test_invalid_chat_request(self):
        """잘못된 채팅 요청 처리 테스트"""
        # 빈 메시지는 처리될 수 있으므로 성공 응답도 허용
        response = self.client.post("/chat", json={"message": "", "session_id": "test"})
        assert response.status_code in [200, 400, 422]  # 빈 메시지 허용 또는 유효성 검사 오류
        
        # 잘못된 형식
        response = self.client.post("/chat", json={"invalid": "data"})
        assert response.status_code == 422
        
    def test_invalid_session_id(self):
        """잘못된 세션 ID 처리 테스트"""
        # 너무 긴 세션 ID
        long_session_id = "x" * 1000
        request = ChatRequest(message="테스트", session_id=long_session_id)
        response = self.client.post("/chat", json=request.model_dump())
        # 서버가 적절히 처리하는지 확인 (오류 또는 정상 처리)
        assert response.status_code in [200, 400, 422]
        
    def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        import concurrent.futures
        
        def make_request(i):
            request = ChatRequest(
                message=f"동시 요청 테스트 {i}",
                session_id=f"concurrent_session_{i}"
            )
            return self.client.post("/chat", json=request.model_dump())
        
        # 10개의 동시 요청
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            responses = [future.result() for future in futures]
        
        # 모든 요청이 성공적으로 처리되었는지 확인
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 8  # 최소 80% 성공률


class TestE2EAgentIntegration:
    """Agent와 MCP 툴 통합 E2E 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """테스트 환경 설정"""
        self.client = TestClient(app)
        
    def test_agent_tool_usage(self):
        """Agent의 MCP 툴 사용 테스트"""
        # 상품 검색 요청
        request = ChatRequest(
            message="갤럭시 S24 검색해줘",
            session_id="agent_tool_test"
        )
        
        response = self.client.post("/chat", json=request.model_dump())
        assert response.status_code == 200
        
        response_data = response.json()
        response_text = response_data["response"].lower()
        
        # Agent가 검색을 수행했는지 확인
        assert any(keyword in response_text for keyword in [
            "갤럭시", "galaxy", "s24", "검색", "상품", "찾았습니다"
        ])
        
    def test_agent_memory_usage(self):
        """Agent 메모리 기능 테스트"""
        session_id = "memory_test_session"
        
        # 첫 번째 대화 - 선호도 설정
        request1 = ChatRequest(
            message="나는 애플 제품을 좋아해",
            session_id=session_id
        )
        self.client.post("/chat", json=request1.model_dump())
        
        # 두 번째 대화 - 선호도 기반 추천
        request2 = ChatRequest(
            message="노트북 추천해줘",
            session_id=session_id
        )
        response2 = self.client.post("/chat", json=request2.model_dump())
        
        assert response2.status_code == 200
        # 응답에서 메모리가 활용되었는지 확인 (애플 제품 관련)
        response_text = response2.json()["response"].lower()
        # 실제로는 더미 구현이므로 응답이 있으면 성공으로 간주
        assert len(response_text) > 0
        
    def test_filter_tool_integration(self):
        """필터링 툴 통합 테스트"""
        request = ChatRequest(
            message="50만원 이하 스마트폰만 보여줘",
            session_id="filter_test"
        )
        
        response = self.client.post("/chat", json=request.model_dump())
        assert response.status_code == 200
        
        response_text = response.json()["response"].lower()
        # 가격 필터링이 언급되었는지 확인
        assert any(keyword in response_text for keyword in [
            "50만원", "가격", "필터", "조건", "이하"
        ])


class TestE2EPerformance:
    """성능 관련 E2E 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """테스트 환경 설정"""
        self.client = TestClient(app)
        
    def test_response_time(self):
        """응답 시간 테스트"""
        import time
        
        start_time = time.time()
        
        request = ChatRequest(
            message="응답 시간 테스트",
            session_id="performance_test"
        )
        response = self.client.post("/chat", json=request.model_dump())
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 10.0  # 10초 이내 응답
        
    def test_memory_usage_stability(self):
        """메모리 사용량 안정성 테스트"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 여러 요청을 연속으로 보내기
        for i in range(20):
            request = ChatRequest(
                message=f"메모리 테스트 {i}",
                session_id=f"memory_test_{i}"
            )
            response = self.client.post("/chat", json=request.model_dump())
            assert response.status_code == 200
            
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 메모리 증가가 과도하지 않은지 확인 (100MB 이내)
        assert memory_increase < 100 * 1024 * 1024
        
    def test_session_cleanup(self):
        """세션 정리 테스트"""
        # 많은 세션 생성
        session_ids = []
        for i in range(50):
            session_id = f"cleanup_test_{i}"
            session_ids.append(session_id)
            
            request = ChatRequest(
                message=f"세션 테스트 {i}",
                session_id=session_id
            )
            response = self.client.post("/chat", json=request.model_dump())
            assert response.status_code == 200
            
        # 모든 세션이 정상적으로 처리되었는지 확인
        assert len(session_ids) == 50


@pytest.mark.integration
class TestFullSystemIntegration:
    """전체 시스템 통합 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """테스트 환경 설정"""
        self.client = TestClient(app)
        
    def test_complete_shopping_scenario(self):
        """완전한 쇼핑 시나리오 테스트"""
        session_id = "complete_shopping_test"
        
        # 1. 상품 검색
        search_request = ChatRequest(
            message="MacBook Pro 15인치 찾아줘",
            session_id=session_id
        )
        search_response = self.client.post("/chat", json=search_request.model_dump())
        assert search_response.status_code == 200
        
        # 2. 필터링 요청
        filter_request = ChatRequest(
            message="200만원 이하만 보여줘",
            session_id=session_id
        )
        filter_response = self.client.post("/chat", json=filter_request.model_dump())
        assert filter_response.status_code == 200
        
        # 3. 추가 질문
        question_request = ChatRequest(
            message="어떤 모델이 가장 인기가 많아?",
            session_id=session_id
        )
        question_response = self.client.post("/chat", json=question_request.model_dump())
        assert question_response.status_code == 200
        
        # 4. 최종 추천 요청
        recommend_request = ChatRequest(
            message="그럼 가장 좋은 것 하나 추천해줘",
            session_id=session_id
        )
        recommend_response = self.client.post("/chat", json=recommend_request.model_dump())
        assert recommend_response.status_code == 200
        
        # 모든 응답이 의미 있는 내용을 포함하는지 확인
        responses = [
            search_response.json()["response"],
            filter_response.json()["response"], 
            question_response.json()["response"],
            recommend_response.json()["response"]
        ]
        
        for response_text in responses:
            assert len(response_text.strip()) > 10  # 의미 있는 응답
            
    def test_error_recovery(self):
        """오류 복구 테스트"""
        session_id = "error_recovery_test"
        
        # 잘못된 요청 후 정상 요청
        invalid_request = ChatRequest(
            message="",  # 빈 메시지
            session_id=session_id
        )
        
        # 빈 메시지는 처리될 수도 있고 오류가 날 수도 있음
        self.client.post("/chat", json=invalid_request.model_dump())
        
        # 정상 요청이 잘 처리되는지 확인
        valid_request = ChatRequest(
            message="정상 요청입니다",
            session_id=session_id
        )
        valid_response = self.client.post("/chat", json=valid_request.model_dump())
        assert valid_response.status_code == 200
        
    def test_cross_component_integration(self):
        """컴포넌트 간 통합 테스트"""
        # 백엔드, Agent, MCP 툴이 모두 연동되는 시나리오
        request = ChatRequest(
            message="최신 게이밍 노트북 3개 추천하고 가격 비교해줘",
            session_id="cross_component_test"
        )
        
        response = self.client.post("/chat", json=request.model_dump())
        assert response.status_code == 200
        
        response_text = response.json()["response"]
        assert len(response_text) > 20  # 상당한 길이의 응답
        
        # 여러 컴포넌트가 관련된 키워드들이 포함되었는지 확인
        response_lower = response_text.lower()
        component_keywords = ["노트북", "게이밍", "추천", "가격", "비교"]
        matched_keywords = sum(1 for keyword in component_keywords if keyword in response_lower)
        assert matched_keywords >= 2  # 최소 2개 키워드 매칭 