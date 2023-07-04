import json

import tiktoken

from govtech_data.models import gptactions
from govtech_data.prompts.task import TASK_SYSTEM_PROMPT, KEYWORD_SUGGESTION_PROMPT
from govtech_data.utils import commands

try:
    import openai
except:
    raise Exception("openai module is not installed, you may need to install govtech-data[openai]")

import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if openai.api_key is None:
    raise Exception("OPENAI_API_KEY is not set! Set it as an environment variable with 'export OPENAI_API_KEY=xxx'")

OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4")
OPENAI_DEFAULT_TEMPERATURE = os.getenv("OPENAI_DEFAULT_TEMPERATURE", 0.0)
OPENAI_DEFAULT_MAX_NUMBER_OF_TOKENS = 4000

TOKEN_BUFFER = os.getenv("OPENAI_TOKEN_BUFFER", 500)
MAXIMUM_NUMBER_OF_TOKENS_KEY = "MAXIMUM_NUMBER_OF_TOKENS"

MODEL_CONFIGS = {
    "gpt-4-0314": {MAXIMUM_NUMBER_OF_TOKENS_KEY: 8000 - TOKEN_BUFFER},
    "gpt-4-0613": {MAXIMUM_NUMBER_OF_TOKENS_KEY: 8000 - TOKEN_BUFFER},
    "gpt-4": {MAXIMUM_NUMBER_OF_TOKENS_KEY: 8000 - TOKEN_BUFFER},
    "gpt-3.5-turbo-0301": {MAXIMUM_NUMBER_OF_TOKENS_KEY: OPENAI_DEFAULT_MAX_NUMBER_OF_TOKENS - TOKEN_BUFFER},
    "gpt-3.5-turbo-0613": {MAXIMUM_NUMBER_OF_TOKENS_KEY: OPENAI_DEFAULT_MAX_NUMBER_OF_TOKENS - TOKEN_BUFFER},
    "gpt-3.5-turbo": {MAXIMUM_NUMBER_OF_TOKENS_KEY: OPENAI_DEFAULT_MAX_NUMBER_OF_TOKENS - TOKEN_BUFFER},
    "gpt-3.5-turbo-16k-0613": {MAXIMUM_NUMBER_OF_TOKENS_KEY: 16000 - TOKEN_BUFFER},
    "gpt-3.5-turbo-16k": {MAXIMUM_NUMBER_OF_TOKENS_KEY: 16000 - TOKEN_BUFFER},
}


class OpenAIClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OpenAIClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.messages_history: list[dict[str, str]] = []
        self.last_response = None
        self.CIRCUIT_BREAKER_LIMIT = 15

    def query(
        self,
        query,
        functions=gptactions.LIST_OF_FUNCTIONS,
        model=OPENAI_DEFAULT_MODEL,
        depth=1,
        task_system_prompt=TASK_SYSTEM_PROMPT,
        role="user",
    ):
        if depth >= self.CIRCUIT_BREAKER_LIMIT:
            logger.error("circuit-breaker triggered to avoid an infinite query loop")
            return False

        if len(self.messages_history) == 0:
            self.messages_history.append(self.get_message("system", task_system_prompt))

        if query:
            message = self.get_message(role, query)
            logger.debug(f"Request:\n{message}")
            self.messages_history.append(message)

        responses = self.simple_query_openai(self.messages_history, functions=functions, model=model, n=1)

        if len(responses) == 0:
            return False

        raw_response = responses[0]

        self.last_response = raw_response

        try:
            finish_reason = raw_response.get("finish_reason", None)
            if finish_reason == "function_call":
                response = raw_response["message"]["function_call"]
                name, args = response["name"], json.loads(response["arguments"])
            else:
                response = raw_response["message"]
                self.messages_history.append(self.get_message("assistant", commands.json_dump(response)))
                return self.query(
                    "Please return a function call",
                    functions=functions,
                    model=model,
                    depth=depth + 1,
                    task_system_prompt=task_system_prompt,
                    role="system",
                )

            logger.debug(f"ChatGPT content response:\n{response}")
            self.messages_history.append(self.get_function_message(name, commands.json_dump(args)))
        except:
            logger.exception(f"response cannot be parsed! ChatGPT content response:\n{raw_response}")
            self.messages_history.append(self.get_message("assistant", commands.json_dump(raw_response)))
            return self.query(
                None,
                functions=functions,
                model=model,
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
            )

        if name == "dataset_search":
            ss_messages = [
                self.get_message("system", KEYWORD_SUGGESTION_PROMPT),
                # self.get_message("function", commands.json_dump(response)),
                self.get_function_message(
                    response["name"],
                    commands.json_dump(json.loads(response["arguments"])),
                ),
                self.get_message("user", args.get("input")),
            ]
            # logger.info(f"ss_messages: {ss_messages}")
            ss_responses = self.simple_query_openai(
                ss_messages,
                functions=gptactions.KEYWORD_PHRASES_FUNCTION,
                model=model,
                temperature=0.7,
                n=1,
            )

            ss_raw_response = ss_responses[0]

            try:
                ss_finish_reason = ss_raw_response.get("finish_reason", None)
                if ss_finish_reason == "function_call":
                    ss_response = ss_raw_response["message"]["function_call"]
                    ss_name, ss_args = ss_response["name"], json.loads(ss_response["arguments"])
                    logger.debug(f"ChatGPT ss_response_data:\n{ss_response}")
                    ss_thoughts, ss_phrases = ss_args.get("current_thoughts", {}).get("thoughts"), ss_args.get(
                        "phrases", []
                    )
                    return self.query(
                        commands.dataset_search_batch([args.get("input")] + ss_phrases),
                        functions=functions,
                        model=model,
                        depth=depth + 1,
                        task_system_prompt=task_system_prompt,
                        role="system",
                    )

            except:
                logger.exception(f"response cannot be parsed! ChatGPT content response:\n{ss_responses}")
                self.messages_history.append(self.get_message("assistant", ss_response))
                return self.query(
                    None,
                    functions=functions,
                    model=model,
                    depth=depth + 1,
                    task_system_prompt=task_system_prompt,
                )

        elif name == "get_dataset":
            return self.query(
                commands.get_dataset_schema(args.get("id")),
                functions=functions,
                model=model,
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
                role="system",
            )

        elif name == "get_dataset_schema":
            return self.query(
                commands.get_dataset_schema(args.get("id")),
                functions=functions,
                model=model,
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
                role="system",
            )

        elif name == "get_all_distinct_values_in_a_dataset_field":
            return self.query(
                commands.get_all_distinct_values_in_a_dataset_field(args.get("id"), args.get("field")),
                functions=functions,
                model=model,
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
                role="system",
            )

        elif name == "search_for_relevant_values_in_a_dataset_field":
            return self.query(
                commands.search_for_relevant_values_in_a_dataset_field(
                    args.get("id"), args.get("field"), args.get("value")
                ),
                functions=functions,
                model=model,
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
                role="system",
            )

        elif name == "do_nothing":
            return self.query(
                None,
                functions=functions,
                model=model,
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
                role="system",
            )

        elif name == "generate_full_code":
            return self.query(
                "Fix and optimize the following code",
                functions=functions,
                model=model,
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
                role="system",
            )

        elif name == "generate_optimized_code":
            return True

        elif name == "task_complete":
            return True

        return self.query(
            None,
            functions=functions,
            model=model,
            depth=depth + 1,
            task_system_prompt=task_system_prompt,
            role="system",
        )

    def query_plot(
        self,
        query,
        functions=gptactions.LIST_OF_FUNCTIONS,
        model=OPENAI_DEFAULT_MODEL,
        task_system_prompt=TASK_SYSTEM_PROMPT,
    ):
        resp = self.query(
            query,
            functions=functions,
            model=model,
            task_system_prompt=task_system_prompt,
            role="user",
        )
        logger.debug(f"query final response: {resp}")
        if resp:
            generated_code = self.get_generated_code_from_history()
            if generated_code:
                logger.debug(f"Code generated by AI\n{generated_code}")
                exec(generated_code)

    def get_generated_code_from_history(self) -> str:
        generated_code = None
        for message in reversed(self.messages_history):
            if "content" not in message:
                continue
            if message.get("role", "") != "function":
                continue
            try:
                if message.get("name", "") == "generate_optimized_code":
                    generated_code = json.loads(message.get("content", "{}")).get("code")
                if generated_code:
                    break
            except:
                continue
        return generated_code

    def messages_add(self, message: dict[str, str]):
        self.messages_history.append(message)

    def messages_length(self):
        return len(self.messages_history)

    def messages_num_tokens(self, model=OPENAI_DEFAULT_MODEL):
        return self.num_tokens_from_messages(self.messages_history, model)

    def messages_clear(self):
        self.messages_history = []

    def print_message_history(self):
        for i, message in enumerate(self.messages_history):
            logger.info(f"--- #{i} ---\n{message})")

    @classmethod
    def num_tokens_from_messages(cls, messages, model=OPENAI_DEFAULT_MODEL):
        """Returns the number of tokens used by a list of messages. - taken from openai-cookbook"""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in ("gpt-3.5-turbo"):
            logger.warning(
                "Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0613."
            )
            return cls.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
        elif model == "gpt-4":
            logger.warning("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0613.")
            return cls.num_tokens_from_messages(messages, model="gpt-4-0613")
        elif model in (
            "gpt-3.5-turbo-0301",
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
        ):
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif model in ("gpt-4-0314", "gpt-4-0613"):
            tokens_per_message = 3
            tokens_per_name = 1
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if not isinstance(value, str):
                    value = commands.json_dump(value)
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    @classmethod
    def simple_query_openai(
        cls,
        messages: list[dict],
        functions: list[dict],
        model=OPENAI_DEFAULT_MODEL,
        temperature=OPENAI_DEFAULT_TEMPERATURE,
        n=1,
    ) -> list[str]:
        use_messages = messages.copy()
        if n == 1:
            logger.debug(f"functions: \n{functions}")
        logger.debug(f"use_messages: \n{use_messages}")
        total_tokens = cls.num_tokens_from_messages(use_messages + functions, model)
        logger.debug(f"Total number of tokens in messages: {total_tokens}")
        if total_tokens >= MODEL_CONFIGS.get(model, {}).get(
            MAXIMUM_NUMBER_OF_TOKENS_KEY,
            OPENAI_DEFAULT_MAX_NUMBER_OF_TOKENS - TOKEN_BUFFER,
        ):
            logger.debug(f"  Need to remove an entry from the list of messages to reduce the number of tokens")
            while total_tokens >= MODEL_CONFIGS.get(model, {}).get(
                MAXIMUM_NUMBER_OF_TOKENS_KEY,
                OPENAI_DEFAULT_MAX_NUMBER_OF_TOKENS - TOKEN_BUFFER,
            ):
                del use_messages[2]
                total_tokens = cls.num_tokens_from_messages(use_messages + functions, model)
                logger.debug(f"  Total number of tokens in messages remaining: {total_tokens}")

        completion = cls.__query_openai(use_messages, functions, model, temperature, n)
        responses = []
        logger.debug(f"ChatGPT Completion Response:\n{completion}")
        for choice in completion.choices:
            responses.append(choice)
            # if "content" in choice.message:
            #     responses.append(choice.message["content"])
        return responses

    @classmethod
    def get_message(cls, role: str, content: str) -> dict[str, str]:
        return {"role": role, "content": content}

    @classmethod
    def get_function_message(cls, name: str, arguments: str) -> dict[str, str]:
        return {"role": "function", "name": name, "content": arguments}

    @classmethod
    def __query_openai(
        cls,
        messages: list[dict],
        functions: list[dict],
        model="gpt-3.5-turbo",
        temperature=OPENAI_DEFAULT_TEMPERATURE,
        n=1,
    ):
        if len(functions) == 0:
            return openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                n=n,
                stream=False,
            )
        return openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call="auto",
            temperature=temperature,
            n=n,
            stream=False,
        )
