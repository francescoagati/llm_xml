# generate_books.py

This script generates an XML document representing a list of books using a language model. It then parses, cleans, and extracts the XML content to create a list of book dictionaries.

## Features
- Generate XML content for a list of books
- Clean and extract XML content from text
- Parse XML content to create a list of books
- Logging for debugging and tracking execution flow

## Requirements
- Python 3.x
- `ollama` library
- `beautifulsoup4` library

## Installation

1. Clone the repository:
```sh
$ git clone <repository_url>
```
2. Navigate to the project directory:
```sh
$ cd <repository_directory>
```
3. Install the required dependencies:
```sh
$ pip install -r requirements.txt
```

## Usage

Run the script to generate and process the XML content:
```sh
$ python generate_books.py
```

## Why LLMs Work Well with XML Output

Language models (LLMs) work well with XML output for several reasons:

1. **Structured Data**: XML provides a structured format that is easy to parse and validate. This makes it suitable for representing hierarchical data like books.

2. **Human-Readable**: XML is human-readable and self-descriptive, making it easier to understand and debug compared to other formats like JSON.

3. **Extensibility**: XML is extensible, allowing for the addition of new elements and attributes without breaking the existing structure.

4. **Standardization**: XML is a widely accepted standard for data interchange, ensuring compatibility with various systems and tools.

5. **Validation**: XML supports schema validation, ensuring that the data adheres to a predefined structure and rules.

# Why XML is a Better Choice for Structured Outputs from LLMs?

## Introduction
Interacting with large language models (LLMs) to obtain structured outputs is a complex challenge. Traditional solutions, such as JSON and function calling, often prove to be rigid and fragile. xmllm offers an alternative based on XML, a semantic format that is readable by both humans and machines and more resilient to errors.

Let's see why XML represents a more robust option for extracting structured data from LLMs and how xmllm simplifies this process.

## 1. Advantages of XML over JSON and Function Calling
Many developers are used to requesting JSON as output from LLMs, but XML has several key advantages:

### 1.1. Greater Error Tolerance
LLMs can generate malformed or incomplete JSON (e.g., with missing quotes or invalid syntax).
XML parsing tools, especially those based on HTML (like htmlparser2 used by xmllm), are much more flexible and can recover data even if the format is dirty or partially incorrect.


### 1.2. XML is Closer to the Natural Writing of LLMs
LLMs have been trained on vast amounts of text, including documents with XML and HTML markup.
XML blends better with the natural way an LLM generates text, avoiding the typical "robotic" style observed when forcing JSON generation.

#### Example of forced JSON output:
```json
{
  "response": "This is a structured response.",
  "data": [ "Item 1", "Item 2", "Item 3" ]
}
```
→ LLMs often generate responses with less fluidity and more structural errors.

#### Example of more natural XML for LLMs:
```xml
<response>This is a structured response.</response>
<data>
    <item>Item 1</item>
    <item>Item 2</item>
    <item>Item 3</item>
</data>
```
→ XML markup allows the model to express itself freely while maintaining structure.

