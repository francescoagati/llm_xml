import sys
import xml.etree.ElementTree as ET
import re
from ollama import chat, ChatResponse
from bs4 import BeautifulSoup
import logging
from functools import wraps
from typing import Dict, List, Optional, Callable, TypeVar, Any


# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

T = TypeVar('T')


def log_decorator(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        logging.debug(f"Calling {func.__name__} with args: {
                      args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.debug(f"{func.__name__} returned {result}")
        return result
    return wrapper


def get_element_text(elem: Optional[ET.Element], default: str = 'Unknown') -> str:
    match elem:
        case None:
            return default
        case _:
            return elem.text or default


def create_book_dict(book_elem: ET.Element) -> Dict[str, str]:
    elements = ['title', 'author', 'publication_year', 'genre', 'isbn']
    return {element: get_element_text(book_elem.find(element)) for element in elements}


@log_decorator
def parse_books_xml(xml_content: str) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_content)
    return [create_book_dict(book) for book in root.findall('book')]


@log_decorator
def clean_xml_content(xml_content: str) -> str:
    transformations = [
        (r'```xml|```', ''),
        (r'<author([^>]+)>', r'<author>\1</author>'),
        (r'<genre\|([^>]+)>', r'<genre>\1</genre>')
    ]
    return ''.join(
        re.sub(pattern, repl, xml_content)
        for pattern, repl in transformations
    )


@log_decorator
def extract_xml_content(text: str) -> str:
    match [text.find('<booklist>'), text.find('</booklist>')]:
        case [-1, _] | [_, -1]:
            raise ValueError("No valid XML content found")
        case [start, end]:
            xml_content = text[start:end + len('</booklist>')]
            return BeautifulSoup(xml_content, "xml").prettify()


def process_content(content: str, pipeline: List[Callable]) -> Any:
    result = content
    for func in pipeline:
        result = func(result)
    return result


@log_decorator
def generate_books_xml() -> None:

    question = 'a list of buddhist books'
    response = get_xml_books(question)

    try:
        result = process_content(
            response.message.content,
            [clean_xml_content, extract_xml_content, parse_books_xml]
        )

        [logging.debug(f"Book: {book}") for book in result]

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        sys.exit(1)


def get_xml_books(question) -> ChatResponse:
    prompt = """
    Generate an XML document that represents a list of books.
    Each book should contain the following elements: title, author, publication_year, genre, and ISBN.
    The root element should be <booklist>, and each book should be nested within a <book> tag.
    Ensure proper XML formatting and structure.
    """

    messages = [
        {'role': role, 'content': content}
        for role, content in [
            ('system', prompt),
            ('user', question)
        ]
    ]

    model = 'llama3.2:1b'
    try:
        response: ChatResponse = chat(model=model, messages=messages)
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
    return response


if __name__ == "__main__":
    generate_books_xml()
