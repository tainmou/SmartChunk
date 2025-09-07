# ==============================================================================
# compare_langchain.py (FINAL VERSION with URL support)
#
# Fetches content from a URL and runs a naive, character-based LangChain
# splitter to demonstrate its weaknesses on live web content.
# ==============================================================================

import sys
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500
CHUNK_OVERLAP = 0

def fetch_raw_html(url: str) -> str:
    """Fetches the full raw HTML from a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"\n[ERROR] Failed to fetch URL: {e}")
        return ""

def run_langchain_comparison(url: str):
    """Fetches and processes a URL with a naive chunker."""
    print("=" * 80)
    print(f"🔬 Running Naive LangChain Chunker on URL: {url}")
    print("=" * 80)
    
    html_text = fetch_raw_html(url)
    if not html_text:
        return

    # Use LangChain's basic character splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    chunks = text_splitter.create_documents([html_text])

    print(f"\n[INFO] LangChain produced {len(chunks)} messy chunks.\n")

    for i, chunk in enumerate(chunks[:5]): # Show first 5 messy chunks
        print(f"--- 💔🙈 LANGCHAIN CHUNK {i+1} (Size: {len(chunk.page_content)}) ---")
        print(chunk.page_content.replace('\n', ' ').strip())
        print("-" * 40)
    
    if len(chunks) > 5:
        print(f"\n... and {len(chunks) - 5} more messy chunks ...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url_to_test = sys.argv[1]
        run_langchain_comparison(url_to_test)
    else:
        print("\n[ERROR] Please provide a URL as a command-line argument.")
        print("Example: python compare_langchain.py \"https://en.wikipedia.org/wiki/Artificial_intelligence\"")

    

