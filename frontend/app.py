"""
Streamlit 프론트엔드 애플리케이션 - 실시간 스트리밍 지원
"""

import streamlit as st
import requests
import sys
import os
import asyncio
import json
from typing import Dict, Any
import time

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import settings
from frontend.streamlit_streaming import StreamlitStreamingUI


def init_session_state():
    """세션 상태 초기화"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    if "user_id" not in st.session_state:
        import uuid
        st.session_state.user_id = str(uuid.uuid4())
    if "streaming_ui" not in st.session_state:
        st.session_state.streaming_ui = StreamlitStreamingUI()
    if "use_streaming" not in st.session_state:
        st.session_state.use_streaming = True


def display_message(message: Dict[str, Any]):
    """메시지 표시"""
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # 상품 정보가 있는 경우 표시
        if "products" in message and message["products"]:
            display_products(message["products"])


def display_products(products: list):
    """상품 정보 표시"""
    st.subheader("🛍️ 검색 결과")
    
    for i, product in enumerate(products):
        with st.expander(f"상품 {i+1}: {product.get('name', '상품명 없음')}"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if product.get("image_url"):
                    st.image(product["image_url"], width=150)
            
            with col2:
                st.write(f"**가격:** {product.get('price', 0):,}원")
                if product.get("original_price"):
                    st.write(f"~~원가: {product['original_price']:,}원~~")
                if product.get("discount_rate"):
                    st.write(f"**할인율:** {product['discount_rate']}%")
                st.write(f"**판매자:** {product.get('seller', '정보 없음')}")
                st.write(f"**평점:** {product.get('rating', 0)}⭐ ({product.get('review_count', 0)}개 리뷰)")
                st.write(f"**배송:** {product.get('shipping_info', '정보 없음')}")
                if product.get("product_url"):
                    st.link_button("상품 보기", product["product_url"])


def send_message_stream(message: str) -> requests.Response:
    """스트리밍 방식으로 메시지 전송"""
    try:
        backend_url = f"http://{settings.backend_host}:{settings.backend_port}"
        response = requests.post(
            f"{backend_url}/chat/stream",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id
            },
            stream=True,
            headers={
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            },
            timeout=30
        )
        response.raise_for_status()
        return response
    except Exception as e:
        raise ConnectionError(f"스트리밍 연결 실패: {e}")


def process_streaming_response(response: requests.Response) -> str:
    """스트리밍 응답 처리"""
    streaming_ui = st.session_state.streaming_ui
    streaming_ui.start_streaming(response.url)
    
    # 스트리밍 메시지 표시용 컨테이너
    response_container = st.empty()
    full_response = ""
    
    try:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data = line[6:]  # 'data: ' 제거
                
                if data == '[DONE]':
                    break
                
                try:
                    chunk = json.loads(data)
                    
                    # 백엔드에서 오는 청크 형식에 맞게 처리
                    if chunk.get("type") == "content" and "content" in chunk:
                        content = chunk.get("content", "")
                        full_response += content
                        
                        # 실시간으로 응답 업데이트
                        display_text = full_response + "▋"  # 커서 효과
                        response_container.markdown(f"🤖 **AI 응답:**\n\n{display_text}")
                    
                    elif chunk.get("type") == "tool_call":
                        tool_name = chunk.get("tool_name", "Unknown")
                        with st.status(f"🔧 {tool_name} 실행 중...", expanded=False):
                            st.write("도구를 실행하고 있습니다...")
                    
                    elif chunk.get("type") == "error":
                        error_msg = chunk.get("error", "알 수 없는 오류")
                        st.error(f"❌ 오류 발생: {error_msg}")
                    
                    elif chunk.get("type") == "done":
                        # 스트리밍 완료
                        break
                
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 텍스트로 처리
                    full_response += data
                    response_container.markdown(f"🤖 **AI 응답:**\n\n{full_response}▋")
    
    except Exception as e:
        st.error(f"스트리밍 처리 오류: {e}")
    
    finally:
        # 스트리밍 완료 시 커서 제거
        response_container.markdown(f"🤖 **AI 응답:**\n\n{full_response}")
        streaming_ui.stop_streaming()
    
    return full_response


def send_message(message: str) -> Dict[str, Any]:
    """일반 방식으로 메시지 전송 (fallback)"""
    try:
        backend_url = f"http://{settings.backend_host}:{settings.backend_port}"
        response = requests.post(
            f"{backend_url}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "response": f"오류가 발생했습니다: {str(e)}",
            "products": []
        }


def get_conversation_history() -> list:
    """대화 히스토리 조회"""
    try:
        backend_url = f"http://{settings.backend_host}:{settings.backend_port}"
        response = requests.get(
            f"{backend_url}/history/{st.session_state.session_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("history", [])
    except Exception:
        return []


def clear_session():
    """세션 초기화"""
    try:
        backend_url = f"http://{settings.backend_host}:{settings.backend_port}"
        response = requests.delete(
            f"{backend_url}/session/{st.session_state.session_id}",
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception:
        return False


def main():
    """메인 애플리케이션"""
    st.set_page_config(
        page_title="🛍️ 실시간 스트리밍 쇼핑 챗봇",
        page_icon="🛍️",
        layout="wide"
    )
    
    st.title("🛍️ 실시간 스트리밍 쇼핑 챗봇")
    st.markdown("**⚡ 실시간 스트리밍으로 빠른 응답을 제공하는 지능형 쇼핑 챗봇입니다!**")
    
    # 세션 상태 초기화
    init_session_state()
    
    # 사이드바
    with st.sidebar:
        st.header("ℹ️ 세션 정보")
        st.write(f"🆔 세션: {st.session_state.session_id[:8]}...")
        st.write(f"👤 사용자: {st.session_state.user_id[:8]}...")
        st.write(f"💬 메시지 수: {len(st.session_state.messages)}")
        
        st.divider()
        
        # 스트리밍 옵션
        st.header("⚙️ 설정")
        st.session_state.use_streaming = st.toggle(
            "🔄 실시간 스트리밍 사용", 
            value=st.session_state.use_streaming,
            help="실시간으로 AI 응답을 받아볼 수 있습니다"
        )
        
        st.divider()
        
        # 대화 히스토리 로드
        if st.button("🔄 히스토리 새로고침"):
            history = get_conversation_history()
            if history:
                st.session_state.messages = []
                for msg in history:
                    st.session_state.messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            st.rerun()
        
        # 대화 초기화
        if st.button("🗑️ 대화 초기화"):
            if clear_session():
                st.session_state.messages = []
                st.session_state.streaming_ui.new_session()
                st.success("대화가 초기화되었습니다!")
            else:
                st.error("초기화 중 오류가 발생했습니다.")
            st.rerun()
    
    # 메시지 히스토리 표시
    for message in st.session_state.messages:
        display_message(message)
    
    # 사용자 입력
    if prompt := st.chat_input("상품을 검색해보세요! (예: 무선 이어폰, 게임용 노트북)"):
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.write(prompt)
        
        # 챗봇 응답 처리
        with st.chat_message("assistant"):
            if st.session_state.use_streaming:
                # 스트리밍 방식
                try:
                    streaming_response = send_message_stream(prompt)
                    ai_response = process_streaming_response(streaming_response)
                except Exception as e:
                    st.error(f"스트리밍 오류: {e}")
                    # fallback to normal mode
                    with st.spinner("일반 모드로 처리 중..."):
                        response = send_message(prompt)
                        ai_response = response["response"]
                        st.write(ai_response)
                        if response.get("products"):
                            display_products(response["products"])
            else:
                # 일반 방식
                with st.spinner("AI가 생각하고 있습니다..."):
                    response = send_message(prompt)
                    ai_response = response["response"]
                
                st.write(ai_response)
                
                # 상품 정보 표시
                if response.get("products"):
                    display_products(response["products"])
        
        # 챗봇 메시지 추가
        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_response if 'ai_response' in locals() else "응답 처리 중 오류가 발생했습니다.",
            "products": response.get("products", []) if 'response' in locals() else []
        })


if __name__ == "__main__":
    main() 