"""
Streamlit 기반 스트리밍 UI
"""

import streamlit as st
import uuid
import time
from typing import Dict, Any, List, Optional


class StreamlitStreamingUI:
    """Streamlit 기반 실시간 스트리밍 UI"""
    
    def __init__(self):
        """UI 초기화"""
        self.session_id = str(uuid.uuid4())
        self.current_response = ""
        self.current_message = ""
        self.is_streaming = False
        self.tool_calls = []
        self.has_error = False
        self.error_message = ""
        
        # UI 컨테이너
        self.response_container = None
        self.typing_container = None
        self.status_container = None
    
    def start_streaming(self, message: str):
        """스트리밍 시작"""
        self.current_message = message
        self.is_streaming = True
        self.current_response = ""
        self.tool_calls = []
        self.has_error = False
        self.error_message = ""
        
        # 타이핑 인디케이터 표시
        self.show_typing_indicator()
    
    def stop_streaming(self):
        """스트리밍 중지"""
        self.is_streaming = False
        
        # 타이핑 인디케이터 제거
        if self.typing_container:
            self.typing_container.empty()
    
    def process_chunk(self, chunk: Dict[str, Any]):
        """청크 처리"""
        chunk_type = chunk.get("type", "")
        
        if chunk_type == "content":
            # 콘텐츠 청크 처리
            content = chunk.get("content", "")
            self.current_response += content
            self.display_streaming_message(self.current_response)
        
        elif chunk_type == "tool_call":
            # 도구 호출 청크 처리
            self.tool_calls.append(chunk)
            tool_name = chunk.get("tool_name", "Unknown")
            self.display_tool_status(tool_name, "실행 중...")
        
        elif chunk_type == "tool_result":
            # 도구 결과 청크 처리
            tool_name = chunk.get("tool_name", "Unknown")
            self.display_tool_status(tool_name, "완료")
        
        elif chunk_type == "error":
            # 에러 청크 처리
            self.has_error = True
            self.error_message = chunk.get("error", "알 수 없는 오류")
            self.display_error(self.error_message)
        
        elif chunk_type == "done":
            # 완료 신호
            self.stop_streaming()
    
    def display_streaming_message(self, message: str):
        """스트리밍 메시지 표시"""
        if not self.response_container:
            self.response_container = st.empty()
        
        # 마크다운으로 메시지 표시 (커서 효과 추가)
        display_text = message
        if self.is_streaming:
            display_text += "▋"  # 커서 효과
        
        self.response_container.markdown(f"🤖 **AI 응답:**\n\n{display_text}")
    
    def display_tool_status(self, tool_name: str, status: str):
        """도구 상태 표시"""
        tool_display_names = {
            "search_naver": "네이버 검색",
            "search_exa": "웹 검색",
            "get_weather": "날씨 조회"
        }
        
        display_name = tool_display_names.get(tool_name, tool_name)
        
        with st.status(f"🔧 {display_name} - {status}", expanded=False):
            st.write(f"도구: {display_name}")
            st.write(f"상태: {status}")
            if status == "완료":
                st.success("처리 완료!")
    
    def display_error(self, error_message: str):
        """에러 메시지 표시"""
        st.error(f"❌ 오류 발생: {error_message}")
    
    def show_typing_indicator(self):
        """타이핑 인디케이터 표시"""
        if not self.typing_container:
            self.typing_container = st.empty()
        
        self.typing_container.markdown("🤖 **AI가 응답을 작성 중입니다...** ⏳")
    
    def clear_display(self):
        """화면 클리어"""
        self.current_response = ""
        self.tool_calls = []
        self.has_error = False
        self.error_message = ""
        
        if self.response_container:
            self.response_container.empty()
            self.response_container = None
        
        if self.typing_container:
            self.typing_container.empty()
            self.typing_container = None
    
    def get_full_response(self) -> str:
        """전체 응답 반환"""
        return self.current_response
    
    def new_session(self):
        """새 세션 시작"""
        self.session_id = str(uuid.uuid4())
        self.current_response = ""
        self.current_message = ""
        self.is_streaming = False
        self.tool_calls = []
        self.has_error = False
        self.error_message = ""
        self.clear_display()
    
    def render_chat_interface(self):
        """채팅 인터페이스 렌더링"""
        st.title("🛒 쇼핑 챗봇")
        st.caption("실시간 스트리밍으로 빠른 응답을 제공합니다")
        
        # 세션 관리
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 새 대화"):
                self.new_session()
                st.rerun()
        
        # 채팅 히스토리 (세션 상태 활용)
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # 히스토리 표시
        for i, (user_msg, ai_msg) in enumerate(st.session_state.chat_history):
            with st.chat_message("user"):
                st.write(user_msg)
            with st.chat_message("assistant"):
                st.write(ai_msg)
        
        # 현재 스트리밍 중인 메시지 표시
        if self.is_streaming and self.current_message:
            with st.chat_message("user"):
                st.write(self.current_message)
            
            with st.chat_message("assistant"):
                # 여기서 실시간 스트리밍 내용이 업데이트됨
                pass
    
    def add_to_history(self, user_message: str, ai_response: str):
        """채팅 히스토리에 추가"""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        st.session_state.chat_history.append((user_message, ai_response))
    
    def get_streaming_placeholder(self):
        """스트리밍용 플레이스홀더 반환"""
        return st.empty() 