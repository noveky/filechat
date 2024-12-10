from . import chat_format, markdown_formatter

import re, yaml, typing, openai.types.chat


def get_section_pattern_for_roles(roles: typing.Iterable[str]) -> re.Pattern[str]:
    role_heading_pattern = "|".join(
        heading
        for role, heading in chat_format.role_heading_map.items()
        if role in roles
    )
    return re.compile(
        rf"(?:\A\n*|\n\n)# ({role_heading_pattern})(?:\n*\Z|\n\n(.*?)(?=\n\n# (?:{role_heading_pattern})(?:\n\n|\n*\Z)|\n*\Z))",
        re.DOTALL,
    )


def match_front_matter(text: str) -> re.Match[str] | None:
    front_matter_pattern = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
    return re.search(front_matter_pattern, text)


def parse_file(file_path: str) -> tuple[dict, list[dict]]:
    """
    Parse the file containing configuration (optional) and messages and return the config and messages.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    config = {}
    front_matter_pattern = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
    front_matter_match = re.search(front_matter_pattern, text)
    if front_matter_match:
        try:
            config = yaml.safe_load(front_matter_match.group(1))
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing config: {e}")
        if not isinstance(config, dict):
            raise ValueError("Invalid config format. Expected a dictionary.")
        text = text[front_matter_match.end() :]

    section_pattern = get_section_pattern_for_roles(chat_format.roles)
    section_matches = re.findall(section_pattern, text)

    messages = [
        {
            "role": chat_format.heading_role_map[str(heading)],
            "content": str(content).strip(),
        }
        for heading, content in section_matches
        if heading in chat_format.heading_role_map
    ]

    if not messages:
        # If there are no messages, assume the file is just a single user message
        # Format the file
        write_messages_to_file(
            file_path,
            messages=[{"role": "user", "content": text.strip()}],
            config=config,
        )
        # Parse the file again
        return parse_file(file_path)

    return config, messages


def format_file(file_path: str) -> None:
    """
    Format the file to ensure a consistent Markdown style.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(markdown_formatter.format_text(text))


def write_messages_to_file(
    file_path: str, messages: list[dict], config: dict = {}
) -> None:
    text = ""
    if config:
        text += f"---\n{yaml.dump(config).strip()}\n---\n\n"
    text += "\n".join(
        f"# {chat_format.role_heading_map[message["role"]]}\n\n{message["content"]}\n"
        for message in messages
    )
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)


def append_heading_to_file(file_path: str, role: str) -> None:
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"\n# {chat_format.role_heading_map[role]}\n\n")


def append_token_to_file(file_path: str, text: str) -> None:
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(text)


def append_message_to_file(
    file_path: str, message: openai.types.chat.ChatCompletionMessage
) -> None:
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(
            f"\n# {chat_format.role_heading_map[message.role]}\n\n{message.content}\n"
        )


def remove_last_message_from_file(
    file_path: str, match_roles: typing.Iterable[str]
) -> None:
    """
    Remove the last message from the file if it matches any of the specified roles.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    section_pattern = get_section_pattern_for_roles(chat_format.roles)
    section_matches = list(re.finditer(section_pattern, text))

    if not section_matches:
        return

    last_match = section_matches[-1]
    if chat_format.heading_role_map[str(last_match.group(1))] not in match_roles:
        return

    text = text[: last_match.start()] + "\n"

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(text)
