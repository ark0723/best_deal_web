"""
MCP 기반 통합 검색 툴
"""

import asyncio
from typing import List, Dict, Any
from langchain_core.tools import tool
from agent.mcp_client import get_mcp_client
import logging

logger = logging.getLogger(__name__)

# DuckDuckGo 실시간 검색 도구 제거됨 - 네이버 API로 대체

# 네이버 실시간 검색 도구 임포트
try:
    from agent.naver_realtime_search import (
        naver_realtime_search, 
        naver_latest_product_search, 
        naver_news_search_tool
    )
    NAVER_TOOLS_AVAILABLE = True
except ImportError:
    logger.warning("네이버 실시간 검색 도구를 가져올 수 없음")
    NAVER_TOOLS_AVAILABLE = False


@tool
async def unified_search_tool(query: str) -> List[Dict[str, Any]]:
    """
    MCP 기반 통합 웹 검색 도구
    
    네이버 검색과 Exa 검색을 통합하여 결과를 제공합니다.
    
    Args:
        query: 검색할 키워드
    
    Returns:
        통합 검색 결과 리스트
    """
    try:
        # MCP 클라이언트 가져오기
        mcp_client = await get_mcp_client()
        
        # 통합 검색 실행
        search_results = await mcp_client.unified_search(query)
        
        # 결과 포맷 통일화
        formatted_results = mcp_client.format_search_results(search_results)
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"통합 검색 실패: {e}")
        return []


@tool
async def naver_search_mcp(query: str) -> Dict[str, Any]:
    """
    네이버 검색 MCP 도구
    
    Args:
        query: 검색할 키워드
    
    Returns:
        네이버 검색 결과
    """
    try:
        mcp_client = await get_mcp_client()
        result = await mcp_client.search_naver(query)
        return result
    except Exception as e:
        logger.error(f"네이버 검색 실패: {e}")
        return {"source": "naver", "results": [], "error": str(e)}


@tool
async def exa_search_mcp(query: str) -> Dict[str, Any]:
    """
    Exa 검색 MCP 도구
    
    Args:
        query: 검색할 키워드
    
    Returns:
        Exa 검색 결과
    """
    try:
        mcp_client = await get_mcp_client()
        result = await mcp_client.search_exa(query)
        return result
    except Exception as e:
        logger.error(f"Exa 검색 실패: {e}")
        return {"source": "exa", "results": [], "error": str(e)}


async def get_mcp_search_tools() -> List:
    """MCP 기반 검색 도구 목록 반환 (실시간 검색 포함)"""
    try:
        # MCP 클라이언트에서 직접 도구 가져오기
        mcp_client = await get_mcp_client()
        mcp_tools = await mcp_client.get_tools()
        
        # 기본 검색 도구 추가
        basic_tools = [
            unified_search_tool,
            naver_search_mcp,
            exa_search_mcp
        ]
        
        # DuckDuckGo 도구 제거됨 - 네이버 API 사용
        
        # 네이버 실시간 검색 도구 추가
        if NAVER_TOOLS_AVAILABLE:
            basic_tools.extend([
                naver_realtime_search,
                naver_latest_product_search,
                naver_news_search_tool
            ])
        
        # MCP 도구와 기본 도구 결합
        all_tools = basic_tools + (mcp_tools if mcp_tools else [])
        
        return all_tools
        
    except Exception as e:
        logger.error(f"MCP 도구 로드 실패: {e}")
        # 에러 시 기본 도구만 반환
        fallback_tools = [
            unified_search_tool,
            naver_search_mcp,
            exa_search_mcp
        ]
        
        # DuckDuckGo 폴백 도구 제거됨
        
        if NAVER_TOOLS_AVAILABLE:
            fallback_tools.extend([
                naver_realtime_search,
                naver_latest_product_search,
                naver_news_search_tool
            ])
        
        return fallback_tools


async def get_shopping_tools_with_mcp() -> List:
    """기존 쇼핑 도구 + MCP 검색 도구"""
    from agent.tools_backup import get_shopping_tools
    
    try:
        # 기존 쇼핑 도구
        original_tools = get_shopping_tools()
        
        # MCP 검색 도구
        mcp_tools = await get_mcp_search_tools()
        
        # 통합 반환 (기존 검색 도구는 제외하고 MCP 도구로 교체)
        filtered_original_tools = [
            tool for tool in original_tools 
            if not (hasattr(tool, 'name') and 'search' in tool.name.lower())
        ]
        
        return filtered_original_tools + mcp_tools
        
    except Exception as e:
        logger.error(f"통합 도구 로드 실패: {e}")
        # 에러 시 기본 도구만 반환
        return await get_mcp_search_tools()


# 사용 가능한 모든 MCP 툴 목록
AVAILABLE_MCP_TOOLS = [
    unified_search_tool,
    naver_search_mcp,
    exa_search_mcp
]

# DuckDuckGo 도구 제거됨 - 네이버 API로 충분

# 네이버 실시간 검색 도구 추가
if NAVER_TOOLS_AVAILABLE:
    AVAILABLE_MCP_TOOLS.extend([
        naver_realtime_search,
        naver_latest_product_search,
        naver_news_search_tool
    ]) 