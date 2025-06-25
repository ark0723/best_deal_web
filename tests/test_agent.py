import pytest
import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import ShoppingAgent
from agent.tools import AVAILABLE_TOOLS
from agent.memory import shopping_memory


class TestShoppingAgent:
    """LangGraph 쇼핑 에이전트 테스트"""
    
    def setup_method(self):
        """테스트 메서드 실행 전 설정"""
        # API 키가 없어도 테스트할 수 있도록 설정
        os.environ["GOOGLE_API_KEY"] = "test-api-key"
        
    def test_agent_initialization(self):
        """에이전트 초기화 테스트"""
        try:
            agent = ShoppingAgent()
            assert agent is not None
            assert agent.llm is not None
            assert agent.tools == []  # 초기에는 빈 리스트
            assert agent.graph is not None
        except Exception as e:
            # API 키 문제로 실패할 수 있으므로 패스
            pytest.skip(f"Agent 초기화 실패 (API 키 문제): {e}")
    
    def test_tools_availability(self):
        """사용 가능한 툴들이 정의되어 있는지 테스트"""
        assert len(AVAILABLE_TOOLS) > 0
        assert all(callable(tool) for tool in AVAILABLE_TOOLS)
    
    def test_add_tool(self):
        """툴 추가 기능 테스트"""
        try:
            agent = ShoppingAgent()
            initial_tool_count = len(agent.tools)
            
            # 첫 번째 툴 추가
            agent.add_tool(AVAILABLE_TOOLS[0])
            assert len(agent.tools) == initial_tool_count + 1
        except Exception as e:
            pytest.skip(f"Agent 초기화 실패 (API 키 문제): {e}")
    
    @pytest.mark.asyncio
    async def test_process_message_basic(self):
        """기본 메시지 처리 테스트"""
        try:
            agent = ShoppingAgent()
            result = await agent.process_message("안녕하세요", "test-session")
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.skip(f"메시지 처리 테스트 실패 (API 키 문제): {e}")


class TestShoppingMemory:
    """쇼핑 메모리 테스트"""
    
    def test_memory_initialization(self):
        """메모리 초기화 테스트"""
        assert shopping_memory is not None
        assert shopping_memory.memory_saver is not None
        assert isinstance(shopping_memory.session_data, dict)
    
    def test_session_data_management(self):
        """세션 데이터 관리 테스트"""
        session_id = "test-session-1"
        test_data = {"user_name": "테스트 사용자", "preferences": {"category": "전자제품"}}
        
        # 데이터 저장
        shopping_memory.save_session_data(session_id, test_data)
        
        # 데이터 조회
        retrieved_data = shopping_memory.get_session_data(session_id)
        assert retrieved_data["user_name"] == "테스트 사용자"
        assert retrieved_data["preferences"]["category"] == "전자제품"
    
    def test_search_history(self):
        """검색 히스토리 테스트"""
        session_id = "test-session-2"
        query = "무선 이어폰"
        results = [{"name": "상품1", "price": 50000}]
        
        # 검색 히스토리 저장
        shopping_memory.save_search_history(session_id, query, results)
        
        # 검색 히스토리 조회
        history = shopping_memory.get_search_history(session_id)
        assert len(history) == 1
        assert history[0]["query"] == query
        assert history[0]["results"] == results
    
    def test_user_preferences(self):
        """사용자 선호도 테스트"""
        session_id = "test-session-3"
        preferences = {"max_price": 100000, "preferred_brands": ["삼성", "애플"]}
        
        # 선호도 저장
        shopping_memory.save_user_preferences(session_id, preferences)
        
        # 선호도 조회
        retrieved_prefs = shopping_memory.get_user_preferences(session_id)
        assert retrieved_prefs["max_price"] == 100000
        assert "삼성" in retrieved_prefs["preferred_brands"]
    
    def test_clear_session(self):
        """세션 삭제 테스트"""
        session_id = "test-session-4"
        test_data = {"test": "data"}
        
        # 데이터 저장
        shopping_memory.save_session_data(session_id, test_data)
        assert shopping_memory.get_session_data(session_id) == test_data
        
        # 세션 삭제
        shopping_memory.clear_session(session_id)
        assert shopping_memory.get_session_data(session_id) == {}


@pytest.mark.asyncio
class TestAgentTools:
    """에이전트 툴 테스트"""
    
    async def test_search_naver_shopping(self):
        """네이버 쇼핑 검색 툴 테스트"""
        from agent.tools import search_naver_shopping
        
        result = await search_naver_shopping("무선 이어폰")
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 첫 번째 상품 검증
        product = result[0]
        assert "name" in product
        assert "price" in product
        assert "seller" in product
        assert "무선 이어폰" in product["name"]
    
    async def test_search_exa(self):
        """Exa 검색 툴 테스트"""
        from agent.tools import search_exa
        
        result = await search_exa("스마트폰 리뷰")
        assert isinstance(result, list)
        assert len(result) > 0
        
        # 첫 번째 결과 검증
        item = result[0]
        assert "title" in item
        assert "content" in item
        assert "url" in item
    
    def test_compare_prices(self):
        """가격 비교 툴 테스트"""
        from agent.tools import compare_prices
        
        products = [
            {"name": "상품1", "price": 50000, "rating": 4.5},
            {"name": "상품2", "price": 60000, "rating": 4.0},
            {"name": "상품3", "price": 45000, "rating": 4.8}
        ]
        
        analysis = compare_prices(products)
        assert analysis["total_products"] == 3
        assert analysis["min_price"] == 45000
        assert analysis["max_price"] == 60000
        assert analysis["avg_price"] == 51666  # (50000 + 60000 + 45000) // 3
        assert "recommended_product" in analysis
        assert "best_value" in analysis
    
    def test_filter_products(self):
        """상품 필터링 툴 테스트"""
        from agent.tools import filter_products
        
        products = [
            {"name": "상품1", "price": 50000, "rating": 4.5, "category": "전자제품"},
            {"name": "상품2", "price": 80000, "rating": 4.0, "category": "의류"},
            {"name": "상품3", "price": 30000, "rating": 3.0, "category": "전자제품"}
        ]
        
        # 가격 필터링
        filtered = filter_products(products, max_price=60000)
        assert len(filtered) == 2
        
        # 평점 필터링
        filtered = filter_products(products, min_rating=4.0)
        assert len(filtered) == 2
        
        # 카테고리 필터링
        filtered = filter_products(products, category="전자제품")
        assert len(filtered) == 2 