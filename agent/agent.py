"""
LangGraph 기반 쇼핑 에이전트
"""

from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from config import settings
import os


class ShoppingAgent:
    """쇼핑 챗봇 에이전트"""
    
    def __init__(self):
        """에이전트 초기화"""
        # API 키 검증
        api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "test-api-key":
            # 테스트 환경에서는 더미 LLM 사용
            self.llm = None
        else:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=settings.agent_model,
                    temperature=settings.agent_temperature,
                    google_api_key=api_key
                )
            except Exception as e:
                print(f"LLM 초기화 실패: {e}")
                self.llm = None
        
        self.tools = []
        self.graph = None
        self._setup_graph()
    
    def _setup_graph(self):
        """LangGraph 그래프 설정"""
        try:
            # 기본 그래프 구조 생성
            workflow = StateGraph(dict)
            
            # 노드 추가
            workflow.add_node("agent", self._agent_node)
            if self.tools:
                workflow.add_node("tools", ToolNode(self.tools))
                
                # 엣지 추가 (툴이 있는 경우)
                workflow.set_entry_point("agent")
                workflow.add_conditional_edges(
                    "agent",
                    self._should_continue,
                    {
                        "continue": "tools",
                        "end": END
                    }
                )
                workflow.add_edge("tools", "agent")
            else:
                # 툴이 없는 경우 간단한 그래프
                workflow.set_entry_point("agent")
                workflow.add_edge("agent", END)
            
            self.graph = workflow.compile()
        except Exception as e:
            print(f"그래프 설정 실패: {e}")
            self.graph = None
    
    def _agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 노드 실행"""
        messages = state.get("messages", [])
        
        if self.llm is None:
            # 테스트 모드에서는 더미 응답
            dummy_response = type('obj', (object,), {
                'content': f"테스트 응답: {messages[-1].get('content', '') if messages else '기본 응답'}"
            })()
            return {"messages": messages + [dummy_response]}
        
        try:
            response = self.llm.invoke(messages)
            return {"messages": messages + [response]}
        except Exception as e:
            error_response = type('obj', (object,), {
                'content': f"LLM 호출 오류: {str(e)}"
            })()
            return {"messages": messages + [error_response]}
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """도구 사용 여부 결정"""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        # 도구 호출이 있는지 확인
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        return "end"
    
    async def process_message(self, message: str, session_id: str = None) -> str:
        """메시지 처리"""
        try:
            if self.graph is None:
                return "에이전트가 초기화되지 않았습니다."
            
            # 상태 초기화
            initial_state = {
                "messages": [{"role": "user", "content": message}]
            }
            
            # 그래프 실행
            result = self.graph.invoke(initial_state)
            
            # 응답 추출
            messages = result.get("messages", [])
            if messages and hasattr(messages[-1], 'content'):
                return messages[-1].content
            
            return "죄송합니다. 응답을 생성할 수 없습니다."
            
        except Exception as e:
            return f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
    
    def add_tool(self, tool):
        """도구 추가"""
        self.tools.append(tool)
        self._setup_graph()  # 그래프 재설정 