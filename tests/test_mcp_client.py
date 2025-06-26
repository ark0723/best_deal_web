"""
MCP 클라이언트 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from agent.mcp_client import MCPSearchClient


class TestMCPSearchClient:
    """MCP 검색 클라이언트 테스트"""
    
    @pytest.fixture
    def mcp_client(self):
        """MCP 클라이언트 픽스처"""
        return MCPSearchClient()
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, mcp_client):
        """클라이언트 초기화 테스트"""
        assert mcp_client is not None
        assert hasattr(mcp_client, 'client')
        assert hasattr(mcp_client, 'tools')
    
    @pytest.mark.asyncio
    async def test_get_tools(self, mcp_client):
        """툴 로드 테스트"""
        with patch.object(mcp_client, '_load_tools', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [MagicMock(name="naver_search"), MagicMock(name="exa_search")]
            
            tools = await mcp_client.get_tools()
            
            assert tools is not None
            assert len(tools) >= 0
            mock_load.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_naver_search_connection(self, mcp_client):
        """네이버 검색 MCP 연결 테스트"""
        # 클라이언트가 있다고 가정하고 모킹
        mock_client = AsyncMock()
        mock_session = AsyncMock()
        mock_client.session.return_value.__aenter__.return_value = mock_session
        
        with patch('langchain_mcp_adapters.tools.load_mcp_tools', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [MagicMock(name="naver_search")]
            mcp_client.client = mock_client
            
            result = await mcp_client.connect_naver_search()
            
            assert result is True
            assert mcp_client.naver_connected is True
    
    @pytest.mark.asyncio
    async def test_exa_search_connection(self, mcp_client):
        """Exa 검색 MCP 연결 테스트"""
        # 클라이언트가 있다고 가정하고 모킹
        mock_client = AsyncMock()
        mock_session = AsyncMock()
        mock_client.session.return_value.__aenter__.return_value = mock_session
        
        with patch('langchain_mcp_adapters.tools.load_mcp_tools', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [MagicMock(name="exa_search")]
            mcp_client.client = mock_client
            
            result = await mcp_client.connect_exa_search()
            
            assert result is True
            assert mcp_client.exa_connected is True
    
    @pytest.mark.asyncio
    async def test_unified_search(self, mcp_client):
        """통합 검색 테스트"""
        mock_naver_result = {"source": "naver", "results": []}
        mock_exa_result = {"source": "exa", "results": []}
        
        # 연결 상태를 True로 설정
        mcp_client.naver_connected = True
        mcp_client.exa_connected = True
        
        with patch.object(mcp_client, 'search_naver', new_callable=AsyncMock) as mock_naver:
            with patch.object(mcp_client, 'search_exa', new_callable=AsyncMock) as mock_exa:
                mock_naver.return_value = mock_naver_result
                mock_exa.return_value = mock_exa_result
                
                results = await mcp_client.unified_search("테스트 쿼리")
                
                assert results is not None
                assert len(results) >= 0
                mock_naver.assert_called_once_with("테스트 쿼리")
                mock_exa.assert_called_once_with("테스트 쿼리")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mcp_client):
        """에러 핸들링 테스트"""
        mcp_client.naver_connected = True
        
        with patch.object(mcp_client, 'search_naver', new_callable=AsyncMock) as mock_naver:
            mock_naver.side_effect = Exception("Connection error")
            
            results = await mcp_client.unified_search("테스트 쿼리")
            
            # 에러가 발생해도 빈 결과를 반환해야 함
            assert results is not None 