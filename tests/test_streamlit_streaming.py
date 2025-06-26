"""
Streamlit 스트리밍 UI 테스트
"""

import pytest
from unittest.mock import Mock, patch
import streamlit as st
from frontend.streamlit_streaming import StreamlitStreamingUI


def test_streamlit_streaming_ui_initialization():
    """스트리밍 UI 초기화 테스트"""
    ui = StreamlitStreamingUI()
    
    assert ui.current_response == ""
    assert ui.is_streaming == False
    assert ui.session_id is not None


def test_streamlit_streaming_ui_start_stream():
    """스트리밍 시작 테스트"""
    ui = StreamlitStreamingUI()
    
    ui.start_streaming("안녕하세요")
    
    assert ui.is_streaming == True
    assert ui.current_message == "안녕하세요"


def test_streamlit_streaming_ui_stop_stream():
    """스트리밍 중지 테스트"""
    ui = StreamlitStreamingUI()
    ui.is_streaming = True
    
    ui.stop_streaming()
    
    assert ui.is_streaming == False


def test_streamlit_streaming_ui_chunk_processing():
    """청크 처리 테스트"""
    ui = StreamlitStreamingUI()
    
    # 콘텐츠 청크 처리
    ui.process_chunk({"type": "content", "content": "안녕하세요 "})
    assert "안녕하세요 " in ui.current_response
    
    # 추가 청크 처리
    ui.process_chunk({"type": "content", "content": "반갑습니다 "})
    assert "안녕하세요 반갑습니다 " in ui.current_response


def test_streamlit_streaming_ui_tool_chunk():
    """도구 호출 청크 처리 테스트"""
    ui = StreamlitStreamingUI()
    
    tool_chunk = {
        "type": "tool_call",
        "tool_name": "search_naver",
        "tool_args": {"query": "아이폰"}
    }
    
    ui.process_chunk(tool_chunk)
    
    # 도구 호출 정보가 저장되어야 함
    assert len(ui.tool_calls) > 0
    assert ui.tool_calls[0]["tool_name"] == "search_naver"


def test_streamlit_streaming_ui_error_chunk():
    """에러 청크 처리 테스트"""
    ui = StreamlitStreamingUI()
    
    error_chunk = {
        "type": "error",
        "error": "연결 오류"
    }
    
    ui.process_chunk(error_chunk)
    
    assert ui.has_error == True
    assert "연결 오류" in ui.error_message


def test_streamlit_streaming_ui_display_message():
    """메시지 표시 테스트"""
    ui = StreamlitStreamingUI()
    
    with patch('streamlit.empty') as mock_empty:
        mock_container = Mock()
        mock_empty.return_value = mock_container
        
        ui.display_streaming_message("테스트 메시지")
        
        assert mock_empty.called
        assert mock_container.markdown.called


def test_streamlit_streaming_ui_display_tool_status():
    """도구 상태 표시 테스트"""
    ui = StreamlitStreamingUI()
    
    with patch('streamlit.status') as mock_status:
        mock_status_context = Mock()
        mock_status.return_value.__enter__ = Mock(return_value=mock_status_context)
        mock_status.return_value.__exit__ = Mock(return_value=None)
        
        ui.display_tool_status("search_naver", "검색 중...")
        
        assert mock_status.called


def test_streamlit_streaming_ui_typing_indicator():
    """타이핑 인디케이터 테스트"""
    ui = StreamlitStreamingUI()
    
    with patch('streamlit.empty') as mock_empty:
        mock_container = Mock()
        mock_empty.return_value = mock_container
        
        ui.show_typing_indicator()
        
        assert mock_empty.called
        assert ui.typing_container is not None


def test_streamlit_streaming_ui_clear_display():
    """화면 클리어 테스트"""
    ui = StreamlitStreamingUI()
    ui.current_response = "기존 응답"
    ui.tool_calls = [{"tool_name": "test"}]
    ui.has_error = True
    
    ui.clear_display()
    
    assert ui.current_response == ""
    assert len(ui.tool_calls) == 0
    assert ui.has_error == False


def test_streamlit_streaming_ui_get_full_response():
    """전체 응답 조회 테스트"""
    ui = StreamlitStreamingUI()
    ui.current_response = "완전한 응답 메시지"
    
    response = ui.get_full_response()
    
    assert response == "완전한 응답 메시지"


def test_streamlit_streaming_ui_session_management():
    """세션 관리 테스트"""
    ui = StreamlitStreamingUI()
    original_session = ui.session_id
    
    ui.new_session()
    
    assert ui.session_id != original_session
    assert ui.current_response == ""
    assert ui.is_streaming == False 