from logging import Logger
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.types import Checkpointer
from sfn_blueprint.schema.schema import  ChatState
from sfn_llm_client import load_model, LLMConfig
from langgraph.graph.state import CompiledStateGraph
def create_chat_agent(
        user_prompt: str,
        system_prompt: str,
        config: LLMConfig,
        logger: Logger,
        checkpointer: Optional[Checkpointer] = None
) -> CompiledStateGraph:
      
    llm = load_model(config)

    def call_chat(state: ChatState):
        logger.info("--- CALLING CHAT AGENT ---")
        response = llm.invoke(
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=user_prompt.format(state.user_query)
            )
        )
        return {"messages": response, "output_message":response.content}

    graph = StateGraph(ChatState)

    graph.add_node("call_chat", call_chat)
    
    graph.set_entry_point("call_chat")
    graph.add_edge("call_chat", END)
    return graph.compile(checkpointer=checkpointer)