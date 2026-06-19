from rendering import (
    DARK_CSS,
    LIGHT_CSS,
    highlight_code,
    normalize_language,
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
