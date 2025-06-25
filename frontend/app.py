"""
Streamlit 프론트엔드 애플리케이션
"""

import streamlit as st
import requests
from typing import Dict, Any
from config import settings


def init_session_state():
    """세션 상태 초기화"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())


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


def send_message(message: str) -> Dict[str, Any]:
    """백엔드로 메시지 전송"""
    try:
        backend_url = f"http://{settings.backend_host}:{settings.backend_port}"
        response = requests.post(
            f"{backend_url}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id
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


def main():
    """메인 애플리케이션"""
    st.set_page_config(
        page_title="🛍️ 쇼핑 챗봇",
        page_icon="🛍️",
        layout="wide"
    )
    
    st.title("🛍️ 쇼핑 챗봇")
    st.markdown("상품을 검색하고 비교해보세요!")
    
    # 세션 상태 초기화
    init_session_state()
    
    # 사이드바
    with st.sidebar:
        st.header("ℹ️ 정보")
        st.write(f"세션 ID: {st.session_state.session_id[:8]}...")
        st.write(f"메시지 수: {len(st.session_state.messages)}")
        
        if st.button("대화 초기화"):
            st.session_state.messages = []
            st.rerun()
    
    # 메시지 히스토리 표시
    for message in st.session_state.messages:
        display_message(message)
    
    # 사용자 입력
    if prompt := st.chat_input("상품을 검색해보세요! (예: 무선 이어폰)"):
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
            with st.spinner("검색 중..."):
                response = send_message(prompt)
            
            st.write(response["response"])
            
            # 상품 정보 표시
            if response.get("products"):
                display_products(response["products"])
        
        # 챗봇 메시지 추가
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["response"],
            "products": response.get("products", [])
        })


if __name__ == "__main__":
    main() 