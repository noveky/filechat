from . import utils, app_config

import openai, openai.types.chat, openai_streaming, typing, dotenv, os


dotenv.load_dotenv()

api_key = app_config.get("api_key", os.getenv("OPENAI_API_KEY"))
base_url = app_config.get("base_url", os.getenv("OPENAI_BASE_URL"))


async def stream_handler_with_config(
    config: dict[str, typing.Any], stream: typing.AsyncGenerator[str, None]
) -> str:
    first_token_received = False
    tokens = []
    async for token in stream:
        if not first_token_received:
            first_token_received = True
            for handler in config.get("stream_response_start_handlers", []):
                handler()
        for handler in config.get("stream_response_token_handlers", []):
            handler(token)
        tokens.append(token)
    for handler in config.get("stream_response_end_handlers", []):
        handler()
    return "".join(tokens)


async def request_completion(
    messages: list[str], config: dict[str, typing.Any] = {}
) -> str:
    async def stream_handler(stream: typing.AsyncGenerator[str, None]):
        return await stream_handler_with_config(config, stream)

    client = openai.AsyncOpenAI(
        api_key=config.get("api_key", api_key),
        base_url=config.get("base_url", base_url),
    )

    async def try_func():
        response = await client.chat.completions.create(
            messages=messages,
            stream=True,
            **{
                k: v
                for k, v in config.items()
                if k in {"model", "temperature", "max_tokens"}
            },
        )

        stream = (
            chunk.choices[0].delta.content
            async for chunk in response
            if chunk.choices and chunk.choices[0].delta.content is not None
        )
        return await stream_handler(stream)

    return await utils.try_loop_async(
        try_func,
        raise_on_retry_exceed=False,
        **{k: v for k, v in config.items() if k in {"max_retries"}},
    )
