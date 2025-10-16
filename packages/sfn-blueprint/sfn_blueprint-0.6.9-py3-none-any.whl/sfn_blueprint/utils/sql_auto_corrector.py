# https://aistudio.google.com/prompts/1fPqpnvpZio1YNKYJP_Pvl7AnZBtMdftm

from __future__ import annotations
from typing import Any, List, Tuple, Dict

import os
import contextlib
from collections import namedtuple
from typing import Callable, Literal
from sfn_blueprint.utils.llm_handler import SFNAIHandler
from sfn_blueprint.utils.llm_handler.llm_clients import get_snowflake_session
class ContextVar:
    _cache: Dict[str, 'ContextVar'] = {}
    def __init__(self, key, default_value):
        self.value = type(default_value)(os.getenv(key, default_value))
        self.key = key
        ContextVar._cache[key] = self
    def __bool__(self): return bool(self.value)

@contextlib.contextmanager
def Context(**kwargs):
    old_context = {k: v.value for k, v in ContextVar._cache.items()}
    for k, v in kwargs.items():
        if k in ContextVar._cache:
            ContextVar._cache[k].value = v
    try:
        yield
    finally:
        for k, v in old_context.items():
            ContextVar._cache[k].value = v


def fetch_data(session: Any, query: str, mode: str = "cursor") -> List[Tuple]:
    return (session.sql(query).collect() if mode == "snowpark" else (lambda cur: cur.fetchall() if cur.description else [])(session.cursor().__enter__().__class__(session.cursor()).__enter__()))

def check_sql(session: Any, query: str, mode: str = "cursor") -> None:
    (session.sql(f"EXPLAIN {query}").collect() if mode == "snowpark"else session.cursor().__enter__().execute(f"EXPLAIN {query}"))
    
def _clean_ai_response(response: str) -> str:
    return response.replace("```sql", "").replace("```", "").strip()

DialectHandler = namedtuple('DialectHandler', ['validator', 'executor', 'recover_on_error'])

DEBUG = ContextVar("DEBUG", 0)
AI_PROVIDER = ContextVar("AI_PROVIDER", "openai")
AI_MODEL = ContextVar("AI_MODEL", "gpt-4o")
AI_TEMPERATURE = ContextVar("AI_TEMPERATURE", 0.3)
AI_MAX_TOKENS = ContextVar("AI_MAX_TOKENS", 1024)
DIALECT_HANDLERS: dict[str, DialectHandler] = {
    "postgres": DialectHandler(validator=check_sql, executor=fetch_data, recover_on_error=lambda sess: sess.rollback()),
    "snowflake": DialectHandler(validator=check_sql, executor=fetch_data, recover_on_error=lambda sess: None ),
    "snowpark": DialectHandler(validator=check_sql, executor=fetch_data, recover_on_error=lambda sess: None )
}

def _get_prompts(dialect: str, context: str, failed_query: str, instructions: str | None, error: str, history: list[tuple[str, str]]) -> tuple[str, str]:
    """Generates the system and user prompts for the AI corrector."""
    system_prompt = """You are an advanced, AI-powered SQL query correction engine. Your sole purpose is to receive a failed SQL query along with its execution context and error message, and return a syntactically correct and logically sound version of that query. You are an expert in multiple SQL dialects, including but not limited to PostgreSQL, Snowflake, and SQLite.

**Your Directives are Absolute:**

1.  **Analyze the Full Context:** You will be given key pieces of information: the SQL dialect, the schema context, the user's failed query, any special instructions, and the exact error message from the database during a syntax check (EXPLAIN) or live execution. **You may also be provided with a `Correction History` of previous failed attempts. You MUST analyze this history to understand what has already been tried and why it failed, to avoid repeating mistakes.**

2.  **Preserve Original Intent:** Your primary and most critical goal is to fix the query while **perfectly preserving the user's original intent**. You must not add, remove, or alter the logic or the ultimate goal of the query. You are a debugger, not a re-writer. For example, if a user's `JOIN` is wrong, fix the `JOIN` condition; do not change it to a `UNION`.

3.  **Focus on the Error:** The provided error message is your primary clue. Use it to identify the root cause of the failure, such as a syntax error, a non-existent column name, a type mismatch, or an incorrect function name for the specified SQL dialect.

4.  **Strict Output Format:** Your response MUST be **only the corrected SQL query** and nothing else.
    -   DO NOT include any explanations, greetings, apologies, or conversational text.
    -   DO NOT wrap the query in Markdown code fences (e.g., ```sql).
    -   DO NOT add comments to the SQL code unless they were part of the original query.

5.  **Failure Condition:** If the error cannot be fixed without violating the "Preserve Original Intent" directive, or if the user's instructions are contradictory or ambiguous, you MUST return the original, unmodified query. This is your safety mechanism to prevent logical corruption."""
    history_text = ""
    if history:
        history_text += "\n\n### Correction History\nThis is a record of previous attempts that have failed. Use this to avoid repeating mistakes.\n"
        for i, (attempted_query, error_message) in enumerate(history):
            history_text += f"\n**Attempt {i + 1}:**\n**Query:**\n```sql\n{attempted_query}\n```\n**Resulting Error:**\n```{error_message}```\n"

    user_prompt = f"### Dialect\n{dialect}\n\n### Context\n{context}{history_text}\n\n### Original Query\n```sql\n{failed_query}\n```\n"
    if instructions: user_prompt += f"\n### Special Instructions\n{instructions}"
    user_prompt += f"\n### Error Message\n{error}"
    return system_prompt, user_prompt

def self_correcting_sql(
    session: any, sql_query: str, dialect: Literal["postgres", "snowflake", "snowpark"],
    context: str, max_retries: int = 3, special_instructions: str | None = None,
    execute: bool = False
) -> tuple[bool, str, list | None, str]:
    
    ai_handler = SFNAIHandler()
    handler = DIALECT_HANDLERS.get(dialect) 
    if not handler:
        if DEBUG: print(f"Unsupported dialect: {dialect}")
        return False, sql_query, None, "Unsupported SQL database"
    if not (session := session or get_snowflake_session()):
        if DEBUG: print("Failed to obtain a Snowflake database session. Please check your connection or credentials.")
        return False, sql_query, None, "Failed to obtain a Snowflake database session. Please check your connection or credentials."

    action_to_perform = handler.executor if execute else handler.validator
    last_query = sql_query
    history: list[tuple[str, str]] = []
    for attempt in range(max_retries):
        try:
            result = action_to_perform(session, last_query, dialect)
            if DEBUG: print(f"Query {'Executed' if execute else 'Validated'} successfully.")
            return True, last_query, result if execute else None, "Operation completed successfully"
        except Exception as e:
            if DEBUG: print(f"\nValidation failed (Attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1: break
            handler.recover_on_error(session)
            system_prompt, user_prompt = _get_prompts(dialect, context, last_query, special_instructions, str(e), history)
            response, _ = ai_handler.route_to(
                AI_PROVIDER.value,
                configuration={
                    "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    "max_tokens": AI_MAX_TOKENS.value,
                    "temperature": AI_TEMPERATURE.value,
                },
                model=AI_MODEL.value)
            last_query = _clean_ai_response(response)
            history.append((last_query, str(e)))
            if DEBUG: print(f"\nAI suggested correction:\n-----\n{last_query}\n-----")

    if DEBUG: print(f"Failed to correct query after {max_retries} retries.")
    return False, sql_query, None, "Failed to correct query after maximum LLM retries"
