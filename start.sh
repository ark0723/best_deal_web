#!/bin/bash

echo "🛍️  쇼핑 챗봇 서버 시작 스크립트"
echo "=================================="
echo ""
echo "실행 옵션을 선택하세요:"
echo "1) FastAPI만 실행 (포트 8000)"
echo "2) Streamlit만 실행 (포트 8501)"  
echo "3) 두 서버 모두 실행"
echo "4) API 문서 확인 (브라우저에서 열기)"
echo ""
read -p "번호를 입력하세요 (1-4): " choice

case $choice in
    1)
        echo "🚀 FastAPI 서버를 시작합니다..."
        echo "📍 서버 주소: http://localhost:8000"
        echo "📍 API 문서: http://localhost:8000/docs"
        python -m uvicorn backend.main:app --host localhost --port 8000 --reload
        ;;
    2)
        echo "🚀 Streamlit 서버를 시작합니다..."
        echo "📍 서버 주소: http://localhost:8501"
        streamlit run frontend/app.py --server.port 8501
        ;;
    3)
        echo "🚀 두 서버 모두 시작합니다..."
        python run_servers.py
        ;;
    4)
        echo "📖 API 문서를 브라우저에서 엽니다..."
        if command -v open &> /dev/null; then
            open http://localhost:8000/docs
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:8000/docs
        else
            echo "브라우저에서 http://localhost:8000/docs 를 직접 열어주세요"
        fi
        ;;
    *)
        echo "❌ 올바르지 않은 선택입니다."
        ;;
esac 