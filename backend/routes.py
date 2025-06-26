"""
쇼핑 챗봇 API 라우트
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from agent.agent import ShoppingAgent
import uuid
import logging
import json
import asyncio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter()

# 전역 에이전트 인스턴스
shopping_agent = None


async def init_agent():
    """에이전트 초기화"""
    global shopping_agent
    try:
        shopping_agent = ShoppingAgent()
        await shopping_agent.initialize()  # MCP 초기화 포함
        logger.info("✅ ShoppingAgent MCP 초기화 성공")
    except Exception as e:
        logger.error(f"❌ ShoppingAgent 초기화 실패: {e}")
        shopping_agent = None


async def ensure_agent_ready():
    """에이전트 준비 상태 확인"""
    global shopping_agent
    if shopping_agent is None:
        await init_agent()
    return shopping_agent


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


async def generate_sse_stream(message: str, session_id: str, user_id: Optional[str] = None):
    """SSE 스트리밍 데이터 생성"""
    try:
        agent = await ensure_agent_ready()
        if agent is None:
            yield f"data: {json.dumps({'type': 'error', 'error': 'ShoppingAgent not available'})}\n\n"
            return
        
        logger.info(f"🔄 스트리밍 시작: session={session_id}")
        
        # 실제 스트리밍 AI 응답 생성
        async for chunk in agent.process_message_stream(
            message=message,
            session_id=session_id,
            user_id=user_id
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01)  # 약간의 지연
        
        # 스트리밍 완료 신호
        yield f"data: [DONE]\n\n"
        
        logger.info(f"✅ 스트리밍 완료: session={session_id}")
        
    except Exception as e:
        logger.error(f"❌ 스트리밍 오류: {e}")
        error_data = {"type": "error", "error": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"
        yield f"data: [DONE]\n\n"


# 헬스 체크
@router.get("/health")
async def health_check():
    """서버 상태 확인"""
    agent = await ensure_agent_ready()
    if agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not initialized")
    
    return {
        "status": "healthy",
        "message": "쇼핑 챗봇 서버가 정상 작동 중입니다 (MCP 통합)",
        "agent_status": "ready",
        "mcp_status": "integrated"
    }


# SSE 스트리밍 채팅 엔드포인트
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE 스트리밍 방식 대화 처리"""
    if not request.message.strip() and request.message != "":
        raise HTTPException(status_code=400, detail="메시지가 필요합니다")
    
    # 세션 ID 생성 (없는 경우)
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id
    
    logger.info(f"📡 SSE 스트리밍 요청: session={session_id}")
    
    return StreamingResponse(
        generate_sse_stream(request.message, session_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


# 채팅 엔드포인트
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """멀티턴 대화 처리"""
    agent = await ensure_agent_ready()
    if agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not available")
    
    try:
        # 세션 ID 생성 (없는 경우)
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id
        
        logger.info(f"📩 메시지 처리: session={session_id}, user={user_id}")
        
        # 에이전트로 메시지 처리
        response = await agent.process_message(
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
    agent = await ensure_agent_ready()
    if agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not available")
    
    try:
        history = agent.get_conversation_history(session_id)
        
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
    agent = await ensure_agent_ready()
    if agent is None:
        raise HTTPException(status_code=503, detail="ShoppingAgent not available")
    
    try:
        result = agent.clear_session(session_id)
        
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