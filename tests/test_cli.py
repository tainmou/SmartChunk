from typer.testing import CliRunner
from smartchunk.cli import app


runner = CliRunner()

def test_fetch_command(monkeypatch):
    sample_html = "<html><body><h1>Hi</h1><p>there</p><script>bad()</script></body></html>"
    monkeypatch.setattr('smartchunk.cli.fetch_article_text', lambda url: sample_html)
    result = runner.invoke(app, ["fetch", "http://example.com", "--format", "json"])
    assert result.exit_code == 0
    assert "Hi" in result.stdout
    assert "bad" not in result.stdout

def test_chunk_command(tmp_path):
    sample_html = "<html><body><h1>Hi</h1><p>there</p><script>bad()</script></body></html>"
    file = tmp_path / "sample.html"
    file.write_text(sample_html)
    result = runner.invoke(app, ["chunk", str(file), "--mode", "html", "--format", "json"])
    assert result.exit_code == 0
    assert "Hi" in result.stdout
    assert "bad" not in result.stdout

def test_stream_command():
    input_html = "<html><body><h1>Hi</h1><p>there</p></body></html>\n"
    result = runner.invoke(app, ["stream", "--mode", "html", "--max-chars", "20", "--format", "jsonl"], input=input_html)
    assert '"id": "c0001"' in result.stdout
    assert "Hi" in result.stdout
