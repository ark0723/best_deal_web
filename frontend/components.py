"""
Streamlit 커스텀 컴포넌트
"""

import streamlit as st
from typing import List, Dict, Any


def product_card(product: Dict[str, Any], index: int = 0):
    """상품 카드 컴포넌트"""
    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd; 
            border-radius: 10px; 
            padding: 15px; 
            margin: 10px 0;
            background-color: #f9f9f9;
        ">
            <h4>{product.get('name', '상품명 없음')}</h4>
            <p><strong>가격:</strong> {product.get('price', 0):,}원</p>
            <p><strong>판매자:</strong> {product.get('seller', '정보 없음')}</p>
            <p><strong>평점:</strong> {product.get('rating', 0)}⭐</p>
        </div>
        """, unsafe_allow_html=True)


def search_filters():
    """검색 필터 컴포넌트"""
    with st.expander("🔍 검색 필터"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_price = st.number_input(
                "최대 가격", 
                min_value=0, 
                max_value=1000000, 
                value=100000,
                step=10000
            )
        
        with col2:
            min_rating = st.slider(
                "최소 평점", 
                min_value=0.0, 
                max_value=5.0, 
                value=3.0,
                step=0.1
            )
        
        with col3:
            category = st.selectbox(
                "카테고리",
                ["전체", "전자제품", "의류", "생활용품", "스포츠", "도서"]
            )
        
        return {
            "max_price": max_price if max_price > 0 else None,
            "min_rating": min_rating if min_rating > 0 else None,
            "category": category if category != "전체" else None
        }


def chat_history_sidebar(messages: List[Dict[str, Any]]):
    """채팅 히스토리 사이드바"""
    with st.sidebar:
        st.header("💬 대화 내역")
        
        if not messages:
            st.write("아직 대화가 없습니다.")
            return
        
        for i, message in enumerate(messages[-5:]):  # 최근 5개만 표시
            if message["role"] == "user":
                st.write(f"👤 {message['content'][:30]}...")
            else:
                st.write(f"🤖 {message['content'][:30]}...")


def stats_display(products: List[Dict[str, Any]]):
    """통계 표시 컴포넌트"""
    if not products:
        return
    
    st.subheader("📊 검색 결과 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    
    prices = [p.get('price', 0) for p in products]
    ratings = [p.get('rating', 0) for p in products if p.get('rating')]
    
    with col1:
        st.metric("총 상품 수", len(products))
    
    with col2:
        if prices:
            st.metric("평균 가격", f"{sum(prices) // len(prices):,}원")
    
    with col3:
        if prices:
            st.metric("최저 가격", f"{min(prices):,}원")
    
    with col4:
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            st.metric("평균 평점", f"{avg_rating:.1f}⭐")


def loading_animation():
    """로딩 애니메이션"""
    return st.empty()


def error_message(message: str):
    """에러 메시지 표시"""
    st.error(f"❌ {message}")


def success_message(message: str):
    """성공 메시지 표시"""
    st.success(f"✅ {message}")


def info_message(message: str):
    """정보 메시지 표시"""
    st.info(f"ℹ️ {message}")


def warning_message(message: str):
    """경고 메시지 표시"""
    st.warning(f"⚠️ {message}") 