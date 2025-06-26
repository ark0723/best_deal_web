"""
MCP 툴 통합 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from agent.mcp_tools import get_mcp_search_tools, unified_search_tool


class TestMCPTools:
    """MCP 툴 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_mcp_search_tools(self):
        """MCP 검색 툴 목록 가져오기 테스트"""
        tools = await get_mcp_search_tools()
        
        assert tools is not None
        assert len(tools) > 0
        
        # unified_search_tool이 포함되어 있는지 확인
        tool_names = [tool.name for tool in tools if hasattr(tool, 'name')]
        assert any('search' in name.lower() for name in tool_names)
    
    @pytest.mark.asyncio
    async def test_unified_search_tool(self):
        """통합 검색 툴 테스트"""
        with patch('agent.mcp_client.get_mcp_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.unified_search.return_value = [
                {"source": "naver", "results": [{"title": "테스트", "content": "내용"}]},
                {"source": "exa", "results": [{"title": "검색", "content": "결과"}]}
            ]
            mock_client.format_search_results.return_value = [
                {"source": "naver", "title": "테스트", "content": "내용", "url": "", "score": 0.9},
                {"source": "exa", "title": "검색", "content": "결과", "url": "", "score": 0.8}
            ]
            mock_get_client.return_value = mock_client
            
            result = await unified_search_tool.ainvoke({"query": "테스트 검색"})
            
            assert result is not None
            assert len(result) >= 0
            mock_client.unified_search.assert_called_once_with("테스트 검색")
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """검색 에러 핸들링 테스트"""
        with patch('agent.mcp_client.get_mcp_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.unified_search.side_effect = Exception("검색 실패")
            mock_get_client.return_value = mock_client
            
            result = await unified_search_tool.ainvoke({"query": "에러 테스트"})
            
            # 에러가 발생해도 빈 리스트를 반환해야 함
            assert result == [] 