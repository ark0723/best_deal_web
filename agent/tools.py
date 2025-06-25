"""
쇼핑 에이전트용 도구 함수들
"""

import asyncio
import random
from typing import List, Dict, Any
from langchain_core.tools import tool
from config import settings


@tool
async def search_naver_shopping(query: str) -> List[Dict[str, Any]]:
    """
    네이버 쇼핑 검색 (더미 구현)
    
    Args:
        query: 검색할 상품명
    
    Returns:
        검색된 상품 정보 리스트
    """
    # 검색 시뮬레이션 지연
    await asyncio.sleep(settings.dummy_search_delay)
    
    # 더미 상품 데이터 생성
    dummy_products = []
    categories = ["전자제품", "의류", "생활용품", "스포츠", "도서"]
    sellers = ["네이버쇼핑", "쿠팡", "G마켓", "11번가", "옥션"]
    
    for i in range(min(5, settings.max_search_results)):
        product = {
            "name": f"{query} 상품 {i+1}",
            "price": random.randint(10000, 500000),
            "original_price": random.randint(15000, 600000),
            "discount_rate": random.randint(5, 50),
            "seller": random.choice(sellers),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "review_count": random.randint(10, 1000),
            "image_url": f"https://example.com/image_{i+1}.jpg",
            "product_url": f"https://shopping.naver.com/product/{i+1}",
            "shipping_info": "무료배송" if random.choice([True, False]) else "배송비 3,000원",
            "category": random.choice(categories)
        }
        dummy_products.append(product)
    
    return dummy_products


@tool
async def search_exa(query: str) -> List[Dict[str, Any]]:
    """
    Exa 검색 (더미 구현)
    
    Args:
        query: 검색할 키워드
    
    Returns:
        검색된 정보 리스트
    """
    # 검색 시뮬레이션 지연
    await asyncio.sleep(settings.dummy_search_delay * 0.5)
    
    # 더미 검색 결과 생성
    dummy_results = []
    
    for i in range(min(3, settings.max_search_results // 2)):
        result = {
            "title": f"{query} 관련 정보 {i+1}",
            "content": f"{query}에 대한 상세 정보입니다. 최신 트렌드와 가격 정보를 포함하고 있습니다.",
            "url": f"https://example.com/article_{i+1}",
            "source": f"정보 사이트 {i+1}",
            "published_date": "2024-01-01"
        }
        dummy_results.append(result)
    
    return dummy_results


@tool
def compare_prices(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    상품 가격 비교 및 분석
    
    Args:
        products: 비교할 상품 리스트
    
    Returns:
        가격 분석 결과
    """
    if not products:
        return {"error": "비교할 상품이 없습니다."}
    
    prices = [p.get("price", 0) for p in products]
    
    analysis = {
        "total_products": len(products),
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_price": sum(prices) // len(prices),
        "price_range": max(prices) - min(prices),
        "recommended_product": min(products, key=lambda x: x.get("price", float('inf'))),
        "best_value": max(products, key=lambda x: x.get("rating", 0) * 100 / max(x.get("price", 1), 1))
    }
    
    return analysis


@tool
def filter_products(products: List[Dict[str, Any]], 
                   max_price: int = None, 
                   min_rating: float = None,
                   category: str = None) -> List[Dict[str, Any]]:
    """
    상품 필터링
    
    Args:
        products: 필터링할 상품 리스트
        max_price: 최대 가격
        min_rating: 최소 평점
        category: 카테고리
    
    Returns:
        필터링된 상품 리스트
    """
    filtered = products.copy()
    
    if max_price:
        filtered = [p for p in filtered if p.get("price", 0) <= max_price]
    
    if min_rating:
        filtered = [p for p in filtered if p.get("rating", 0) >= min_rating]
    
    if category:
        filtered = [p for p in filtered if p.get("category", "").lower() == category.lower()]
    
    return filtered


def get_shopping_tools() -> List:
    """쇼핑 도구 목록 반환"""
    return [
        search_naver_shopping,
        search_exa,
        compare_prices,
        filter_products
    ]


# 사용 가능한 모든 툴 목록
AVAILABLE_TOOLS = [
    search_naver_shopping,
    search_exa,
    compare_prices,
    filter_products
] 