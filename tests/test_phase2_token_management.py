"""
Phase 2: 메시지 트리밍 및 토큰 관리 테스트
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from agent.agent import ShoppingAgent


class TestPhase2TokenManagement:
    """Phase 2: 메시지 트리밍 및 토큰 관리 테스트 클래스"""
    
    @pytest.fixture
    def agent(self):
        """테스트용 ShoppingAgent 인스턴스"""
        return ShoppingAgent()
    
    def test_trim_messages_basic(self, agent):
        """2.1 기본 메시지 트리밍 기능 테스트"""
        # 긴 메시지 리스트 생성
        messages = []
        for i in range(20):
            messages.append(HumanMessage(content=f"긴 메시지 {i} " * 100))  # 긴 메시지
            messages.append(AIMessage(content=f"응답 메시지 {i} " * 100))
        
        # 트리밍 실행
        trimmed = agent._trim_messages(messages, max_tokens=1000)
        
        # 검증: 원본보다 짧아야 함
        assert len(trimmed) < len(messages)
        # 검증: 최근 메시지들이 유지되어야 함
        assert trimmed[-1].content == messages[-1].content
    
    def test_trim_messages_empty_list(self, agent):
        """2.2 빈 메시지 리스트 트리밍 테스트"""
        messages = []
        trimmed = agent._trim_messages(messages)
        assert trimmed == []
    
    def test_count_tokens_basic(self, agent):
        """2.3 토큰 카운팅 기능 테스트"""
        messages = [
            HumanMessage(content="안녕하세요"),
            AIMessage(content="반갑습니다")
        ]
        
        token_count = agent._count_tokens(messages)
        assert token_count > 0
        assert isinstance(token_count, int)
    
    def test_trim_messages_fallback(self, agent):
        """2.4 트리밍 실패 시 폴백 로직 테스트"""
        # 많은 메시지로 폴백 로직 유발
        messages = []
        for i in range(50):
            messages.append(HumanMessage(content=f"메시지 {i}"))
        
        trimmed = agent._trim_messages(messages, max_tokens=100)
        
        # 폴백으로 최근 10개 이하여야 함
        assert len(trimmed) <= 10
        # 최근 메시지들이 유지되어야 함
        assert trimmed[-1].content == messages[-1].content
    
    def test_token_limit_respected(self, agent):
        """2.5 토큰 제한 준수 테스트"""
        # 매우 긴 메시지들 생성
        messages = []
        for i in range(10):
            long_content = "매우 긴 메시지 내용입니다. " * 200  # 약 2000자
            messages.append(HumanMessage(content=long_content))
        
        max_tokens = 500
        trimmed = agent._trim_messages(messages, max_tokens=max_tokens)
        
        # 트리밍된 메시지의 토큰 수가 제한보다 작거나 같아야 함
        actual_tokens = agent._count_tokens(trimmed)
        assert actual_tokens <= max_tokens * 1.2  # 약간의 오차 허용 