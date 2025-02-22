import sys
import xml.etree.ElementTree as ET
import re
from ollama import chat, ChatResponse
from bs4 import BeautifulSoup
import logging
from functools import wraps
from typing import Dict, List, Optional, Callable, TypeVar, Any
from dataclasses import dataclass


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


@dataclass
class Parameter:
    name: str
    type: str
    value: Any = None

@dataclass
class Function:
    name: str
    parameters: List[Parameter]

def parse_function_def(xml_content: str) -> Function:
    """Parse XML function definition into a Function object"""
    root = ET.fromstring(xml_content)
    name = root.get('name')
    params = []
    
    for param in root.findall('./Input/Parameter'):
        param_value = Parameter(
            name=param.get('name'),
            type=param.get('type'),
            value=param.text if param.text else None
        )
        logging.debug(f"Parsed parameter: {param_value}")
        params.append(param_value)
    
    return Function(name=name, parameters=params)

def generate_function_call(func: Function) -> Dict[str, Any]:
    """Generate function call parameters from Function object"""
    params = {
        param.name: convert_type(param.value, param.type) 
        for param in func.parameters
        if param.value is not None
    }
    logging.debug(f"Generated parameters for {func.name}: {params}")
    return params

def convert_type(value: str, type_name: str) -> Any:
    """Convert string value to specified type"""
    if value is None:
        return None
    
    type_converters = {
        'int': int,
        'float': float,
        'str': str,
        'bool': lambda x: x.lower() == 'true'
    }
    
    converter = type_converters.get(type_name)
    if not converter:
        raise ValueError(f"Unsupported type: {type_name}")
    
    result = converter(value)
    logging.debug(f"Converted value '{value}' to type {type_name}: {result}")
    return result

def get_llm_function_call(xml_definition: str) -> str:
    """Ask LLM to generate a function call based on XML definition"""
    prompt = """
    Given this XML function definition, return ONLY a valid Python function call string, nothing else.
    Maintain the exact function name case from the XML.
    DO NOT include any explanation text or backticks.
    
    For example, if given:
    <Function name="CalculateSum">
        <Input>
            <Parameter name="x" type="int">5</Parameter>
            <Parameter name="y" type="int">3</Parameter>
        </Input>
    </Function>
    You should return exactly and only:
    CalculateSum(x=5, y=3)
    """
    
    messages = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': xml_definition}
    ]
    
    try:
        response: ChatResponse = chat(model='llama3.2:1b', messages=messages)
        # Clean the response to get just the function call
        call_string = response.message.content.strip()
        logging.debug(f"LLM generated function call: {call_string}")
        # Remove any markdown backticks and extra text
        call_string = re.sub(r'^.*?([A-Za-z_][A-Za-z0-9_]*\(.*\)).*?$', r'\1', call_string, flags=re.DOTALL)
        return call_string
    except Exception as e:
        logging.error(f"LLM error: {e}")
        raise

def execute_function_call(call_string: str, available_functions: Dict[str, callable]) -> Any:
    """Execute a function call string with the given available functions"""
    # Extract function name from call string
    func_name = call_string.split('(')[0].strip()
    
    if func_name not in available_functions:
        raise ValueError(f"Function {func_name} not found in available functions")
    
    # Execute the function call
    try:
        result = eval(call_string, {"__builtins__": {}}, available_functions)
        return result
    except Exception as e:
        logging.error(f"Error executing function: {e}")
        raise

def example_usage():
    # Example function definition
    xml = '''
    <Function name="CalculateSum">
        <Input>
            <Parameter name="a" type="int">5</Parameter>
            <Parameter name="b" type="int">3</Parameter>
        </Input>
    </Function>
    '''
    
    # Define available functions
    def calculate_sum(a: int, b: int) -> int:
        return a + b
    
    available_functions = {
        'CalculateSum': calculate_sum
    }
    
    logging.info("Processing function definition")
    logging.debug(f"Input XML:\n{xml}")
    
    try:
        # Get function call from LLM
        call_string = get_llm_function_call(xml)
        logging.info(f"LLM generated function call: {call_string}")
        
        # Execute the function
        result = execute_function_call(call_string, available_functions)
        logging.info(f"Function result: {result}")
        
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    example_usage()
    #generate_books_xml()
