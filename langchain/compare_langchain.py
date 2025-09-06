from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

# --- Configuration ---
# We use a small chunk size to guarantee it will fail on the structured data.
CHUNK_SIZE = 150
CHUNK_OVERLAP = 20
DEMO_FILE = "demo.html"

def run_langchain_chunker():
    """
    Reads the demo HTML file and chunks it using a naive LangChain splitter.
    """
    print("=" * 80)
    print("🔬 Running Naive LangChain Chunker...")
    print("=" * 80)

    try:
        file_path = Path(DEMO_FILE)
        html_content = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"\n[ERROR] The file '{DEMO_FILE}' was not found.")
        print("Please make sure it is in the same directory as this script.")
        return

    # This is LangChain's most common, "one-size-fits-all" splitter.
    langchain_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    chunks = langchain_splitter.split_text(html_content)

    print(f"\n[INFO] LangChain produced {len(chunks)} chunks.\n")

    for i, chunk in enumerate(chunks):
        print(f"--- 💔🙈 LANGCHAIN CHUNK {i+1} (Size: {len(chunk)}) ---")
        # Replace newlines for cleaner printing in the terminal
        print(chunk.replace("\n", " "))
        print("-" * (35 + len(str(i+1)) + len(str(len(chunk)))))


if __name__ == "__main__":
    run_langchain_chunker()
