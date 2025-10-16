
import logging
from uuid import uuid4
from pathlib import Path
from inspect import isclass
from datetime import datetime
from string import Formatter
from pydantic import BaseModel
from typing import Optional, List, Set, Dict, Tuple, Any, Literal, Union, Type

import mlflow
from langgraph.types import Checkpointer
from langgraph.store.base import BaseStore
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langchain.callbacks.base import BaseCallbackHandler
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from sfn_llm_client import CostCallbackHandler, LLMConfig

from sfn_blueprint.utils.logging import setup_logger
from sfn_blueprint.schema.schema import MultiAgentConfig
from sfn_blueprint.graph.chat_graph import create_chat_agent
from sfn_blueprint.graph.reflection_graph import create_reflection_agent
from sfn_blueprint.utils.langgraph_logging import ConfigurableLoggingHandler
from sfn_blueprint.prompts.prompt_template import ReflectionPromptTemplates, fmt_msg


class LangGraphAgent:
    """Manages the LangGraph Agent/workflow and interactions with the LLM.
    """

    def __init__(
            self, 
            config: RunnableConfig, 
            required_agents: Literal["reflection", "chat"],
            connection:  Optional[Union[str, Any]] = None,
            store: Optional[BaseStore] = None,
            debug: bool = False,
            loggings: Optional[Tuple[logging.Logger, logging.Handler]] = None,
    ):
        
        self._logger, _ = loggings or setup_logger("LangGraphAgent")
        if  required_agents == "chat":
            self._config = LLMConfig(config["configurable"])
        elif required_agents == "reflection":
            self._config = MultiAgentConfig.from_runnable_config(
                runnable_settings=config, 
                required_agents=["critique", "reflector"],
            )
        else:
            raise ValueError(
                f"Invalid value for required_agents: {required_agents!r}. Expected 'chat' or 'reflection'.")

        self._cost_callback = CostCallbackHandler(logger=self._logger)
        self._logger_callback = ConfigurableLoggingHandler(
            logger=self._logger,
            log_level=logging.INFO
        )
        self._logger_callback.raise_error = False
        self._callbacks: List[BaseCallbackHandler] = [
            self._cost_callback,
            self._logger_callback
        ]

        self._mlflow_current_date: Optional[str] = None
        # self._update_mlflow_tracking_uri_if_needed()

        self._checkpointer = self._get_checkpointer(connection) if connection else None
        self._store = store
        self._debug = debug

        self._graph_reflection: Optional[CompiledStateGraph] = None
        self._graph_chat: Optional[CompiledStateGraph] = None

    def _get_checkpointer(
            self,
            connection: Optional[Union[str, Any]] = None,
        ) -> BaseCheckpointSaver:
        serde = JsonPlusSerializer(pickle_fallback=True)
        if connection == "in_memory":
            msg = fmt_msg( "In memory checkpointer is not recommended for production use.",  "engine/checkpointer", color="yellow")
            self._logger.warning(msg)
            return MemorySaver(serde=serde)

        if isinstance(connection, str):
            if connection.startswith("postgresql"):
                from langgraph.checkpoint.postgres import PostgresSaver
                checkpointer = PostgresSaver.from_conn_string(connection, serde=serde)
                checkpointer.setup()
                msg = fmt_msg("Postgres connection string used to save checkpointer.",  "engine/checkpointer")
                self._logger.info(msg)
                return checkpointer
            else:
                from langgraph.checkpoint.sqlite import SqliteSaver
                msg = fmt_msg("Sqlite  connection string used to save checkpointer.",  "engine/checkpointer")
                self._logger.info(msg)
                return SqliteSaver.from_conn_string(connection, serde=serde)

        try:
            import sqlite3
            is_sqlite_conn = isinstance(connection, sqlite3.Connection)
        except ImportError:
            is_sqlite_conn = False

        if is_sqlite_conn:

            from langgraph.checkpoint.sqlite import SqliteSaver
            msg = fmt_msg("Sqlite connection object used to save checkpointer.",  "engine/checkpointer")
            self._logger.info(msg)
            return SqliteSaver(conn=connection, serde=serde)
        
        try:
            # psycopg2 is the underlying library used by the postgres checkpointer
            from psycopg2.extensions import connection as psycopg2_connection
            is_postgres_conn = isinstance(connection, psycopg2_connection)
        except ImportError:
            is_postgres_conn = False
            
        if is_postgres_conn:
            
            from langgraph.checkpoint.postgres import PostgresSaver
            checkpointer = PostgresSaver(conn=connection, serde=serde)
            checkpointer.setup()
            msg = fmt_msg("Postgres connection object used to save checkpointer.",  "engine/checkpointer")
            self._logger.info(msg)
            return checkpointer
        
        msg = fmt_msg("Unsupported connection type.",  "engine/checkpointer", color="red")
        self._logger.error(msg)
        raise TypeError(
            f"Unsupported connection type: {type(connection)}. "
            "Expected None, a string (PostgreSQL URI or SQLite path), "
            "a sqlite3.Connection object, or a psycopg2 connection object."
        )
    
    def _update_mlflow_tracking_uri_if_needed(self):
        today_str = datetime.now().strftime("%Y_%m_%d")
        
        if self._mlflow_current_date != today_str:
            log_path = Path(f"./mlruns_daily/{today_str}")
            log_path.mkdir(parents=True, exist_ok=True)
            
            mlflow.set_tracking_uri(f"file:///{log_path.absolute()}")
            mlflow.set_experiment("reflection_chat")
            mlflow.langchain.autolog()
            self._mlflow_current_date = today_str
            
            msg = fmt_msg(f"MLflow tracking URI has been set/updated to daily path: {log_path.absolute()}", "engine/mlflow")
            self._logger.info(msg)



    def build_reflection(
            self,
            initial_user_prompt: str,
            initial_system_prompt: str,
            critique_user_prompt: str,
            critique_system_prompt: str,
            reflector_user_prompt: str,
            reflector_system_prompt: str,
            ouput_structure: Type[BaseModel]
    ):
        
        if not  issubclass(ouput_structure, BaseModel):
            msg = fmt_msg("Reflection graph: output_structure must be a pydantic BaseModel class", "engine/build_reflection", color="red")
            self._logger.error(msg)
            raise ValueError(msg)

        templates = ReflectionPromptTemplates(
            initial_system_prompt=initial_system_prompt,
            initial_user_prompt=initial_user_prompt,
            critique_system_prompt=critique_system_prompt,
            critique_user_prompt=critique_user_prompt,
            refine_system_prompt=reflector_system_prompt,
            refine_user_prompt=reflector_user_prompt,
                )

        self._graph_reflection = create_reflection_agent(
        config=self._config,
        logger=self._logger,
        templates=templates,
        output_structure=ouput_structure,
        checkpointer=self._checkpointer,
        store=self._store,
        debug=self._debug
        )
        msg = fmt_msg("Reflection graph build done", "engine/build_reflection")
        self._logger.info(msg)
        
        return self._graph_reflection
    
    def build_chat(
            self,
            user_prompt: str,
            system_prompt: str
    ):
        self._graph_chat = create_chat_agent(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            config=self._config,
            logger=self._logger,
            checkpointer=self._checkpointer,
        )
        msg = fmt_msg("chat graph build done", "engine/build_chat")
        self._logger.info(msg)

    def invoke(
        self, 
        user_query: Dict[str, Any],
        agent_type: Literal["reflection", "chat"],
        max_reflections:int = 3,
        thread_id: Optional[str] = None,
        session: Optional[str] = None,
        tracing = False
        ):

        if tracing: 
            self._update_mlflow_tracking_uri_if_needed()
        current_thread_id = thread_id or f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}_{uuid4().hex[:10]}"

        running_config = RunnableConfig(
            configurable={"thread_id": current_thread_id, "custom_session": session},
            callbacks = self._callbacks, 
        )
        
        if self._graph_reflection is not None and agent_type == "reflection":
            msg = fmt_msg("reflection graph is invoke", "engine/invoke")
            self._logger.info(msg)
            input_graph = {"user_query": user_query, "max_reflections": max_reflections}
            result = self._graph_reflection.invoke(input_graph, running_config)
            return result.get("current_response", [])

        if self._graph_chat is not None and agent_type == "chat":
            msg = fmt_msg("chat graph is invoke", "engine/invoke")
            self._logger.info(msg)
            input_graph = {"user_query": user_query}
            result = self._graph_chat.invoke(input_graph, running_config)
            return result.get("output_message", [])

        msg = fmt_msg("No graph is present please build graph first", "engine/invoke", color="red")
        self._logger.error(msg)
        return None
    


    def reset_cost(self):
        self._cost_callback.reset()

    def get_cost_metrics(self) -> Dict[str, Union[int, float]]:
        return {
            "total_tokens": self._cost_callback.total_tokens,
            "prompt_tokens": self._cost_callback.prompt_tokens,
            "completion_tokens": self._cost_callback.completion_tokens,
            "cache_tokens": 0,
            "reasoning_tokens": 0,
            "guardrails_tokens": self._cost_callback.guardrails_tokens,
            "successful_requests": self._cost_callback.successful_requests,
            "total_cost": self._cost_callback.total_cost,
        }




