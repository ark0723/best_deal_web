"""
네이버 API를 활용한 실시간 검색 모듈
"""

import asyncio
import aiohttp
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


class NaverRealtimeSearchClient:
    """네이버 실시간 검색 클라이언트"""
    
    def __init__(self):
        self.session = None
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            logger.warning("네이버 API 키가 설정되지 않음. 네이버 검색 기능이 제한됩니다.")
    
    async def _get_session(self):
        """HTTP 세션 가져오기"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _get_headers(self):
        """네이버 API 헤더 생성"""
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    async def search_web(self, query: str, display: int = 10, sort: str = "date") -> List[Dict[str, Any]]:
        """네이버 웹 검색"""
        if not self.client_id or not self.client_secret:
            logger.warning("네이버 API 키가 없어 웹 검색을 건너뜁니다.")
            return []
        
        try:
            session = await self._get_session()
            url = "https://openapi.naver.com/v1/search/webkr.json"
            
            params = {
                "query": query,
                "display": display,
                "sort": sort
            }
            
            headers = self._get_headers()
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    results = []
                    for item in items:
                        results.append({
                            "title": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                            "content": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                            "url": item.get("link", ""),
                            "source": "naver_web",
                            "score": 0.8,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    return results
                else:
                    logger.error(f"네이버 웹 검색 API 오류: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"네이버 웹 검색 실패: {e}")
            return []
    
    async def search_news(self, query: str, display: int = 10, sort: str = "date") -> List[Dict[str, Any]]:
        """네이버 뉴스 검색"""
        if not self.client_id or not self.client_secret:
            logger.warning("네이버 API 키가 없어 뉴스 검색을 건너뜁니다.")
            return []
        
        try:
            session = await self._get_session()
            url = "https://openapi.naver.com/v1/search/news.json"
            
            params = {
                "query": query,
                "display": display,
                "sort": sort
            }
            
            headers = self._get_headers()
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    results = []
                    for item in items:
                        results.append({
                            "title": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                            "content": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                            "url": item.get("link", ""),
                            "source": "naver_news",
                            "score": 0.9,  # 뉴스는 신뢰도가 높음
                            "timestamp": datetime.now().isoformat(),
                            "pubDate": item.get("pubDate", "")
                        })
                    
                    return results
                else:
                    logger.error(f"네이버 뉴스 검색 API 오류: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"네이버 뉴스 검색 실패: {e}")
            return []
    
    async def search_blog(self, query: str, display: int = 10, sort: str = "date") -> List[Dict[str, Any]]:
        """네이버 블로그 검색"""
        if not self.client_id or not self.client_secret:
            logger.warning("네이버 API 키가 없어 블로그 검색을 건너뜁니다.")
            return []
        
        try:
            session = await self._get_session()
            url = "https://openapi.naver.com/v1/search/blog.json"
            
            params = {
                "query": query,
                "display": display,
                "sort": sort
            }
            
            headers = self._get_headers()
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    results = []
                    for item in items:
                        results.append({
                            "title": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                            "content": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                            "url": item.get("link", ""),
                            "source": "naver_blog",
                            "score": 0.7,
                            "timestamp": datetime.now().isoformat(),
                            "bloggerName": item.get("bloggername", ""),
                            "postDate": item.get("postdate", "")
                        })
                    
                    return results
                else:
                    logger.error(f"네이버 블로그 검색 API 오류: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"네이버 블로그 검색 실패: {e}")
            return []
    
    async def search_shopping(self, query: str, display: int = 10, sort: str = "date") -> List[Dict[str, Any]]:
        """네이버 쇼핑 검색"""
        if not self.client_id or not self.client_secret:
            logger.warning("네이버 API 키가 없어 쇼핑 검색을 건너뜁니다.")
            return []
        
        try:
            session = await self._get_session()
            url = "https://openapi.naver.com/v1/search/shop.json"
            
            params = {
                "query": query,
                "display": display,
                "sort": sort
            }
            
            headers = self._get_headers()
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    results = []
                    for item in items:
                        results.append({
                            "title": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                            "content": item.get("description", "").replace("<b>", "").replace("</b>", ""),
                            "url": item.get("link", ""),
                            "source": "naver_shopping",
                            "score": 0.85,
                            "timestamp": datetime.now().isoformat(),
                            "price": item.get("lprice", ""),
                            "mallName": item.get("mallName", ""),
                            "brand": item.get("brand", "")
                        })
                    
                    return results
                else:
                    logger.error(f"네이버 쇼핑 검색 API 오류: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"네이버 쇼핑 검색 실패: {e}")
            return []
    
    async def unified_naver_search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """통합 네이버 검색"""
        all_results = []
        
        # 각 검색 타입별 결과 수 분배
        results_per_type = max_results // 4
        
        # 병렬로 모든 네이버 검색 실행
        search_tasks = [
            self.search_web(query, results_per_type, "date"),
            self.search_news(query, results_per_type, "date"),
            self.search_blog(query, results_per_type, "date"),
            self.search_shopping(query, results_per_type, "date")
        ]
        
        try:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for result in search_results:
                if isinstance(result, list) and not isinstance(result, Exception):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"네이버 검색 중 오류: {result}")
            
            # 점수 기준으로 정렬하고 중복 제거
            unique_results = []
            seen_urls = set()
            
            for result in sorted(all_results, key=lambda x: x.get("score", 0), reverse=True):
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            return unique_results[:max_results]
            
        except Exception as e:
            logger.error(f"통합 네이버 검색 실패: {e}")
            return []
    
    async def close(self):
        """세션 종료"""
        if self.session:
            await self.session.close()


# 전역 네이버 검색 클라이언트
_naver_client = None


async def get_naver_client() -> NaverRealtimeSearchClient:
    """네이버 검색 클라이언트 싱글톤 접근"""
    global _naver_client
    
    if _naver_client is None:
        _naver_client = NaverRealtimeSearchClient()
    
    return _naver_client


async def close_naver_client():
    """네이버 검색 클라이언트 세션 종료"""
    global _naver_client
    
    if _naver_client is not None:
        await _naver_client.close()
        _naver_client = None


@tool
async def naver_realtime_search(query: str) -> List[Dict[str, Any]]:
    """
    네이버 실시간 검색 도구
    
    네이버 API를 사용하여 웹, 뉴스, 블로그, 쇼핑에서 최신 정보를 검색합니다.
    맥북 프로 M4 같은 최신 제품 정보에 특히 유용합니다.
    
    Args:
        query: 검색할 키워드
    
    Returns:
        네이버 통합 검색 결과 리스트
    """
    try:
        client = await get_naver_client()
        results = await client.unified_naver_search(query)
        
        logger.info(f"네이버 실시간 검색 완료: {len(results)}개 결과")
        return results
        
    except Exception as e:
        logger.error(f"네이버 실시간 검색 실패: {e}")
        return []


@tool
async def naver_latest_product_search(query: str) -> List[Dict[str, Any]]:
    """
    네이버 최신 제품 정보 검색 도구
    
    네이버에서 최신 제품 출시 정보, 스펙, 가격 등을 검색합니다.
    
    Args:
        query: 제품명 (예: "맥북 프로 M4", "아이폰 15 프로")
    
    Returns:
        네이버 최신 제품 정보 검색 결과
    """
    try:
        # 제품 검색에 최적화된 쿼리 추가
        enhanced_query = f"{query} 최신 2024 출시 스펙 가격"
        
        client = await get_naver_client()
        results = await client.unified_naver_search(enhanced_query)
        
        # 제품 정보에 특화된 필터링
        product_results = []
        for result in results:
            title = result.get("title", "").lower()
            content = result.get("content", "").lower()
            
            # 제품 정보 관련 키워드 확인
            if any(keyword in title or keyword in content for keyword in 
                   ["스펙", "가격", "출시", "리뷰", "성능", "비교", "2024", "최신", "신제품"]):
                product_results.append(result)
        
        logger.info(f"네이버 최신 제품 검색 완료: {len(product_results)}개 결과")
        return product_results[:10]  # 상위 10개 결과만 반환
        
    except Exception as e:
        logger.error(f"네이버 최신 제품 검색 실패: {e}")
        return []


@tool
async def naver_news_search_tool(query: str) -> List[Dict[str, Any]]:
    """
    네이버 뉴스 검색 도구
    
    최신 뉴스만 검색하여 가장 신뢰할 수 있는 정보를 제공합니다.
    
    Args:
        query: 검색할 키워드
    
    Returns:
        네이버 뉴스 검색 결과
    """
    try:
        client = await get_naver_client()
        results = await client.search_news(query, display=10, sort="date")
        
        logger.info(f"네이버 뉴스 검색 완료: {len(results)}개 결과")
        return results
        
    except Exception as e:
        logger.error(f"네이버 뉴스 검색 실패: {e}")
        return [] 