"""
쇼핑 챗봇 API 라우트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from agent.agent import ShoppingAgent
import uuid
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter()

# 전역 에이전트 인스턴스
try:
    shopping_agent = ShoppingAgent()
    logger.info("✅ ShoppingAgent 초기화 성공")
except Exception as e:
    logger.error(f"❌ ShoppingAgent 초기화 실패: {e}")
    shopping_agent = None


# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: Optional[str] = None


class HistoryResponse(BaseModel):
    history: List[Dict[str, Any]]
    session_id: str


# 헬스 체크
@router.get("/health")
async def health_check():
    """서버 상태 확인"""
    if shopping_agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not initialized")
    
    return {
        "status": "healthy",
        "message": "쇼핑 챗봇 서버가 정상 작동 중입니다",
        "agent_status": "ready"
    }


# 채팅 엔드포인트
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """멀티턴 대화 처리"""
    if shopping_agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not available")
    
    try:
        # 세션 ID 생성 (없는 경우)
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id
        
        logger.info(f"📩 메시지 처리: session={session_id}, user={user_id}")
        
        # 에이전트로 메시지 처리
        response = await shopping_agent.process_message(
            message=request.message,
            session_id=session_id,
            user_id=user_id
        )
        
        logger.info(f"✅ 응답 생성 완료: {len(response)}자")
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            user_id=user_id
        )
        
    except Exception as e:
        logger.error(f"❌ 채팅 처리 오류: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
        )


# 대화 히스토리 조회
@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """세션별 대화 히스토리 조회"""
    if shopping_agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not available")
    
    try:
        history = shopping_agent.get_conversation_history(session_id)
        
        return HistoryResponse(
            history=history,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"❌ 히스토리 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"히스토리 조회 중 오류가 발생했습니다: {str(e)}"
        )


# 세션 초기화
@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """세션 초기화"""
    if shopping_agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not available")
    
    try:
        result = shopping_agent.clear_session(session_id)
        
        return {
            "message": f"세션 {session_id}이 초기화되었습니다",
            "success": result
        }
        
    except Exception as e:
        logger.error(f"❌ 세션 초기화 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"세션 초기화 중 오류가 발생했습니다: {str(e)}"
        )


# 에이전트 상태 조회
@router.get("/agent/status")
async def get_agent_status():
    """에이전트 상태 정보"""
    if shopping_agent is None:
        return {"status": "not_initialized", "error": "ShoppingAgent not available"}
    
    return {
        "status": "ready",
        "checkpointer": "InMemorySaver",
        "store": "InMemoryStore",
        "tools_count": len(shopping_agent.tools),
        "graph_compiled": shopping_agent.graph is not None
    } 