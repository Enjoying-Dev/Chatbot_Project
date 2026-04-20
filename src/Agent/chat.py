from typing import List, Dict
from langgraph.graph import StateGraph, START, END

from src.Agent.graph.graph_state import GraphState
from src.Agent.graph.graph_nodes import (
    route_query,
    route_after_router,
    route_after_mysql,
    mysql_retrieval_node,
    vector_retrieval_node,
    respond_node,
)


class ChatService:
    def __init__(self):
        self.graph = self._build_graph()

    @staticmethod
    def _build_graph():
        workflow = StateGraph(state_schema=GraphState)

        workflow.add_node("route_query", route_query)
        workflow.add_node("mysql_retrieval", mysql_retrieval_node)
        workflow.add_node("vector_retrieval", vector_retrieval_node)
        workflow.add_node("respond", respond_node)

        workflow.add_edge(START, "route_query")

        workflow.add_conditional_edges(
            "route_query",
            route_after_router,
            {
                "mysql_retrieval": "mysql_retrieval",
                "vector_retrieval": "vector_retrieval",
            },
        )

        workflow.add_conditional_edges(
            "mysql_retrieval",
            route_after_mysql,
            {
                "vector_retrieval": "vector_retrieval",
                "respond": "respond",
            },
        )

        workflow.add_edge("vector_retrieval", "respond")
        workflow.add_edge("respond", END)

        return workflow.compile()

    def process_message(self, query: str, conversation_history: List[Dict[str, str]]) -> dict:
        messages = conversation_history + [{"role": "user", "content": query}]
        initial_state = GraphState(messages=messages, query=query)
        final_state = self.graph.invoke(initial_state)
        return {
            "response": final_state["messages"][-1]["content"],
            "context": final_state.get("context") or "",
            "database": (
                final_state.get("database").value
                if final_state.get("database") is not None
                else None
            ),
            "routing_reason": final_state.get("routing_reason"),
            "fallback_used": final_state.get("fallback_used"),
            "sql_query": final_state.get("sql_query"),
        }


chat_service = ChatService()
