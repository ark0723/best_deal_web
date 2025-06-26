"""
SSE 스트리밍 클라이언트
"""

import asyncio
import json
import uuid
import requests
from typing import Callable, Optional, List, Dict, Any
import time


class StreamingChatClient:
    """SSE 기반 실시간 채팅 클라이언트"""
    
    def __init__(self, base_url: str, auto_reconnect: bool = True):
        """클라이언트 초기화"""
        self.base_url = base_url.rstrip('/')
        self.session_id = str(uuid.uuid4())
        self.is_connected = False
        self.auto_reconnect = auto_reconnect
        self.message_queue = []
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # 이벤트 핸들러
        self.on_chunk: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_reconnect: Optional[Callable] = None
    
    def _build_stream_url(self, message: str, session_id: str) -> str:
        """스트리밍 URL 구성"""
        return f"{self.base_url}/chat/stream"
    
    def _create_event_source(self, message: str, session_id: str):
        """EventSource 생성 (실제로는 requests 사용)"""
        url = self._build_stream_url(message, session_id)
        
        payload = {
            "message": message,
            "session_id": session_id
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                stream=True,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache"
                },
                timeout=30
            )
            response.raise_for_status()
            return response
        except Exception as e:
            raise ConnectionError(f"스트리밍 연결 실패: {e}")
    
    async def connect(self, message: str, session_id: Optional[str] = None):
        """스트리밍 연결 및 메시지 전송"""
        session_id = session_id or self.session_id
        
        try:
            response = self._create_event_source(message, session_id)
            self.is_connected = True
            self.reconnect_attempts = 0
            
            if self.on_connect:
                self.on_connect()
            
            await self._process_stream(response)
            
        except Exception as e:
            self.is_connected = False
            if self.on_error:
                self.on_error(str(e))
            
            if self.auto_reconnect and self.reconnect_attempts < self.max_reconnect_attempts:
                await self._handle_connection_error()
    
    async def _process_stream(self, response):
        """스트리밍 응답 처리"""
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    data = line[6:]  # 'data: ' 제거
                    
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data)
                        self._handle_message(chunk)
                    except json.JSONDecodeError:
                        # JSON이 아닌 경우 텍스트로 처리
                        chunk = {"type": "content", "content": data}
                        self._handle_message(chunk)
        
        except Exception as e:
            if self.on_error:
                self.on_error(f"스트리밍 처리 오류: {e}")
        
        finally:
            self.is_connected = False
            if self.on_disconnect:
                self.on_disconnect()
    
    def _handle_message(self, chunk: Dict[str, Any]):
        """메시지 처리"""
        if self.on_chunk:
            self.on_chunk(chunk)
    
    def _handle_error(self, error: str):
        """오류 처리"""
        if self.on_error:
            self.on_error(error)
    
    async def _handle_connection_error(self):
        """연결 오류 처리 및 재연결"""
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts <= self.max_reconnect_attempts:
            # 재연결 지연 (exponential backoff)
            delay = min(2 ** self.reconnect_attempts, 30)
            await asyncio.sleep(delay)
            
            if await self._attempt_reconnect():
                if self.on_reconnect:
                    self.on_reconnect()
            else:
                await self._handle_connection_error()
    
    async def _attempt_reconnect(self) -> bool:
        """재연결 시도"""
        try:
            # 큐에 있는 마지막 메시지로 재연결 시도
            if self.message_queue:
                last_message = self.message_queue[-1]
                await self.connect(last_message, self.session_id)
                return True
            return False
        except Exception:
            return False
    
    def disconnect(self):
        """연결 해제"""
        self.is_connected = False
        if self.on_disconnect:
            self.on_disconnect()
    
    def _add_to_queue(self, message: str):
        """메시지 큐에 추가"""
        self.message_queue.append(message)
        
        # 큐 크기 제한 (최근 10개만 유지)
        if len(self.message_queue) > 10:
            self.message_queue = self.message_queue[-10:]
    
    def _process_queue(self) -> List[str]:
        """큐 처리"""
        processed = self.message_queue.copy()
        self.message_queue.clear()
        return processed 