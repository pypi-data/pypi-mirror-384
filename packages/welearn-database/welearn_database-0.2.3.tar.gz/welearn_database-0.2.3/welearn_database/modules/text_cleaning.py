import logging
import re
from html import unescape
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class HTMLTagRemover(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, data):
        self.result.append(data)

    def get_text(self):
        return "".join(self.result)


def remove_extra_whitespace(text: str) -> str:
    """removes extra whitespace from text

    Args:
        text (str): text to evaluate

    Returns:
        str: text without extra whitespace
    """
    if not isinstance(text, str):
        return text
    return " ".join(text.split())


def remove_html_stuff(text: str) -> str:
    """
    removes html tags and special stuff like &amp; from text

    Args:
        text (str): text to evaluate

    Returns:
        str: text without html tags
    """
    if not isinstance(text, str):
        return text
    remover = HTMLTagRemover()
    remover.feed(text + "\n")
    txt = remover.get_text()
    ret = unescape(txt)
    return ret


def format_cc_license(to_format_license: str) -> str:
    """
    Format a Creative Commons license to a well formated url.
    :param to_format_license: License to format.
    :return: License well formated.
    """
    if not isinstance(to_format_license, str):
        return to_format_license
    splitted_elements = to_format_license.split("-")
    version = splitted_elements[-1].strip()
    rights_code = "-".join(splitted_elements[1:-1]).strip().lower()

    return (
        f"https://creativecommons.org/licenses/{rights_code.lower()}/{version.lower()}/"
    )

def clean_return_to_line(string: str):
    if not isinstance(string, str):
        return string
    ret = re.sub(r"([\n\t\r])", "", string).strip()
    return ret


def clean_text(content: str) -> str:
    """
    Clean the content of a document by removing html tags and extra whitespace

    Args:
        content (str): the content of the document

    Returns:
        str: the cleaned content
    """
    if not isinstance(content, str):
        return content
    return remove_extra_whitespace(remove_html_stuff(content)).strip()
