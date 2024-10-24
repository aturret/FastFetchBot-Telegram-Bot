import re

from bs4 import BeautifulSoup

from config import TELEGRAM_TEXT_LIMIT, JINJA2_ENV, TEMPLATE_TRANSLATION, TEMPLATE_LANGUAGE
from utils.logger import logger

template = JINJA2_ENV.get_template("social_media_message.jinja2")
template_text = TEMPLATE_TRANSLATION.get(
    TEMPLATE_LANGUAGE, TEMPLATE_TRANSLATION["zh_CN"]
)


def message_formatting(data: dict) -> str:
    """
    Format the message to be sent to the user.
    :param data:
    :return: text (str) the formatted text for telegram bot api sending message.
    """
    if data["message_type"] == "short":
        data["text"] = telegram_message_html_trim(data["text"])
    message_template = template
    text = message_template.render(data=data, template_text=template_text)
    logger.debug(f"message text: \n{text}")
    return text


def telegram_message_html_trim(html_content: str, trim_length: int = TELEGRAM_TEXT_LIMIT) -> str:
    # remove all img tag
    soup = BeautifulSoup(html_content, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    html_content = str(soup)

    if len(html_content) <= trim_length:
        return html_content

        # Initial trimming
    trimmed_content = html_content[:trim_length]
    remaining_content = html_content[trim_length:]

    # Find the position of the last complete tag in the trimmed content
    last_complete_pos = trimmed_content.rfind('<')
    if last_complete_pos != -1:
        trimmed_content = trimmed_content[:last_complete_pos]
        remaining_content = html_content[last_complete_pos:] + remaining_content

    # Remove any incomplete tags by ensuring each tag is closed
    cleaned_html = ''
    open_tags = []

    tag_pattern = re.compile(r'<(/?)([a-zA-Z0-9]+)([^>]*)>')
    pos = 0

    while pos < len(trimmed_content):
        match = tag_pattern.search(trimmed_content, pos)
        if not match:
            break

        start, end = match.span()
        cleaned_html += trimmed_content[pos:start]

        closing, tag_name, attributes = match.groups()

        if closing:
            if open_tags and open_tags[-1] == tag_name:
                open_tags.pop()
                cleaned_html += match.group(0)
        else:
            if not attributes.endswith('/'):
                open_tags.append(tag_name)
                cleaned_html += match.group(0)

        pos = end

    cleaned_html += trimmed_content[pos:]

    # Ensure to close all open tags
    for tag in reversed(open_tags):
        cleaned_html += f'</{tag}>'

    print(cleaned_html)
    return cleaned_html + ' ...'
