from smartchunk import SmartChunker

def test_basic_chunking():
    txt = (
        "# Title\n\n"
        "## A\n"
        "para1\n\n"
        "## B\n"
        "line1\n\n"
        "- item 1\n"
        "- item 2\n\n"
        "```python\n"
        "print('x')\n"
        "```\n"
    )
    chunks = SmartChunker().chunk(txt, max_chars=60, overlap_chars=10)
    assert len(chunks) >= 1, "should produce at least one chunk"
    # header path should include the top-level Title
    assert all("Title" in c.header_path for c in chunks)
    # consecutive chunks should share overlap
    if len(chunks) >= 2:
        assert chunks[0].text[-10:] in chunks[1].text
