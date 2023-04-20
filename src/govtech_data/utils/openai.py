import json

import tiktoken

from govtech_data.prompts.task import TASK_SYSTEM_PROMPT, KEYWORD_SUGGESTION_PROMPT
from govtech_data.utils import commands

try:
    import openai
except:
    raise Exception(
        "openai module is not installed, you may need to install govtech-data[openai]"
    )

import os

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if openai.api_key is None:
    raise Exception(
        "OPENAI_API_KEY is not set! Set it as an environment variable with 'export OPENAI_API_KEY=xxx'"
    )

DEFAULT_TEMPERATURE = 0.0
MAXIMUM_NUMBER_OF_TOKENS = 3500


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

    def query(self, query, depth=1, task_system_prompt=TASK_SYSTEM_PROMPT):
        if depth >= self.CIRCUIT_BREAKER_LIMIT:
            logger.error("circuit-breaker triggered to avoid an infinite query loop")
            return False

        if len(self.messages_history) == 0:
            self.messages_history.append(self.get_message("system", task_system_prompt))

        if query:
            message = self.get_message("user", query)
            logger.debug(f"Request:\n{message}")
            self.messages_history.append(message)

        responses = self.simple_query_openai(self.messages_history, n=1)

        if len(responses) == 0:
            return False

        response = responses[0]

        self.last_response = response

        try:
            response_data = json.loads(response, strict=False)
            logger.debug(f"ChatGPT content response:\n{response_data}")
            self.messages_history.append(
                self.get_message("assistant", commands.json_dumps(response_data))
            )
        except:
            logger.error(
                f"response cannot be parsed! ChatGPT content response:\n{response}"
            )
            self.messages_history.append(self.get_message("assistant", response))
            return self.query(
                None, depth=depth + 1, task_system_prompt=task_system_prompt
            )

        command = response_data.get("command", {})
        name, args = command.get("name"), command.get("args")

        if name == "dataset_search":
            ss_messages = [
                self.get_message("system", KEYWORD_SUGGESTION_PROMPT),
                self.get_message("user", args.get("input")),
            ]
            logger.info(f"ss_messages: {ss_messages}")
            ss_responses = self.simple_query_openai(ss_messages, temperature=0.7, n=1)
            ss_response_data = json.loads(ss_responses[0], strict=False)
            logger.debug(f"ChatGPT ss_response_data:\n{ss_response_data}")
            ss_thoughts, ss_phrases = ss_response_data.get(
                "thoughts"
            ), ss_response_data.get("phrases")
            return self.query(
                commands.dataset_search_batch([args.get("input")] + ss_phrases),
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
            )
            # return self.query(
            #     commands.dataset_search(args.get("input")),
            #     depth=depth + 1,
            #     task_system_prompt=task_system_prompt,
            # )

        elif name == "get_dataset":
            return self.query(
                commands.get_dataset_schema(args.get("id")),
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
            )

        elif name == "get_dataset_schema":
            return self.query(
                commands.get_dataset_schema(args.get("id")),
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
            )

        elif name == "get_all_distinct_values_in_a_dataset_field":
            return self.query(
                commands.get_all_distinct_values_in_a_dataset_field(
                    args.get("id"), args.get("field")
                ),
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
            )

        elif name == "search_for_relevant_values_in_a_dataset_field":
            return self.query(
                commands.search_for_relevant_values_in_a_dataset_field(
                    args.get("id"), args.get("field"), args.get("value")
                ),
                depth=depth + 1,
                task_system_prompt=task_system_prompt,
            )

        elif name == "do_nothing":
            return self.query(
                None, depth=depth + 1, task_system_prompt=task_system_prompt
            )

        elif name == "evaluate_full_code":
            return True

        elif name == "task_complete":
            return True

        return self.query(None, depth=depth + 1, task_system_prompt=task_system_prompt)

    def query_plot(self, query, task_system_prompt=TASK_SYSTEM_PROMPT):
        resp = self.query(query, task_system_prompt=task_system_prompt)
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
            try:
                last_message_content = json.loads(message["content"])
            except:
                continue
            if (
                last_message_content.get("command", {}).get("name", "")
                == "evaluate_full_code"
            ):
                generated_code = (
                    last_message_content.get("command", {}).get("args", {}).get("code")
                )
            if generated_code:
                break
        return generated_code

    def messages_add(self, message: dict[str, str]):
        self.messages_history.append(message)

    def messages_length(self):
        return len(self.messages_history)

    def messages_num_tokens(self):
        return self.num_tokens_from_messages(self.messages_history)

    def messages_clear(self):
        self.messages_history = []

    def print_message_history(self):
        for message in self.messages_history:
            logger.info(f"\n{message})")

    @classmethod
    def num_tokens_from_messages(cls, messages, model="gpt-3.5-turbo"):
        """Returns the number of tokens used by a list of messages. - taken from openai-cookbook"""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model == "gpt-3.5-turbo":
            logger.warning(
                "Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301."
            )
            return cls.num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
        elif model == "gpt-4":
            logger.warning(
                "Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314."
            )
            return cls.num_tokens_from_messages(messages, model="gpt-4-0314")
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = (
                4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            )
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif model == "gpt-4-0314":
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
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    @classmethod
    def simple_query_openai(
        cls,
        messages: list[dict],
        model="gpt-3.5-turbo",
        temperature=DEFAULT_TEMPERATURE,
        n=1,
    ) -> list[str]:
        use_messages = messages.copy()
        use_messages_total_tokens = cls.num_tokens_from_messages(use_messages, model)
        logger.debug(f"Total number of tokens in messages: {use_messages_total_tokens}")
        if use_messages_total_tokens >= MAXIMUM_NUMBER_OF_TOKENS:
            logger.debug(
                f"  Need to remove an entry from the list of messages to reduce the number of tokens"
            )
            while use_messages_total_tokens >= MAXIMUM_NUMBER_OF_TOKENS:
                del use_messages[2]
                use_messages_total_tokens = cls.num_tokens_from_messages(
                    use_messages, model
                )
                logger.debug(
                    f"  Total number of tokens in messages remaining: {use_messages_total_tokens}"
                )

        completion = cls.__query_openai(use_messages, model, temperature, n)
        responses = []
        logger.debug(f"ChatGPT Completion Response:\n{completion}")
        for choice in completion.choices:
            if "content" in choice.message:
                responses.append(choice.message["content"])
        return responses

    @classmethod
    def get_message(cls, role: str, content: str) -> dict[str, str]:
        return {"role": role, "content": content}

    @classmethod
    def __query_openai(
        cls,
        messages: list[dict],
        model="gpt-3.5-turbo",
        temperature=DEFAULT_TEMPERATURE,
        n=1,
    ):
        return openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            n=n,
            stream=False,
        )
