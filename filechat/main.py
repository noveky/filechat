from . import completion_handler, file_operations, utils, app_config

import sys, asyncio
from termcolor import colored


print_response = app_config.get("print_response", True)
stream_for_file = app_config.get("stream_for_file", True)
model = app_config.get("model", None)
temperature = app_config.get("temperature", None)


async def main():
    try:
        # Validate command-line arguments
        if len(sys.argv) != 2:
            raise ValueError("Invalid number of arguments. Expected a file path.")
        file_path = sys.argv[1]  # Get the file path from command-line arguments

        # Initialize configurations
        config = {
            "model": model,
            "temperature": temperature,
            "print_response": print_response,
            "stream_for_file": stream_for_file,
        }

        # Format the file for a consistent style
        file_operations.format_file(file_path)

        # Parse the input file to retrieve configuration overrides and messages
        config_overrides, messages = file_operations.parse_file(file_path)
        config.update(config_overrides)
        print(colored(f"Configuration: {config}", "green"))

        messages_to_remove = 0

        def remove_trailing_messages():
            nonlocal messages_to_remove
            while messages_to_remove > 0:
                file_operations.remove_last_message_from_file(
                    file_path, match_roles={"user", "assistant"}
                )
                messages_to_remove -= 1

        # Remove any trailing empty messages
        while (
            len(messages) > 0
            and "content" in messages[-1]
            and str(messages[-1]["content"]).strip() == ""
        ):
            messages_to_remove += 1
            messages.pop()
        remove_trailing_messages()

        # Check if the last message is an assistant message
        if len(messages) == 0:
            raise ValueError("Expected user message.")
        elif messages[-1]["role"] == "assistant":
            utils.log_warning("The last message is an assistant message.")
            if utils.ask_yes_no("Replace it?", default=False):
                messages_to_remove += 1
                messages.pop()

        stream_response_start_handlers = []
        stream_response_token_handlers = []
        stream_response_end_handlers = []

        # Set up stream response handlers
        if print_response:
            stream_response_token_handlers.append(
                lambda token: print(colored(token, "dark_grey"), end="", flush=True)
            )
            stream_response_end_handlers.append(lambda: print())
        if stream_for_file:
            # Clear the previous response from the file at the start of the stream
            stream_response_start_handlers.append(remove_trailing_messages)
            # Append a heading to the file at the start of the stream
            stream_response_start_handlers.append(
                lambda: file_operations.append_heading_to_file(
                    file_path, role="assistant"
                )
            )
            # Append response tokens to the file during the stream
            stream_response_token_handlers.append(
                lambda token: file_operations.append_token_to_file(
                    file_path, text=token
                )
            )
            # Append a newline to the file at the end of the stream
            stream_response_end_handlers.append(
                lambda: file_operations.append_token_to_file(file_path, text="\n")
            )
        else:  # If not streaming for file
            # Clear previous messages from the file at the end of the stream
            stream_response_end_handlers.append(remove_trailing_messages)
            # Append the complete message (including the heading and the trailing newline) to the file at the end of the stream
            stream_response_end_handlers.append(
                lambda: file_operations.append_message_to_file(
                    file_path, message=response_message
                )
            )
        # Print a message at the end of the stream
        stream_response_end_handlers.append(lambda: print("Completion stream ended."))
        # Prompt the user to continue the conversation at the end of the stream
        stream_response_end_handlers.append(
            lambda: file_operations.append_heading_to_file(file_path, role="user")
        )

        # Update the configuration with the stream response handlers
        config.update(
            {
                "stream_response_start_handlers": stream_response_start_handlers,
                "stream_response_token_handlers": stream_response_token_handlers,
                "stream_response_end_handlers": stream_response_end_handlers,
            }
        )

        # Request completion using the completion handler
        print("Requesting completion...")
        response_message = await completion_handler.request_completion(
            messages=messages, config=config
        )
    except Exception as e:
        utils.log_error(e)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        utils.log_error("Process interrupted by user.")
