import sys
import xml.etree.ElementTree as ET
import re
from ollama import chat, ChatResponse
from bs4 import BeautifulSoup
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Decorator for logging

def log_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.debug(f"{func.__name__} returned {result}")
        return result
    return wrapper

@log_decorator
def parse_books_xml(xml_content):
    root = ET.fromstring(xml_content)
    books = []
    for book_elem in root.findall('book'):
        title_elem = book_elem.find('title')
        author_elem = book_elem.find('author')
        publication_year_elem = book_elem.find('publication_year')
        genre_elem = book_elem.find('genre')
        isbn_elem = book_elem.find('isbn')
        title = title_elem.text if title_elem is not None else 'Unknown'
        author = author_elem.text if author_elem is not None else 'Unknown'
        publication_year = publication_year_elem.text if publication_year_elem is not None else 'Unknown'
        genre = genre_elem.text if genre_elem is not None else 'Unknown'
        isbn = isbn_elem.text if isbn_elem is not None else 'Unknown'
        book = {
            'title': title,
            'author': author,
            'publication_year': publication_year,
            'genre': genre,
            'isbn': isbn
        }
        books.append(book)
    return books

@log_decorator
def clean_xml_content(xml_content):
    xml_content = re.sub(r'```xml|```', '', xml_content)
    xml_content = re.sub(r'<author([^>]+)>', r'<author>\1</author>', xml_content)
    xml_content = re.sub(r'<genre\|([^>]+)>', r'<genre>\1</genre>', xml_content)
    return xml_content

@log_decorator
def extract_xml_content(text):
    start = text.find('<booklist>')
    end = text.find('</booklist>') + len('</booklist>')
    if start != -1 and end != -1:
        xml_content = text[start:end]
        soup = BeautifulSoup(xml_content, "xml")
        return soup.prettify()
    else:
        raise ValueError("No valid XML content found")

@log_decorator
def generate_books_xml():
    prompt = """
    Generate an XML document that represents a list of books.
    Each book should contain the following elements: title, author, publication_year, genre, and ISBN.
    The root element should be <booklist>, and each book should be nested within a <book> tag.
    Ensure proper XML formatting and structure.
    """
    try:
        response: ChatResponse = chat(model='llama3.2', messages=[
            {
                'role': 'system',
                'content': prompt,
            },
            {
                'role': 'user',
                'content': 'a list of buddhist books'
            }
        ])
        xml_content = response.message.content
        xml_content = clean_xml_content(xml_content)
        xml_content = extract_xml_content(xml_content)
        books = parse_books_xml(xml_content)
        for book in books:
            logging.debug(f"Book: {book}")
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    generate_books_xml()