from rendering import (
    DARK_CSS,
    LIGHT_CSS,
    highlight_code,
    normalize_language,
    render_markdown,
)


def test_known_language_passes_through():
    assert normalize_language("python") == "python"


def test_unknown_language_falls_back_to_text():
    assert normalize_language("not-a-real-lang") == "text"


def test_empty_language_falls_back_to_text():
    assert normalize_language("") == "text"


def test_highlight_wraps_in_source_class():
    html = highlight_code("print('hi')", "python")
    assert 'class="source' in html


def test_highlight_unknown_language_does_not_raise():
    html = highlight_code("whatever", "not-real")
    assert "whatever" in html


def test_theme_css_are_scoped_and_distinct():
    assert ':root:not([data-theme="dark"]) .source' in LIGHT_CSS
    assert ':root[data-theme="dark"] .source' in DARK_CSS
    assert LIGHT_CSS != DARK_CSS


def test_markdown_renders_headings():
    html = render_markdown("# Title")
    assert "<h1" in html and "Title" in html


def test_markdown_strips_script_tags():
    html = render_markdown("hello <script>alert(1)</script>")
    assert "<script" not in html.lower()


def test_markdown_strips_onclick_attributes():
    html = render_markdown('<a href="x" onclick="evil()">link</a>')
    assert "onclick" not in html


def test_markdown_keeps_safe_links():
    html = render_markdown("[ok](https://example.com)")
    assert 'href="https://example.com"' in html
