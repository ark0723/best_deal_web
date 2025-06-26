"""
LangGraph 기반 쇼핑 에이전트 - 멀티턴 대화 지원
"""

from typing import Dict, Any, List, Optional, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.messages.utils import trim_messages
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from config import settings
from agent.tools import get_shopping_tools
import os
import uuid
import asyncio
from typing_extensions import TypedDict


class CustomMessagesState(MessagesState):
    """확장된 메시지 상태 - 사용자 정보 및 대화 컨텍스트 포함"""
    user_id: Optional[str] = None
    session_preferences: Dict[str, Any] = {}
    search_history: List[str] = []


class ShoppingAgent:
    """멀티턴 대화를 지원하는 쇼핑 에이전트"""
    
    def __init__(self):
        """에이전트 초기화"""
        # 체크포인터와 스토어 초기화
        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        
        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.google_api_key,
            temperature=0.7
        )
        
        # 도구 설정 (async 초기화는 별도 메서드에서)
        self.tools = []
        self.tool_node = None
        self.graph = None
        self._initialized = False
    
    async def initialize(self):
        """비동기 초기화"""
        if not self._initialized:
            # MCP 도구 로드
            self.tools = await get_shopping_tools()
            self.tool_node = ToolNode(self.tools)
            
            # 그래프 구성
            self.graph = self._build_graph()
            self._initialized = True
    
    def _build_graph(self) -> StateGraph:
        """대화 그래프 구성"""
        builder = StateGraph(CustomMessagesState)
        
        # 노드 추가
        builder.add_node("agent", self._agent_node)
        builder.add_node("tools", self.tool_node)
        
        # 엣지 추가
        builder.add_edge(START, "agent")
        builder.add_conditional_edges(
            "agent",
            self._should_continue,
            {"continue": "tools", "end": END}
        )
        builder.add_edge("tools", "agent")
        
        # 체크포인터와 스토어와 함께 컴파일
        return builder.compile(checkpointer=self.checkpointer, store=self.store)
    
    def _agent_node(self, state: CustomMessagesState, config: RunnableConfig) -> Dict[str, Any]:
        """에이전트 노드 - LLM 호출 및 응답 생성"""
        # 메시지 트리밍
        messages = self._trim_messages(state["messages"])
        
        # 사용자 메모리 조회
        user_memories = self._get_user_memories(state.get("user_id"))
        
        # 시스템 컨텍스트 구성
        system_context = self._build_system_context(user_memories, state)
        
        # 시스템 메시지 추가
        full_messages = [SystemMessage(content=system_context)] + messages
        
        # LLM 호출
        response = self.llm.bind_tools(self.tools).invoke(full_messages)
        
        # 사용자 선호도 학습
        if state.get("user_id"):
            self._learn_user_preferences(state["user_id"], messages)
        
        return {"messages": [response]}
    
    def _should_continue(self, state: CustomMessagesState) -> str:
        """도구 사용 여부 결정"""
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        return "end"
    
    def _trim_messages(self, messages: List[BaseMessage], max_tokens: int = 4000) -> List[BaseMessage]:
        """메시지 트리밍으로 토큰 제한 관리"""
        if not messages:
            return messages
        
        try:
            # trim_messages 사용
            return trim_messages(
                messages,
                max_tokens=max_tokens,
                strategy="last",
                token_counter=self._count_tokens,
                include_system=False,
                allow_partial=False
            )
        except Exception:
            # 실패 시 최근 10개 메시지만 유지
            return messages[-10:] if len(messages) > 10 else messages
    
    def _count_tokens(self, messages: List[BaseMessage]) -> int:
        """메시지 토큰 수 계산 (근사치)"""
        total_tokens = 0
        for message in messages:
            # 단순한 토큰 계산 (문자 수 / 4)
            total_tokens += len(str(message.content)) // 4
        return total_tokens
    
    def _build_system_context(self, user_memories: List[Dict], state: CustomMessagesState) -> str:
        """시스템 컨텍스트 구성"""
        base_context = """당신은 한국의 최고 쇼핑 어시스턴트입니다.
        
주요 기능:
1. 상품 검색 및 추천
2. 가격 비교 및 할인 정보 제공
3. 리뷰 분석 및 요약
4. 개인화된 쇼핑 조언

대화 원칙:
- 친근하고 도움이 되는 톤으로 응답
- 사용자의 선호도와 과거 대화 기억
- 구체적이고 실용적인 정보 제공
- 필요시 추가 질문으로 요구사항 명확화"""
        
        # 사용자 선호도 추가
        if user_memories:
            preferences = []
            for memory in user_memories[:3]:  # 최근 3개만
                if memory.get('type') == 'preference':
                    preferences.append(memory.get('content', ''))
            
            if preferences:
                base_context += f"\n\n사용자 선호도:\n" + "\n".join(f"- {pref}" for pref in preferences)
        
        # 세션 선호도 추가
        if state.get("session_preferences"):
            session_prefs = state["session_preferences"]
            if session_prefs:
                base_context += f"\n\n현재 세션 정보:\n"
                for key, value in session_prefs.items():
                    base_context += f"- {key}: {value}\n"
        
        return base_context
    
    def _get_user_memories(self, user_id: Optional[str]) -> List[Dict]:
        """사용자 장기 메모리 조회"""
        if not user_id:
            return []
        
        try:
            # 스토어에서 사용자 메모리 검색
            memories = self.store.search(
                namespace=(user_id, "memories"),
                query="",
                limit=10
            )
            return [memory.value for memory in memories]
        except Exception:
            return []
    
    def _learn_user_preferences(self, user_id: str, messages: List[BaseMessage]):
        """사용자 선호도 학습"""
        if not messages:
            return
        
        # 최근 사용자 메시지에서 선호도 키워드 추출
        user_messages = [msg for msg in messages[-5:] if isinstance(msg, HumanMessage)]
        
        for message in user_messages:
            content = message.content.lower()
            
            # 가격 선호도 추출
            if any(keyword in content for keyword in ['저렴', '싸', '할인', '가격']):
                self._save_user_memory(user_id, "가격 중시형 사용자", "preference")
            
            # 브랜드 선호도 추출
            brands = ['삼성', '애플', 'lg', '소니', '나이키', '아디다스']
            for brand in brands:
                if brand in content:
                    self._save_user_memory(user_id, f"{brand} 선호", "preference")
    
    def _save_user_memory(self, user_id: str, content: str, memory_type: str):
        """사용자 메모리 저장"""
        try:
            memory_id = str(uuid.uuid4())
            self.store.put(
                namespace=(user_id, "memories"),
                key=memory_id,
                value={
                    "content": content,
                    "type": memory_type,
                    "timestamp": str(uuid.uuid4())  # 실제로는 실제 타임스탬프 사용
                }
            )
        except Exception:
            pass  # 메모리 저장 실패는 무시
    
    async def _ensure_initialized(self):
        """초기화 확인"""
        if not self._initialized:
            await self.initialize()
    
    async def process_message_stream(
        self, 
        message: str, 
        session_id: str, 
        user_id: Optional[str] = None
    ):
        """스트리밍 방식으로 메시지 처리"""
        try:
            # 초기화 확인
            await self._ensure_initialized()
            
            # 설정 구성
            config = RunnableConfig(
                configurable={
                    "thread_id": session_id,
                    "user_id": user_id or "anonymous"
                }
            )
            
            # 입력 상태 구성
            input_state = {
                "messages": [HumanMessage(content=message)],
                "user_id": user_id,
                "session_preferences": {},
                "search_history": []
            }
            
            # 그래프 스트리밍 실행
            async for event in self.graph.astream(input_state, config=config, stream_mode="updates"):
                for node_name, data in event.items():
                    # 에이전트 노드에서 응답 처리
                    if node_name == "agent" and "messages" in data:
                        last_message = data["messages"][-1]
                        
                        # AI 메시지 처리
                        if isinstance(last_message, AIMessage):
                            # 도구 호출이 있는 경우
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                for tool_call in last_message.tool_calls:
                                    yield {
                                        "type": "tool_call",
                                        "tool_name": tool_call["name"],
                                        "tool_args": tool_call["args"]
                                    }
                            
                            # 텍스트 응답이 있는 경우
                            if last_message.content:
                                # 응답을 단어별로 분할하여 스트리밍
                                words = last_message.content.split()
                                for i, word in enumerate(words):
                                    yield {
                                        "type": "content",
                                        "content": word + " ",
                                        "index": i,
                                        "total": len(words)
                                    }
                                    await asyncio.sleep(0.02)  # 스트리밍 효과
                    
                    # 도구 실행 결과 처리
                    elif node_name == "tools" and "messages" in data:
                        for tool_message in data["messages"]:
                            if hasattr(tool_message, 'name'):
                                yield {
                                    "type": "tool_result",
                                    "tool_name": tool_message.name,
                                    "result_preview": str(tool_message.content)[:100] + "..."
                                }
            
            # 스트리밍 완료 신호
            yield {
                "type": "done",
                "session_id": session_id
            }
            
        except Exception as e:
            # 오류 발생 시 에러 메시지 스트리밍
            yield {
                "type": "error",
                "error": str(e),
                "session_id": session_id
            }

    async def process_message(
        self, 
        message: str, 
        session_id: str, 
        user_id: Optional[str] = None
    ) -> str:
        """메시지 처리 및 응답 생성"""
        # 초기화 확인
        await self._ensure_initialized()
        
        # 설정 구성
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        # 입력 메시지 구성
        input_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_preferences": {},
            "search_history": []
        }
        
        # 그래프 실행
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.graph.invoke(input_state, config)
            )
            
            # 응답 메시지 추출
            last_message = response["messages"][-1]
            if hasattr(last_message, 'content'):
                return last_message.content
            else:
                return str(last_message)
        
        except Exception as e:
            return f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """대화 히스토리 조회"""
        try:
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }
            
            # 현재 상태 조회
            state = self.graph.get_state(config)
            
            if state and state.values and "messages" in state.values:
                messages = state.values["messages"]
                
                # 메시지를 딕셔너리 형태로 변환
                history = []
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        history.append({
                            "role": "user",
                            "content": msg.content,
                            "timestamp": getattr(msg, 'timestamp', None)
                        })
                    elif isinstance(msg, AIMessage):
                        history.append({
                            "role": "assistant", 
                            "content": msg.content,
                            "timestamp": getattr(msg, 'timestamp', None)
                        })
                
                return history
            
            return []
            
        except Exception:
            return []
    
    def clear_session(self, session_id: str) -> bool:
        """세션 초기화"""
        try:
            # 체크포인터에서 스레드 삭제
            self.checkpointer.delete_thread(session_id)
            return True
        except Exception:
            return False 