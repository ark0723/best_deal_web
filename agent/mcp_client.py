"""
MCP 기반 웹 검색 클라이언트
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from config import settings
import logging

logger = logging.getLogger(__name__)

# DuckDuckGo 실시간 검색 제거됨 - 네이버 API 사용

# 네이버 실시간 검색 임포트
try:
    from .naver_realtime_search import get_naver_client
    NAVER_SEARCH_AVAILABLE = True
except ImportError:
    logger.warning("네이버 실시간 검색 모듈을 가져올 수 없음")
    NAVER_SEARCH_AVAILABLE = False


class MCPSearchClient:
    """MCP 기반 통합 검색 클라이언트"""
    
    def __init__(self):
        """클라이언트 초기화"""
        self.client = None
        self.tools = []
        self.naver_connected = False
        self.exa_connected = False
        self._naver_tools = []
        self._exa_tools = []
    
    async def initialize(self) -> bool:
        """클라이언트 초기화"""
        try:
            # MultiServerMCPClient 설정
            server_config = {
                "naver_search_mcp": {
                    "url": os.getenv("NAVER_SEARCH_MCP_URL", "http://localhost:8001/mcp"),
                    "transport": "streamable_http",
                },
                "exa_search_mcp": {
                    "url": os.getenv("EXA_SEARCH_MCP_URL", "http://localhost:8002/mcp"),
                    "transport": "streamable_http",
                }
            }
            
            self.client = MultiServerMCPClient(server_config)
            
            # 개별 연결 시도
            await self.connect_naver_search()
            await self.connect_exa_search()
            
            # 모든 툴 로드
            await self.get_tools()
            
            return True
            
        except Exception as e:
            logger.error(f"MCP 클라이언트 초기화 실패: {e}")
            return False
    
    async def connect_naver_search(self) -> bool:
        """네이버 검색 MCP 연결"""
        try:
            if self.client:
                async with self.client.session("naver_search_mcp") as session:
                    await session.initialize()
                    naver_tools = await load_mcp_tools(session)
                    self._naver_tools = naver_tools
                    self.naver_connected = True
                    logger.info("네이버 검색 MCP 연결 성공")
                    return True
            return False
        except Exception as e:
            logger.warning(f"네이버 검색 MCP 연결 실패: {e}")
            self.naver_connected = False
            return False
    
    async def connect_exa_search(self) -> bool:
        """Exa 검색 MCP 연결"""
        try:
            if self.client:
                async with self.client.session("exa_search_mcp") as session:
                    await session.initialize()
                    exa_tools = await load_mcp_tools(session)
                    self._exa_tools = exa_tools
                    self.exa_connected = True
                    logger.info("Exa 검색 MCP 연결 성공")
                    return True
            return False
        except Exception as e:
            logger.warning(f"Exa 검색 MCP 연결 실패: {e}")
            self.exa_connected = False
            return False
    
    async def get_tools(self) -> List:
        """모든 MCP 툴 반환"""
        try:
            return await self._load_tools()
        except Exception as e:
            logger.error(f"툴 로드 실패: {e}")
            return []
    
    async def _load_tools(self) -> List:
        """내부 툴 로드 메서드"""
        try:
            if self.client:
                all_tools = await self.client.get_tools()
                self.tools = all_tools
                return all_tools
            return []
        except Exception as e:
            logger.error(f"내부 툴 로드 실패: {e}")
            return []
    
    async def search_naver(self, query: str) -> Dict[str, Any]:
        """네이버 검색 실행"""
        if not self.naver_connected or not self._naver_tools:
            return {"source": "naver", "results": [], "error": "네이버 검색 연결 안됨"}
        
        try:
            # 네이버 검색 툴 실행
            for tool in self._naver_tools:
                if "search" in tool.name.lower() or "naver" in tool.name.lower():
                    result = await tool.ainvoke({"query": query})
                    return {"source": "naver", "results": result}
            
            return {"source": "naver", "results": [], "error": "검색 툴을 찾을 수 없음"}
            
        except Exception as e:
            logger.error(f"네이버 검색 실패: {e}")
            return {"source": "naver", "results": [], "error": str(e)}
    
    async def search_exa(self, query: str) -> Dict[str, Any]:
        """Exa 검색 실행"""
        if not self.exa_connected or not self._exa_tools:
            return {"source": "exa", "results": [], "error": "Exa 검색 연결 안됨"}
        
        try:
            # Exa 검색 툴 실행
            for tool in self._exa_tools:
                if "search" in tool.name.lower() or "exa" in tool.name.lower():
                    result = await tool.ainvoke({"query": query})
                    return {"source": "exa", "results": result}
            
            return {"source": "exa", "results": [], "error": "검색 툴을 찾을 수 없음"}
            
        except Exception as e:
            logger.error(f"Exa 검색 실패: {e}")
            return {"source": "exa", "results": [], "error": str(e)}
    
    async def unified_search(self, query: str, use_realtime_fallback: bool = True) -> List[Dict[str, Any]]:
        """통합 검색 실행 (실시간 폴백 포함)"""
        results = []
        
        # 병렬 검색 실행
        search_tasks = []
        
        if self.naver_connected:
            search_tasks.append(self.search_naver(query))
        
        if self.exa_connected:
            search_tasks.append(self.search_exa(query))
        
        try:
            if search_tasks:
                search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                for result in search_results:
                    if isinstance(result, dict) and not isinstance(result, Exception):
                        results.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"검색 중 오류 발생: {result}")
            
            # MCP 검색이 실패하거나 결과가 없을 때 실시간 검색 폴백 사용
            if use_realtime_fallback:
                has_valid_results = any(
                    result.get("results") and len(result.get("results", [])) > 0 
                    for result in results
                )
                
                if not has_valid_results:
                    logger.info("MCP 검색 결과가 없어 실시간 검색 폴백 사용")
                    
                    # 네이버 실시간 검색 시도
                    if NAVER_SEARCH_AVAILABLE:
                        try:
                            naver_client = await get_naver_client()
                            naver_results = await naver_client.unified_naver_search(query)
                            
                            if naver_results:
                                results.append({
                                    "source": "naver_realtime",
                                    "results": naver_results
                                })
                                logger.info(f"네이버 실시간 검색 완료: {len(naver_results)}개 결과")
                            
                        except Exception as e:
                            logger.error(f"네이버 실시간 검색 실패: {e}")
                    
                    # DuckDuckGo 폴백 제거됨 - 네이버 API가 충분히 효과적임
            
            return results
            
        except Exception as e:
            logger.error(f"통합 검색 실패: {e}")
            return []
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """검색 결과 포맷 통일화"""
        formatted_results = []
        
        for result in results:
            source = result.get("source", "unknown")
            search_results = result.get("results", [])
            
            if isinstance(search_results, list):
                for item in search_results:
                    formatted_item = {
                        "source": source,
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "url": item.get("url", ""),
                        "score": item.get("score", 0.0)
                    }
                    formatted_results.append(formatted_item)
        
        # 점수 기준으로 정렬
        formatted_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return formatted_results
    
    async def close(self):
        """연결 종료"""
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.error(f"클라이언트 종료 중 오류: {e}")


# 전역 MCP 클라이언트 인스턴스
_mcp_client = None


async def get_mcp_client() -> MCPSearchClient:
    """MCP 클라이언트 싱글톤 접근"""
    global _mcp_client
    
    if _mcp_client is None:
        _mcp_client = MCPSearchClient()
        await _mcp_client.initialize()
    
    return _mcp_client 