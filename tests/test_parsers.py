from smartchunk.parsers import parse_html


def test_parse_html_basic():
    html = """<!DOCTYPE html>
    <html><body>
    <h1>Title</h1>
    <p>First paragraph.</p>
    <ul><li>Item1</li><li>Item2</li></ul>
    <script>alert('bad')</script>
    </body></html>"""
    text = parse_html(html)
    assert text.startswith("# DOCTYPE HTML")
    assert "# Title" in text
    assert "* Item1" in text
    assert "bad" not in text
