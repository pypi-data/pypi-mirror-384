from logging import Logger
from typing import Literal,  Optional
from pydantic import BaseModel
from langgraph.types import Checkpointer
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import END, START, StateGraph, MessagesState
from langchain_core.runnables.fallbacks import RunnableWithFallbacks
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from sfn_blueprint.schema.schema import MultiAgentConfig, ReflectionState, CritiqueStructureOutput, ReflectionPromptTemplates
from sfn_llm_client import  load_model

from langchain_core.output_parsers import PydanticOutputParser
from sfn_blueprint.prompts.prompt_template import ReflectionPromptTemplates
def create_reflection_agent(
        config: MultiAgentConfig,
        logger: Logger,
        templates: ReflectionPromptTemplates,
        output_structure: BaseModel,
        checkpointer: Optional[Checkpointer] = None,
        store: Optional[BaseStore] = None,
        debug: bool = False,

    ) -> CompiledStateGraph:
    
    reflector_llm = load_model(config.reflector)
    critique_llm = load_model(config.critique)

    # parser = PydanticOutputParser(pydantic_object=Critique)  # if you added snow flake model with fall back the you added this else not need without fallback snowflex it works
    # structured_critique_llm = critique_llm | parser
    structured_critique_llm = critique_llm.with_structured_output(CritiqueStructureOutput)
    structured_reflector_llm = reflector_llm.with_structured_output(output_structure)

    def generate_initial_response(state: ReflectionState, config: RunnableConfig) -> ReflectionState:
        # logger.info("--- GENERATING INITIAL RESPONSE ---")
        system_prompt, user_prompt = templates.format_initial(**state.user_query)

        response = structured_reflector_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ],
                {"metadata": {"custom_session": config["configurable"]["custom_session"]}}
        )

        ai_message = AIMessage(content=response.model_dump_json())
        return { "current_response": response, "messages": [ai_message] }

    def critique_response(state: ReflectionState, config: RunnableConfig) -> ReflectionState:

        # logger.info("--- CRITIQUING RESPONSE ---")
        system_prompt, user_prompt = templates.format_critique(assistant_response = state.current_response.model_dump())
        critique_result = structured_critique_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ],
                {"metadata": {"custom_session": config["configurable"]["custom_session"]}}
        )
        # logger.info(f"Critique Score: {critique_result.score}, Sufficient: {critique_result.is_sufficient}")
        
        critique_message = AIMessage(
            content=f"Critique: {critique_result.critique}",
            name="critic"
        )
        return {"critique": critique_result, "messages": [critique_message]}
    
    def reflect_and_refine(state: ReflectionState, config: RunnableConfig) -> ReflectionState:
        # logger.info("--- REFLECTING AND REFINING ---")
        system_prompt, user_prompt = templates.format_refine(previous_response=state.current_response.model_dump(), critique=state.critique.critique )
        
        response = structured_reflector_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
                ],
                {"metadata": {"custom_session": config["configurable"]["custom_session"]}}
        )
        ai_message = AIMessage(content=response.model_dump_json())
        return { "current_response": response, "reflections_count": state.reflections_count + 1, "messages": [ai_message] }
    
    def should_reflect(state: ReflectionState) -> Literal["reflect_and_refine", END]:
        # logger.info("--- CHECKING REFLECTION CONDITION ---")
        
        if state.critique.is_sufficient:
            # logger.info("--- RESPONSE IS SUFFICIENT ---")
            return END
        if state.reflections_count >= state.max_reflections:
            # logger.info("--- MAX REFLECTIONS REACHED ---")
            return END
        # logger.info("--- RESPONSE NEEDS REFINEMENT ---")
        return "reflect_and_refine"
    
    graph = StateGraph(ReflectionState)
    graph.add_node("generate_initial_response", generate_initial_response)
    graph.add_node("critique_response", critique_response)
    graph.add_node("reflect_and_refine", reflect_and_refine)

    graph.add_edge(START, "generate_initial_response")
    graph.add_edge("generate_initial_response", "critique_response")
    graph.add_edge("reflect_and_refine", "critique_response")

    graph.add_conditional_edges(
        "critique_response",
        should_reflect,
        {
            "reflect_and_refine": "reflect_and_refine",
            END: END,
        },
    )

    return graph.compile(
        checkpointer=checkpointer,
        store=store,
        debug=debug
    )



    

    

