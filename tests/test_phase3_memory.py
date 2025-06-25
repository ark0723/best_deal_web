"""
Phase 3: 사용자 메모리 및 선호도 학습 테스트
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from agent.agent import ShoppingAgent


class TestPhase3Memory:
    """Phase 3: 사용자 메모리 및 선호도 학습 테스트 클래스"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 ShoppingAgent 인스턴스"""
        return ShoppingAgent()
    
    @pytest.fixture
    def test_user_id(self):
        """테스트용 사용자 ID"""
        return "test_user_003"
    
    def test_save_user_memory(self, agent, test_user_id):
        """3.1 사용자 메모리 저장 테스트"""
        # 메모리 저장
        agent._save_user_memory(test_user_id, "가격 중시형 사용자", "preference")
        
        # 저장된 메모리 조회
        memories = agent._get_user_memories(test_user_id)
        
        # 검증
        assert len(memories) > 0
        assert any(memory.get("content") == "가격 중시형 사용자" for memory in memories)
    
    def test_get_user_memories_empty(self, agent):
        """3.2 존재하지 않는 사용자 메모리 조회 테스트"""
        memories = agent._get_user_memories("nonexistent_user")
        assert len(memories) == 0
    
    def test_learn_price_preference(self, agent, test_user_id):
        """3.3 가격 선호도 학습 테스트"""
        messages = [
            HumanMessage(content="저렴한 노트북 찾고 있어요"),
            HumanMessage(content="할인 상품 있나요?")
        ]
        
        agent._learn_user_preferences(test_user_id, messages)
        
        # 저장된 선호도 확인
        memories = agent._get_user_memories(test_user_id)
        price_preferences = [m for m in memories if "가격 중시형" in str(m.get("content", ""))]
        assert len(price_preferences) > 0
    
    def test_learn_brand_preference(self, agent, test_user_id):
        """3.4 브랜드 선호도 학습 테스트"""
        messages = [
            HumanMessage(content="삼성 갤럭시 스마트폰 어때요?"),
            HumanMessage(content="애플 제품도 고려해볼게요")
        ]
        
        agent._learn_user_preferences(test_user_id, messages)
        
        # 저장된 브랜드 선호도 확인
        memories = agent._get_user_memories(test_user_id)
        brand_preferences = [m for m in memories if any(brand in str(m.get("content", "")) for brand in ["삼성", "애플"])]
        assert len(brand_preferences) > 0
    
    def test_build_system_context_with_memories(self, agent, test_user_id):
        """3.5 메모리 기반 시스템 컨텍스트 구성 테스트"""
        # 테스트 메모리 저장
        agent._save_user_memory(test_user_id, "가격 중시형 사용자", "preference")
        agent._save_user_memory(test_user_id, "삼성 선호", "preference")
        
        # 상태 구성
        from agent.agent import CustomMessagesState
        state = CustomMessagesState(
            messages=[],
            user_id=test_user_id,
            session_preferences={"budget": "50만원 이하"},
            search_history=[]
        )
        
        # 메모리 조회 및 컨텍스트 구성
        memories = agent._get_user_memories(test_user_id)
        context = agent._build_system_context(memories, state)
        
        # 검증: 사용자 선호도가 포함되어야 함
        assert "사용자 선호도" in context or "가격 중시형" in context or "삼성" in context
        assert "현재 세션 정보" in context or "budget" in context 