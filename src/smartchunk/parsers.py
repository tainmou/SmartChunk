import re
from bs4 import BeautifulSoup

def parse_html(html_content: str) -> str:
    """
    Intelligently and correctly parses HTML content into a clean, Markdown-like
    text format by transforming the document tree in-place. This version preserves
    the full document structure.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Section 1: DOCTYPE ---
    # Create a placeholder for the doctype if it exists.
    doctype_section = ""
    if html_content.lower().strip().startswith("<!doctype html>"):
        doctype_section = "# DOCTYPE HTML\n\n---\n\n"

    # --- In-Place Transformations on the Soup Object ---

    # Decompose (remove) all tags that are not useful for text content, like styles and scripts.
    for tag in soup.find_all(['script', 'style', 'nav', 'header']):
        tag.decompose()

    # Convert header tags to Markdown header syntax
    for i in range(1, 7):
        for tag in soup.find_all(f'h{i}'):
            tag.replace_with(f"\n\n{'#' * i} {tag.get_text(strip=True)}\n\n")

    # Convert paragraph tags to plain text with newlines
    for tag in soup.find_all('p'):
        tag.replace_with(f"{tag.get_text(strip=True)}\n\n")

    # Convert <pre> tags to Markdown fenced code blocks
    for tag in soup.find_all('pre'):
        # Using .string helps preserve the exact code formatting within the block
        code_content = tag.string or tag.get_text()
        tag.replace_with(f"```\n{code_content.strip()}\n```\n\n")
        
    # Convert list items
    for tag in soup.find_all('li'):
        tag.replace_with(f"* {tag.get_text(strip=True)}\n")
    for tag in soup.find_all(['ul', 'ol']):
        # Replace the list tag with just its processed content (the list items)
        tag.replace_with(tag.get_text())

    # Convert tables to a simple text representation
    for tag in soup.find_all('table'):
        table_text = ""
        for row in tag.find_all('tr'):
            row_text = " | ".join([cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])])
            table_text += row_text + "\n"
        tag.replace_with(table_text)
    
    # --- Final Text Extraction ---
    
    # After all transformations, get the text from the entire soup.
    # We use a space as a separator to prevent words from mashing together.
    full_text = soup.get_text(separator=' ', strip=False)
    
    # Clean up excessive newlines and whitespace that might have been created
    cleaned_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()
    
    # Combine the doctype section with the main content
    return doctype_section + cleaned_text


def parse_markdown(text: str) -> str:
    """Minimal cleanup for Markdown text."""
    return text.strip()

def parse_text(text: str) -> str:
    """Minimal cleanup for plain text."""
    return text.strip()
