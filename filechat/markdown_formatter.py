from . import chat_format

import re


def format_h1(text: str) -> str:
    """
    Ensure consistent spacing around H1 headings.
    """

    if text == "":
        return text

    role_heading_pattern = "|".join(
        heading
        for role, heading in chat_format.role_heading_map.items()
        if role in chat_format.roles
    )
    heading_pattern = re.compile(
        rf"(?:(?<=\A)|(?<=\n))\n*(# (?:{role_heading_pattern}))(?:\n+|\Z)", re.DOTALL
    )
    heading_matches = re.finditer(heading_pattern, text)
    last_match_end = 0
    formatted_text = ""
    for heading_match in heading_matches:
        formatted_text += (
            text[last_match_end : heading_match.start()]
            + "\n"
            + heading_match.group(1)
            + "\n\n"
        )
        last_match_end = heading_match.end()
    formatted_text += text[last_match_end:]
    return formatted_text


def format_text(text: str) -> str:
    """
    Format a Markdown text file content.
    """

    # Exclude front matter, code blocks and math blocks
    exclusive_pattern = re.compile(
        r"(?P<block>\A---\s*?\n.*?\n---|```[^\n]*?\n.*?```|\$\$\n.*?\n\$\$)\s*?(?P<end>\n|\Z)",
        re.DOTALL,
    )
    exclusive_matches = re.finditer(exclusive_pattern, text)
    last_match_end = 0
    formatted_text = ""
    for exclusive_match in exclusive_matches:
        formatted_text += (
            format_h1(text[last_match_end : exclusive_match.start()])
            + exclusive_match.group("block")
            + exclusive_match.group("end")
        )
        last_match_end = exclusive_match.end()
    formatted_text += format_h1(text[last_match_end:])
    return formatted_text.strip() + "\n"
