"""
네이버 MCP를 활용한 실시간 검색 테스트
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 네이버 실시간 검색 도구들 임포트
from agent.naver_realtime_search import (
    naver_realtime_search,
    naver_latest_product_search,
    naver_news_search_tool,
    close_naver_client
)


async def test_naver_realtime_search():
    """네이버 실시간 검색 테스트"""
    print("🔍 네이버 실시간 검색: '맥북 프로 M4'")
    
    try:
        result = await naver_realtime_search.ainvoke({"query": "맥북 프로 M4"})
        
        print(f"✅ 네이버 실시간 검색 완료: {len(result)}개 결과")
        
        for i, item in enumerate(result[:3], 1):
            print(f"  {i}. [{item.get('source')}] {item.get('title', 'N/A')}")
            print(f"     URL: {item.get('url', 'N/A')[:50]}...")
            print(f"     점수: {item.get('score', 'N/A')}")
            print()
        
        return result
        
    except Exception as e:
        print(f"❌ 네이버 실시간 검색 실패: {e}")
        return []


async def test_naver_latest_product():
    """네이버 최신 제품 검색 테스트"""
    print("\n📱 네이버 최신 제품 검색: '맥북 프로 M4'")
    
    try:
        result = await naver_latest_product_search.ainvoke({"query": "맥북 프로 M4"})
        
        print(f"✅ 네이버 최신 제품 검색 완료: {len(result)}개 결과")
        
        for i, item in enumerate(result[:3], 1):
            print(f"  {i}. [{item.get('source')}] {item.get('title', 'N/A')}")
            print(f"     내용: {item.get('content', 'N/A')[:80]}...")
            if item.get('price'):
                print(f"     가격: {item.get('price')}")
            print()
        
        return result
        
    except Exception as e:
        print(f"❌ 네이버 최신 제품 검색 실패: {e}")
        return []


async def test_naver_news():
    """네이버 뉴스 검색 테스트"""
    print("\n📰 네이버 뉴스 검색: '맥북 프로 M4'")
    
    try:
        result = await naver_news_search_tool.ainvoke({"query": "맥북 프로 M4"})
        
        print(f"✅ 네이버 뉴스 검색 완료: {len(result)}개 결과")
        
        for i, item in enumerate(result[:3], 1):
            print(f"  {i}. {item.get('title', 'N/A')}")
            print(f"     내용: {item.get('content', 'N/A')[:80]}...")
            if item.get('pubDate'):
                print(f"     발행일: {item.get('pubDate')}")
            print()
        
        return result
        
    except Exception as e:
        print(f"❌ 네이버 뉴스 검색 실패: {e}")
        return []


async def unified_naver_search(query: str):
    """통합 네이버 검색"""
    print(f"\n🔄 통합 네이버 검색: '{query}'")
    
    # 병렬로 모든 네이버 검색 실행
    tasks = [
        test_naver_realtime_search(),
        test_naver_latest_product(),
        test_naver_news()
    ]
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n📊 통합 검색 결과:")
        search_types = ["실시간 검색", "최신 제품", "뉴스"]
        
        all_results = []
        total_count = 0
        for i, (search_type, result) in enumerate(zip(search_types, results)):
            if isinstance(result, Exception):
                print(f"  ❌ {search_type}: {result}")
            elif result and len(result) > 0:
                print(f"  ✅ {search_type}: {len(result)}개 결과")
                all_results.extend(result)
                total_count += len(result)
            else:
                print(f"  ⚠️  {search_type}: 결과 없음")
        
        return all_results
        
    except Exception as e:
        print(f"❌ 통합 네이버 검색 실패: {e}")
        return []


async def main():
    """메인 테스트 함수"""
    print("🚀 네이버 MCP 실시간 검색 테스트 시작\n")
    
    # API 키 확인
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    if naver_client_id and naver_client_secret:
        print(f"✅ 네이버 API 키 확인됨")
        print(f"   Client ID: {naver_client_id[:10]}...")
        print(f"   Client Secret: {naver_client_secret[:10]}...")
    else:
        print("❌ 네이버 API 키가 설정되지 않음")
        print("   .env 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET을 설정해주세요")
    
    print("=" * 60)
    
    # 개별 네이버 검색 테스트
    await test_naver_realtime_search()
    await test_naver_latest_product()
    await test_naver_news()
    
    print("\n" + "=" * 60)
    
    # 통합 네이버 검색 테스트
    unified_results = await unified_naver_search("맥북 프로 M4")
    
    print(f"\n📈 최종 결과: {len(unified_results)}개 총 데이터 수집")
    
    print("\n" + "=" * 60)
    print("✨ 네이버 MCP 테스트 완료!")
    
    # 세션 정리
    await close_naver_client()
    print("🧹 세션 정리 완료")


if __name__ == "__main__":
    asyncio.run(main()) 