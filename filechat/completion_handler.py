from . import utils, app_config

import openai, openai.types.chat, openai_streaming, typing, dotenv, os


dotenv.load_dotenv()

api_key = app_config.get("api_key", os.getenv("OPENAI_API_KEY"))
base_url = app_config.get("base_url", os.getenv("OPENAI_API_URL"))


async def content_handler_with_config(
    config: dict[str, typing.Any], content: typing.AsyncGenerator[str, None]
):
    first_token_received = False
    try:
        async for token in content:
            if not first_token_received:
                first_token_received = True
                for handler in config.get("stream_response_start_handlers", []):
                    handler()
            for handler in config.get("stream_response_token_handlers", []):
                handler(token)
    except:
        pass
    finally:
        for handler in config.get("stream_response_end_handlers", []):
            handler()


async def request_completion(
    messages: list[str], config: dict[str, typing.Any] = {}
) -> openai.types.chat.ChatCompletionMessage:
    async def content_handler(content: typing.AsyncGenerator[str, None]):
        await content_handler_with_config(config, content)

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

        response = await openai_streaming.process_response(
            response=response,
            content_func=content_handler,
        )
        return response[1]

    return await utils.try_loop_async(
        try_func,
        raise_on_retry_exceed=False,
        **{k: v for k, v in config.items() if k in {"max_retries"}},
    )
