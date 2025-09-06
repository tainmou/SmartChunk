from bs4 import BeautifulSoup

def parse_markdown(text: str) -> str:
    # right now just return as-is
    return text

def parse_text(text: str) -> str:
    # strip extra whitespace
    return "\n".join(line.strip() for line in text.splitlines())

def parse_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    # keep headings, paragraphs, lists, code blocks
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)
