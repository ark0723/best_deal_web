"""
Phase 4: 세션 기반 대화 처리 테스트
"""

import pytest
import asyncio
from agent.agent import ShoppingAgent


class TestPhase4Session:
    """Phase 4: 세션 기반 대화 처리 테스트 클래스"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 ShoppingAgent 인스턴스"""
        return ShoppingAgent()
    
    @pytest.fixture
    def test_session_id(self):
        """테스트용 세션 ID"""
        return "test_session_004"
    
    @pytest.fixture
    def test_user_id(self):
        """테스트용 사용자 ID"""
        return "test_user_004"
    
    @pytest.mark.asyncio
    async def test_process_message_basic(self, agent, test_session_id, test_user_id):
        """4.1 기본 메시지 처리 테스트"""
        message = "안녕하세요, 노트북 추천해주세요"
        
        response = await agent.process_message(message, test_session_id, test_user_id)
        
        # 검증: 응답이 문자열이어야 함
        assert isinstance(response, str)
        assert len(response) > 0
        # 에러 메시지가 아니어야 함
        assert not response.startswith("죄송합니다. 처리 중 오류가")
    
    @pytest.mark.asyncio
    async def test_conversation_history_persistence(self, agent, test_session_id, test_user_id):
        """4.2 대화 히스토리 유지 테스트"""
        # 첫 번째 메시지
        message1 = "저는 게임용 노트북을 찾고 있어요"
        await agent.process_message(message1, test_session_id, test_user_id)
        
        # 두 번째 메시지
        message2 = "예산은 150만원 정도입니다"
        await agent.process_message(message2, test_session_id, test_user_id)
        
        # 대화 히스토리 조회
        history = agent.get_conversation_history(test_session_id)
        
        # 검증: 두 메시지가 모두 히스토리에 있어야 함
        assert len(history) >= 2
        user_messages = [h for h in history if h.get("role") == "user"]
        assert len(user_messages) >= 2
        
        # 메시지 내용 확인
        user_contents = [h.get("content") for h in user_messages]
        assert any("게임용 노트북" in content for content in user_contents)
        assert any("150만원" in content for content in user_contents)
    
    def test_get_conversation_history_empty(self, agent):
        """4.3 빈 세션 히스토리 조회 테스트"""
        history = agent.get_conversation_history("empty_session")
        assert len(history) == 0
    
    def test_clear_session(self, agent, test_session_id):
        """4.4 세션 초기화 테스트"""
        # 세션에 메시지 추가 (실제로는 process_message를 통해)
        # 여기서는 clear_session 기능만 테스트
        result = agent.clear_session(test_session_id)
        
        # 검증: 성공 여부 반환
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_isolation(self, agent, test_user_id):
        """4.5 다중 세션 격리 테스트"""
        session1 = "session_001"
        session2 = "session_002"
        
        # 세션 1에 메시지
        await agent.process_message("세션1에서 스마트폰 찾아요", session1, test_user_id)
        
        # 세션 2에 메시지
        await agent.process_message("세션2에서 태블릿 찾아요", session2, test_user_id)
        
        # 각 세션의 히스토리 조회
        history1 = agent.get_conversation_history(session1)
        history2 = agent.get_conversation_history(session2)
        
        # 검증: 세션이 격리되어야 함
        user1_contents = [h.get("content") for h in history1 if h.get("role") == "user"]
        user2_contents = [h.get("content") for h in history2 if h.get("role") == "user"]
        
        assert any("스마트폰" in content for content in user1_contents)
        assert any("태블릿" in content for content in user2_contents)
        
        # 세션 간 내용이 섞이지 않았는지 확인
        assert not any("태블릿" in content for content in user1_contents)
        assert not any("스마트폰" in content for content in user2_contents) 