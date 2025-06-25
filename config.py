import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Google Gemini API 설정
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # 서버 설정
    backend_host: str = os.getenv("BACKEND_HOST", "localhost")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port: int = int(os.getenv("FRONTEND_PORT", "8501"))
    
    # 디버그 모드
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS 설정
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"
    
    def get_cors_origins(self) -> List[str]:
        """CORS origins 리스트 반환"""
        return self.cors_origins.split(",")
    
    # 로그 설정
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Agent 설정
    agent_model: str = "gemini-1.5-flash"
    agent_temperature: float = 0.7
    max_tokens: int = 1000
    
    # 더미 데이터 설정
    dummy_search_delay: float = 1.0  # 검색 시뮬레이션 지연 시간
    max_search_results: int = 10
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


# 전역 설정 인스턴스
settings = Settings() 