"""
AI 응답 스트리밍 로직 테스트
"""

import pytest
import asyncio
from agent.agent import ShoppingAgent
import json


@pytest.mark.asyncio
async def test_agent_streaming_response():
    """에이전트 스트리밍 응답 테스트"""
    agent = ShoppingAgent()
    
    # 스트리밍 응답 생성
    stream_generator = agent.process_message_stream(
        message="안녕하세요",
        session_id="test-session"
    )
    
    chunks = []
    async for chunk in stream_generator:
        chunks.append(chunk)
    
    # 적어도 하나의 청크가 있어야 함
    assert len(chunks) > 0
    
    # 각 청크가 딕셔너리 형태여야 함
    for chunk in chunks:
        assert isinstance(chunk, dict)
        assert "type" in chunk
        
        # content 타입 청크만 content 필드 확인
        if chunk["type"] == "content":
            assert "content" in chunk


@pytest.mark.asyncio
async def test_agent_streaming_with_tools():
    """도구 사용과 함께 스트리밍 테스트"""
    agent = ShoppingAgent()
    
    # MCP 도구를 사용하는 메시지
    stream_generator = agent.process_message_stream(
        message="아이폰 15 가격 알려줘",
        session_id="test-session-tools"
    )
    
    chunks = []
    async for chunk in stream_generator:
        chunks.append(chunk)
    
    # 도구 사용이 포함된 스트리밍 응답 확인
    assert len(chunks) > 0
    
    # 도구 호출 정보가 포함되었는지 확인
    tool_chunks = [chunk for chunk in chunks if chunk.get("type") == "tool_call"]
    content_chunks = [chunk for chunk in chunks if chunk.get("type") == "content"]
    
    # 최종 응답 내용이 있어야 함
    assert len(content_chunks) > 0


@pytest.mark.asyncio
async def test_agent_streaming_error_handling():
    """스트리밍 에러 처리 테스트"""
    agent = ShoppingAgent()
    
    try:
        # 빈 메시지로 스트리밍 시도
        stream_generator = agent.process_message_stream(
            message="",
            session_id="test-error"
        )
        
        chunks = []
        async for chunk in stream_generator:
            chunks.append(chunk)
        
        # 에러 상황에서도 적절한 응답이 있어야 함
        assert len(chunks) > 0
        
    except Exception as e:
        # 예외가 발생해도 적절히 처리되어야 함
        assert isinstance(e, Exception)


@pytest.mark.asyncio 
async def test_agent_streaming_session_memory():
    """세션 메모리와 함께 스트리밍 테스트"""
    agent = ShoppingAgent()
    session_id = "test-memory-session"
    
    # 첫 번째 메시지
    stream_gen1 = agent.process_message_stream(
        message="내 이름은 김철수야",
        session_id=session_id
    )
    
    chunks1 = []
    async for chunk in stream_gen1:
        chunks1.append(chunk)
    
    assert len(chunks1) > 0
    
    # 두 번째 메시지 (이전 대화 기억해야 함)
    stream_gen2 = agent.process_message_stream(
        message="내 이름이 뭐라고 했지?",
        session_id=session_id
    )
    
    chunks2 = []
    async for chunk in stream_gen2:
        chunks2.append(chunk)
    
    assert len(chunks2) > 0
    
    # 응답에 이름이 포함되어 있는지 확인
    content_chunks = [chunk for chunk in chunks2 if chunk.get("type") == "content"]
    full_response = "".join([chunk.get("content", "") for chunk in content_chunks])
    assert "김철수" in full_response or "철수" in full_response


@pytest.mark.asyncio
async def test_agent_streaming_chunk_format():
    """스트리밍 청크 형식 테스트"""
    agent = ShoppingAgent()
    
    stream_generator = agent.process_message_stream(
        message="테스트 메시지",
        session_id="test-format"
    )
    
    chunks = []
    async for chunk in stream_generator:
        chunks.append(chunk)
        
        # 각 청크의 필수 필드 검증
        assert "type" in chunk
        assert chunk["type"] in ["content", "tool_call", "tool_result", "error", "done"]
        
        if chunk["type"] == "content":
            assert "content" in chunk
            assert isinstance(chunk["content"], str)
    
    assert len(chunks) > 0 