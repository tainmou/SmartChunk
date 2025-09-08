import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def fetch_article_text(url: str) -> str:
    """
    Fetches the main content of an article from a URL.

    This function is designed to be robust. It will:
    1. Identify itself with a clear User-Agent.
    2. Attempt to find the main content using common HTML5 tags (<article>, <main>).
    3. Fall back to a heuristic based on paragraph density to find the content.
    4. Return the raw HTML of the main content block for further processing.
    """
    headers = {
        'User-Agent': 'SmartChunk/1.0 (LanguageModelBot/1.0; +http://smartchunk.ai/bot)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    except requests.RequestException as e:
        logger.error("Error fetching URL %s: %s", url, e)
        return ""

    soup = BeautifulSoup(response.text, 'html.parser')

    # --- Intelligent Content Extraction ---

    # 1. Primary Method: Look for <article> or <main> tags
    main_content = soup.find('article') or soup.find('main')

    # 2. Fallback Method: Find the parent with the most <p> tags
    if not main_content:
        paragraphs = soup.find_all('p')
        if not paragraphs:
            # If no paragraphs, we can't use this heuristic.
            # Return the whole body's text as a last resort.
            body = soup.find('body')
            if body:
                return body.prettify() # Return the raw HTML for the parser to handle
            return ""

        # Find the parent that contains the most paragraphs
        parent_map = {}
        for p in paragraphs:
            if p.parent not in parent_map:
                parent_map[p.parent] = 0
            parent_map[p.parent] += 1
        
        # Find the parent with the highest paragraph count
        if parent_map:
            main_content = max(parent_map, key=parent_map.get)

    # 3. Final Resort
    if not main_content:
        body = soup.find('body')
        if body:
            return body.prettify()
        return ""

    # Return the raw HTML of the extracted main content block.
    # Your existing HTML parser is already excellent at cleaning this up.
    return main_content.prettify()
