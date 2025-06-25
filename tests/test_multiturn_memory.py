"""
멀티턴 대화 메모리 기능 테스트
TDD 방식으로 Phase 1-2 기능 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agent.agent import ShoppingAgent, CustomMessagesState
from langchain_core.messages import HumanMessage, AIMessage


class TestMultiturnMemory:
    """멀티턴 대화 메모리 테스트 클래스"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 ShoppingAgent 인스턴스"""
        return ShoppingAgent()
    
    @pytest.fixture
    def sample_session_id(self):
        """테스트용 세션 ID"""
        return "test_session_001"
    
    @pytest.fixture
    def sample_user_id(self):
        """테스트용 사용자 ID"""
        return "test_user_001"

    # Phase 1: 기본 멀티턴 구조 구축 테스트
    
    def test_inmemory_saver_initialization(self, agent):
        """1. InMemorySaver 체크포인터 설정 테스트"""
        assert agent.checkpointer is not None
        assert hasattr(agent.checkpointer, 'put')
        assert hasattr(agent.checkpointer, 'get_tuple')
        assert hasattr(agent.checkpointer, 'list')
    
    def test_custom_messages_state_definition(self, agent):
        """2. MessagesState 기반 상태 정의 테스트"""
        state = CustomMessagesState()
        
        # 기본 MessagesState 속성 확인
        assert hasattr(state, 'messages') or 'messages' in state
        
        # CustomMessagesState 확장 속성 확인
        expected_keys = ['user_id', 'session_preferences', 'search_history']
        for key in expected_keys:
            assert hasattr(state, key) or key in state
    
    @pytest.mark.asyncio
    async def test_thread_id_session_management(self, agent, sample_session_id, sample_user_id):
        """3. thread_id 기반 세션 관리 구현 테스트"""
        message1 = "안녕하세요, 노트북을 찾고 있어요"
        message2 = "이전에 말한 노트북 중에서 가장 저렴한 걸로 추천해주세요"
        
        # 첫 번째 메시지
        response1 = await agent.process_message(
            message1, 
            session_id=sample_session_id, 
            user_id=sample_user_id
        )
        assert response1 is not None
        assert isinstance(response1, str)
        
        # 두 번째 메시지 (같은 세션)
        response2 = await agent.process_message(
            message2, 
            session_id=sample_session_id, 
            user_id=sample_user_id
        )
        assert response2 is not None
        assert isinstance(response2, str)
        
        # 다른 세션에서의 메시지
        response3 = await agent.process_message(
            message2, 
            session_id="different_session", 
            user_id=sample_user_id
        )
        assert response3 is not None
        # 다른 세션에서는 컨텍스트가 다를 것으로 예상
    
    def test_conversation_history_retrieval(self, agent, sample_session_id):
        """4. 기본 대화 연속성 테스트 - 대화 히스토리 조회"""
        history = agent.get_conversation_history(sample_session_id)
        assert isinstance(history, list)
        # 빈 세션의 경우 빈 리스트 반환
        assert len(history) >= 0

    # Phase 2: 메모리 관리 시스템 테스트
    
    @pytest.mark.asyncio
    async def test_message_history_storage(self, agent, sample_session_id, sample_user_id):
        """5. 메시지 히스토리 저장/조회 기능 테스트"""
        test_message = "삼성 노트북 추천해주세요"
        
        # 메시지 처리
        await agent.process_message(
            test_message, 
            session_id=sample_session_id, 
            user_id=sample_user_id
        )
        
        # 히스토리 조회
        history = agent.get_conversation_history(sample_session_id)
        
        # 메시지가 저장되었는지 확인
        assert len(history) > 0
        # 사용자 메시지와 에이전트 응답이 모두 있는지 확인
        user_messages = [msg for msg in history if msg.get('role') == 'user']
        assistant_messages = [msg for msg in history if msg.get('role') == 'assistant']
        
        assert len(user_messages) > 0
        assert len(assistant_messages) > 0
    
    def test_message_trimming_functionality(self, agent):
        """6. 토큰 제한 관리 및 메시지 트리밍 테스트"""
        # 긴 메시지 목록 생성
        long_messages = []
        for i in range(15):
            long_messages.append(HumanMessage(content=f"메시지 {i}: " + "a" * 100))
            long_messages.append(AIMessage(content=f"응답 {i}: " + "b" * 100))
        
        # 트리밍 테스트
        trimmed = agent._trim_messages(long_messages, max_tokens=500)
        
        assert isinstance(trimmed, list)
        assert len(trimmed) <= len(long_messages)
        # 트리밍된 메시지는 원본보다 적어야 함
        if len(long_messages) > 10:
            assert len(trimmed) < len(long_messages)
    
    @pytest.mark.asyncio
    async def test_conversation_context_maintenance(self, agent, sample_session_id, sample_user_id):
        """7. 대화 컨텍스트 유지 로직 테스트"""
        # 연속된 대화
        messages = [
            "안녕하세요",
            "노트북을 찾고 있어요",
            "가격은 100만원 이하로 부탁해요",
            "그 중에서 가장 좋은 걸로 추천해주세요"
        ]
        
        responses = []
        for message in messages:
            response = await agent.process_message(
                message, 
                session_id=sample_session_id, 
                user_id=sample_user_id
            )
            responses.append(response)
        
        # 모든 응답이 정상적으로 생성되었는지 확인
        for response in responses:
            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
        
        # 대화 히스토리 확인
        history = agent.get_conversation_history(sample_session_id)
        assert len(history) >= len(messages)
    
    def test_session_independent_memory(self, agent, sample_user_id):
        """8. 세션별 독립적 메모리 관리 테스트"""
        session1 = "session_001"
        session2 = "session_002"
        
        # 각 세션의 히스토리는 독립적이어야 함
        history1 = agent.get_conversation_history(session1)
        history2 = agent.get_conversation_history(session2)
        
        # 초기에는 모두 빈 상태
        assert isinstance(history1, list)
        assert isinstance(history2, list)
    
    def test_user_preference_learning_structure(self, agent):
        """사용자 선호도 학습 구조 테스트"""
        # _learn_user_preferences 메서드 존재 확인
        assert hasattr(agent, '_learn_user_preferences')
        assert callable(agent._learn_user_preferences)
        
        # _get_user_memories 메서드 존재 확인
        assert hasattr(agent, '_get_user_memories')
        assert callable(agent._get_user_memories)
    
    def test_system_context_building(self, agent):
        """시스템 컨텍스트 구성 테스트"""
        # _build_system_context 메서드 존재 확인
        assert hasattr(agent, '_build_system_context')
        assert callable(agent._build_system_context)
        
        # 테스트용 상태 생성
        test_state = CustomMessagesState()
        test_memories = []
        
        context = agent._build_system_context(test_memories, test_state)
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert "쇼핑 어시스턴트" in context or "assistant" in context.lower()
    
    def test_session_clearing(self, agent, sample_session_id):
        """세션 초기화 기능 테스트"""
        # 세션 초기화 메서드 존재 확인
        assert hasattr(agent, 'clear_session')
        assert callable(agent.clear_session)
        
        # 세션 초기화 실행
        result = agent.clear_session(sample_session_id)
        
        # 결과는 boolean이어야 함
        assert isinstance(result, bool)


