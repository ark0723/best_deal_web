#!/usr/bin/env python3
"""
FastAPI와 Streamlit 서버를 동시에 실행하는 스크립트
"""

import subprocess
import time
import sys
import signal
import os
from threading import Thread


def run_fastapi():
    """FastAPI 서버 실행"""
    print("🚀 FastAPI 서버를 시작합니다...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "backend.main:app", 
            "--host", "localhost", 
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 FastAPI 서버를 종료합니다.")


def run_streamlit():
    """Streamlit 서버 실행"""
    print("🚀 Streamlit 서버를 시작합니다...")
    time.sleep(3)  # FastAPI가 먼저 시작되도록 대기
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", 
            "run", "frontend/app.py",
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Streamlit 서버를 종료합니다.")


def signal_handler(sig, frame):
    """Ctrl+C 신호 처리"""
    print("\n\n🛑 서버들을 종료합니다...")
    os._exit(0)


def main():
    """메인 함수"""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("="*60)
    print("🛍️  쇼핑 챗봇 서버 시작")
    print("="*60)
    print("📍 FastAPI Backend: http://localhost:8000")
    print("📍 Streamlit Frontend: http://localhost:8501")
    print("📍 API 문서: http://localhost:8000/docs")
    print("="*60)
    print("⏹️  종료하려면 Ctrl+C를 누르세요")
    print("="*60)
    
    # 두 서버를 별도 스레드에서 실행
    fastapi_thread = Thread(target=run_fastapi, daemon=True)
    streamlit_thread = Thread(target=run_streamlit, daemon=True)
    
    fastapi_thread.start()
    streamlit_thread.start()
    
    try:
        # 메인 스레드는 대기
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 서버들을 종료합니다...")


if __name__ == "__main__":
    main() 