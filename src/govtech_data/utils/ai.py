try:
    import openai
except:
    raise Exception(
        "openai module is not installed, you may need to install govtech-data[openai]"
    )

import os

from loguru import logger

openai.api_key = os.getenv("OPENAI_API_KEY")

if openai.api_key is None:
    raise Exception(
        "OPENAI_API_KEY is not set! Set it as an environment variable with 'export OPENAI_API_KEY=xxx'"
    )


def simple_query_openai(
    messages: list[dict], model="gpt-3.5-turbo", temperature=1.0, n=1
):
    completion = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        n=n,
        stream=False,
    )
    responses = []
    for choice in completion.choices:
        logger.debug(f"ChatGPT response:\n{choice.message}")
        if "content" in choice.message:
            responses.append(choice.message["content"])
    return responses