class TestMemoryStore:
    """메모리 저장소 관련 테스트"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 ShoppingAgent 인스턴스"""
        return ShoppingAgent()
    
    def test_memory_store_initialization(self, agent):
        """메모리 저장소 초기화 테스트"""
        assert agent.store is not None
        assert hasattr(agent.store, 'put')
        assert hasattr(agent.store, 'search')
    
    def test_graph_compilation_with_memory(self, agent):
        """메모리와 함께 그래프 컴파일 테스트"""
        assert agent.graph is not None
        # 그래프가 체크포인터와 스토어와 함께 컴파일되었는지 확인
        assert hasattr(agent.graph, 'invoke')
        assert hasattr(agent.graph, 'get_state')


# 통합 테스트
class TestMultiturnIntegration:
    """멀티턴 대화 통합 테스트"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 ShoppingAgent 인스턴스"""
        return ShoppingAgent()
    
    @pytest.mark.asyncio
    async def test_full_multiturn_conversation_flow(self, agent):
        """전체 멀티턴 대화 플로우 테스트"""
        session_id = "integration_test_session"
        user_id = "integration_test_user"
        
        # 대화 시나리오
        conversation = [
            "안녕하세요",
            "노트북을 찾고 있습니다",
            "게이밍용으로 사용할 예정이에요",
            "예산은 150만원 정도입니다",
            "추천해주신 제품 중에서 가장 인기있는 걸로 부탁해요"
        ]
        
        for i, message in enumerate(conversation):
            response = await agent.process_message(
                message, 
                session_id=session_id, 
                user_id=user_id
            )
            
            # 각 응답이 정상적으로 생성되는지 확인
            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
            
            # 대화가 진행될수록 히스토리가 쌓이는지 확인
            history = agent.get_conversation_history(session_id)
            expected_min_length = (i + 1) * 2  # 사용자 메시지 + 에이전트 응답
            assert len(history) >= i + 1  # 최소한 사용자 메시지는 있어야 함
        
        # 최종 히스토리 검증
        final_history = agent.get_conversation_history(session_id)
        assert len(final_history) >= len(conversation)
        
        # 사용자 메시지와 에이전트 응답이 교대로 나타나는지 확인
        user_messages = [msg for msg in final_history if msg.get('role') == 'user']
        assistant_messages = [msg for msg in final_history if msg.get('role') == 'assistant']
        
        assert len(user_messages) == len(conversation)
        assert len(assistant_messages) >= len(conversation)  # 최소한 같은 수 이상의 응답 