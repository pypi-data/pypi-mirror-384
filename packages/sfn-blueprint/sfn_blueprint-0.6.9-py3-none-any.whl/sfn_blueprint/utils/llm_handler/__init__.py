from sfn_blueprint.utils.llm_handler.llm_clients import *
from sfn_blueprint.utils.logging import setup_logger
from sfn_blueprint.config.model_config import MODEL_CONFIG, SUPPORT_MESSAGE
from sfn_blueprint.utils.llm_response_formatter import llm_response_formatter, llm_response_formatter_langchain
# from sfn_llm_client.agent.agent_executor import call_agent
class SFNAIHandler:
    def __init__(self, logger_name="SFNAIHandler"):
        self.logger, _ = setup_logger(logger_name)
        self.client_map = {
            'openai': sfn_openai_client,
            'anthropic': sfn_anthropic_client,
            'cortex': sfn_cortex_client
        }
        self.client_map_langchain = {
            'openai': sfn_openai_client_langchain,
            'cortex': sfn_cortex_client_langchain
        }

    def route_to(self, llm_provider, configuration, model,db_url=None):
        """Routes requests to the appropriate LLM provider and send chat completion requests to LLM.
            :param configuration : dict
                A dictionary containing the following keys:
                - messages (mandatory): A list of dictionaries where each dictionary represents a message. 
                    Each message must contain a "role" (e.g., "system" or "user") and "content" (the message text).
                - temperature (optional): Controls the creativity of the responses. If not provided, 
                    the default value is 0.7.
                - max_tokens (optional): The maximum number of tokens to generate in the response. 
                    If not provided, the default value is 1000.

            :param model : str
                The Anthropic model to be used for generating the chat completion. This is a mandatory parameter.

            :return : 
                response : dict containing the generated text and other metadata.
                token_cost_summary : dict contains api cost
        """

        self.logger.info(f"Routing request to {llm_provider} using model {model}")
        
        if llm_provider not in self.client_map and llm_provider != 'cortex':
            self.logger.error(f"Unsupported LLM provider: {llm_provider} - {SUPPORT_MESSAGE}")
            return
        
        kwargs = {"model": model, **{k: configuration[k] for k in ("temperature", "max_tokens", "top_p", "text_format") if k in configuration}}
        if llm_provider == 'cortex':
            if not (session := get_snowflake_session(db_url)): raise Exception("Session not found")
            kwargs["session"] = session
            if "guardrails" in configuration: kwargs["guardrails"] = configuration["guardrails"]

        try:
            llm_client = self.client_map[llm_provider](model)
            response, token_cost_summary = llm_client.chat_completion(
                messages=configuration["messages"],
                **kwargs
            )

            self.logger.info(f"Received response from {llm_provider}: {response}")
            response = llm_response_formatter(response, llm_provider, self.logger)         
            return response, token_cost_summary
        except Exception as e:
            self.logger.error(f"Error while executing API call to {llm_provider}: {e}")
            raise

    def route_to_langchain(self, llm_provider, configuration, model, snowflake_session=None):
        self.logger.info(f"Routing request to {llm_provider} using model {model}")
        if llm_provider not in self.client_map_langchain and llm_provider != 'cortex':
            self.logger.error(f"Unsupported LLM provider: {llm_provider} - {SUPPORT_MESSAGE}")
            return

        model_config = MODEL_CONFIG['suggestions_generator'][llm_provider]
        session = None

        try:
            llm_client = self.client_map_langchain[llm_provider](model)
            response, token_cost_summary = llm_client.chat_completion(
                messages=configuration["messages"],
                temperature=configuration.get("temperature", model_config['temperature']),
                max_tokens=configuration.get("max_tokens", model_config['max_tokens']),
                model=model,
                retries=model_config['max_attempt'],
                retry_delay=model_config['retry_delay'],
                session=snowflake_session
            )

            self.logger.info(f"Received response from {llm_provider}: {response}")
            response = llm_response_formatter_langchain(response, llm_provider, self.logger)         
            return response, token_cost_summary
        except Exception as e:
            self.logger.error(f"Error while executing API call to {llm_provider}: {e}")
            raise

    # def route_to_agent(self, llm_provider, configuration, model, snowflake_session=None, tools=None):
    #     """
    #     Run an agentic/tool-calling workflow using LangChain.
    #     :param tools: list, optional, list of LangChain tool objects
    #     """
    #     self.logger.info(f"Routing request to {llm_provider} using model {model}")
    #     if llm_provider not in self.client_map_langchain and llm_provider != 'cortex':
    #         self.logger.error(f"Unsupported LLM provider: {llm_provider} - {SUPPORT_MESSAGE}")
    #         return

    #     model_config = MODEL_CONFIG['suggestions_generator'][llm_provider]
    #     try:
    #         llm_client = self.client_map_langchain[llm_provider](model)
    #         if llm_provider == 'cortex':
    #             llm_client = llm_client.get_langchain_llm(
    #                 model=model,
    #                 temperature=configuration.get("temperature", model_config['temperature']),
    #                 max_tokens=configuration.get("max_tokens", model_config['max_tokens']),
    #                 top_p=configuration.get("top_p", 1),
    #                 session=snowflake_session
    #             )
    #         elif llm_provider == 'openai':
    #             llm_client = llm_client.get_langchain_llm(
    #                 model=model,
    #                 temperature=configuration.get("temperature", model_config['temperature']),
    #                 max_tokens=configuration.get("max_tokens", model_config['max_tokens'])
    #             )
    #         response, token_cost_summary = call_agent(llm_client=llm_client, tools=tools, configuration=configuration)
    #         self.logger.info(f"Received response from {llm_provider}: {response}")
    #         return response, token_cost_summary
    #     except Exception as e:
    #         self.logger.error(f"Error while executing API call to {llm_provider}: {e}")
    #         raise

