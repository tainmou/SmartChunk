# src/smartchunk/fetcher.py
import requests
from bs4 import BeautifulSoup

def fetch_article_text(url: str) -> str:
    """Fetches and extracts the main content from a URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad responses (404, 500)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main content of the page (this selector is an example)
        # Often the main content is in a <main> tag or an <article> tag
        main_content = soup.find('main') or soup.find('article')
        
        if main_content:
            return main_content.get_text(separator='\n\n', strip=True)
        else:
            # Fallback if a clear main tag isn't found
            return soup.body.get_text(separator='\n\n', strip=True)
            
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return ""