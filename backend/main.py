"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from backend.routes import router


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    app = FastAPI(
        title="쇼핑 챗봇 API",
        description="LangGraph 기반 쇼핑 챗봇 백엔드 API",
        version="1.0.0",
        debug=settings.debug
    )
    
    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 라우터 포함
    app.include_router(router)
    
    return app


app = create_app()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "쇼핑 챗봇 API 서버가 실행 중입니다"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug
    ) 