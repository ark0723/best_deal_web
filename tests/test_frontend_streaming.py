"""
프론트엔드 스트리밍 클라이언트 테스트
"""

import pytest
import asyncio
import requests
from unittest.mock import Mock, patch
from frontend.streaming_client import StreamingChatClient


def test_streaming_client_initialization():
    """스트리밍 클라이언트 초기화 테스트"""
    client = StreamingChatClient("http://localhost:8000")
    
    assert client.base_url == "http://localhost:8000"
    assert client.session_id is not None
    assert client.is_connected == False


def test_streaming_client_url_construction():
    """스트리밍 URL 구성 테스트"""
    client = StreamingChatClient("http://localhost:8000")
    
    url = client._build_stream_url("안녕하세요", "test-session")
    
    assert "/chat/stream" in url
    assert "test-session" in url


@pytest.mark.asyncio
async def test_streaming_client_connection():
    """스트리밍 연결 테스트"""
    client = StreamingChatClient("http://localhost:8000")
    
    # Mock EventSource-like behavior
    with patch('frontend.streaming_client.StreamingChatClient._create_event_source') as mock_es:
        mock_es.return_value = Mock()
        
        await client.connect("테스트 메시지", "test-session")
        
        assert mock_es.called
        assert client.is_connected == True


@pytest.mark.asyncio
async def test_streaming_client_message_processing():
    """스트리밍 메시지 처리 테스트"""
    client = StreamingChatClient("http://localhost:8000")
    
    received_chunks = []
    
    def on_chunk(chunk):
        received_chunks.append(chunk)
    
    client.on_chunk = on_chunk
    
    # 가상의 SSE 데이터 시뮬레이션
    test_chunks = [
        {"type": "content", "content": "안녕하세요 "},
        {"type": "content", "content": "반갑습니다 "},
        {"type": "done", "session_id": "test-session"}
    ]
    
    for chunk in test_chunks:
        client._handle_message(chunk)
    
    assert len(received_chunks) == 3
    assert received_chunks[0]["type"] == "content"
    assert received_chunks[-1]["type"] == "done"


def test_streaming_client_error_handling():
    """스트리밍 클라이언트 오류 처리 테스트"""
    client = StreamingChatClient("http://localhost:8000")
    
    error_handled = []
    
    def on_error(error):
        error_handled.append(error)
    
    client.on_error = on_error
    
    # 오류 시뮬레이션
    client._handle_error("연결 오류")
    
    assert len(error_handled) == 1
    assert "연결 오류" in error_handled[0]


def test_streaming_client_disconnection():
    """스트리밍 연결 해제 테스트"""
    client = StreamingChatClient("http://localhost:8000")
    client.is_connected = True
    
    client.disconnect()
    
    assert client.is_connected == False


@pytest.mark.asyncio
async def test_streaming_client_reconnection():
    """스트리밍 재연결 테스트"""
    client = StreamingChatClient("http://localhost:8000", auto_reconnect=True)
    
    reconnection_attempts = []
    
    def on_reconnect():
        reconnection_attempts.append(True)
    
    client.on_reconnect = on_reconnect
    
    # 연결 실패 시뮬레이션
    with patch.object(client, '_attempt_reconnect') as mock_reconnect:
        mock_reconnect.return_value = True
        
        await client._handle_connection_error()
        
        assert mock_reconnect.called


def test_streaming_client_message_queue():
    """메시지 큐 처리 테스트"""
    client = StreamingChatClient("http://localhost:8000")
    
    # 메시지 큐에 추가
    client._add_to_queue("메시지 1")
    client._add_to_queue("메시지 2")
    
    assert len(client.message_queue) == 2
    
    # 큐에서 처리
    processed = client._process_queue()
    
    assert len(processed) == 2
    assert "메시지 1" in processed
    assert "메시지 2" in processed 