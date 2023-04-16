import tiktoken

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


class OpenAIClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OpenAIClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, *args, **kwargs):
        super(OpenAIClient, self).__init__(self, *args, **kwargs)
        self.messages_history: list[dict[str, str]] = []

    def messages_add(self, message: dict[str, str]):
        self.messages_history.append(message)

    def messages_length(self):
        return len(self.messages_history)

    def messages_num_tokens(self):
        return self.num_tokens_from_messages(self.messages_history)

    def messages_clear(self):
        self.messages_history = []

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
        cls, messages: list[dict], model="gpt-3.5-turbo", temperature=1.0, n=1
    ) -> list[dict[str, str]]:
        completion = cls.__query_openai(messages, model, temperature, n)
        responses = []
        for choice in completion.choices:
            logger.debug(f"ChatGPT response:\n{choice.message}")
            if "content" in choice.message:
                responses.append(choice.message["content"])
        return responses

    @classmethod
    def get_message(cls, role: str, content: str) -> dict[str, str]:
        return {"role": role, "content": content}

    @classmethod
    def __query_openai(
        cls, messages: list[dict], model="gpt-3.5-turbo", temperature=1.0, n=1
    ):
        return openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            n=n,
            stream=False,
        )
