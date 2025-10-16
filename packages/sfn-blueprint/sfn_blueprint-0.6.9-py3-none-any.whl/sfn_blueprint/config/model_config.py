
SFN_SUPPORTED_LLM_PROVIDERS = [
    "openai",
    "anthropic",
    "cortex"
]

SUPPORT_MESSAGE = f"""
We're currently not supporting this LLM provider. 
Please feel free to email us at - rajesh@stepfunction.ai 
with subject line - "SFNBLueprint Pip Package Query", 
and we'll work to enhance the package 
by adding support for this LLM agent in future updates.
"""

SUPPORT_MESSAGE_FOR_MODEL = f"""
We're currently not supporting this Model. 
Please feel free to email us at - rajesh@stepfunction.ai 
with subject line - "SFNBLueprint Pip Package Query", 
and we'll work to enhance the package 
by adding support for this Model in future updates.
"""

OPENAI_DEFAULTS = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000,
    "max_attempt": 3,
    "retry_delay": 3.0,
    "unsupported_model_msg": SUPPORT_MESSAGE_FOR_MODEL
}

ANTHROPIC_DEFAULTS = {
    "model":  "claude-3-5-sonnet-20240620",
    "temperature": 0.7,
    "max_tokens": 1000,
    "max_attempt": 2,
    "retry_delay": 3.0,
    "unsupported_model_msg": SUPPORT_MESSAGE_FOR_MODEL
}

CORTEX_DEFAULTS = {
    "model":  "snowflake-arctic",
    "temperature": 0.7,
    "max_tokens": 1000,
    "max_attempt": 2,
    "retry_delay": 3.0,
    "unsupported_model_msg": SUPPORT_MESSAGE_FOR_MODEL
}

COMMON_CONFIG = {
    "openai": {**OPENAI_DEFAULTS},
    "anthropic": {**ANTHROPIC_DEFAULTS},
    "cortex": {**CORTEX_DEFAULTS},
}

MODEL_CONFIG = {
    "code_generator": {
        "openai": {
            **OPENAI_DEFAULTS,
            "max_tokens": 500,
        },
        "anthropic": {
            **ANTHROPIC_DEFAULTS,
            "max_tokens": 500
        },
        "cortex":{
            **CORTEX_DEFAULTS,
            "max_tokens": 500
        }
    },
    "suggestions_generator": {
        **COMMON_CONFIG
    },
    "validator": {
        **COMMON_CONFIG
    }
}
