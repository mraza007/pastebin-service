import bleach
import markdown as md
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.util import ClassNotFound

_ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    "p", "pre", "h1", "h2", "h3", "h4", "h5", "h6",
    "img", "hr", "br", "span", "table", "thead", "tbody",
    "tr", "th", "td",
}
_ALLOWED_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "*": ["class"],
}

# Theme CSS is scoped by the active theme on :root, so a single rendered
# `.source` block is styled correctly in both light and dark mode.
_LIGHT_SELECTOR = ':root:not([data-theme="dark"]) .source'
_DARK_SELECTOR = ':root[data-theme="dark"] .source'

LIGHT_CSS = HtmlFormatter(style="default").get_style_defs(_LIGHT_SELECTOR)
DARK_CSS = HtmlFormatter(style="monokai").get_style_defs(_DARK_SELECTOR)


def normalize_language(language: str) -> str:
    """Return language if Pygments knows it, else 'text'."""
    try:
        get_lexer_by_name(language)
        return language
    except ClassNotFound:
        return "text"


def highlight_code(content: str, language: str) -> str:
    """Highlight code into a single `.source` block themed via scoped CSS."""
    lexer = get_lexer_by_name(normalize_language(language), stripall=True)
    formatter = HtmlFormatter(linenos=True, cssclass="source")
    return highlight(content, lexer, formatter)


def get_language_options() -> list[tuple[str, str]]:
    """Sorted (lexer_alias, display_name) pairs for the language picker."""
    return sorted(
        (lexer[1][0], lexer[0]) for lexer in get_all_lexers() if lexer[1]
    )


def render_markdown(content: str) -> str:
    """Render markdown to sanitized HTML (defends against stored XSS)."""
    raw_html = md.markdown(content, extensions=["fenced_code", "tables"])
    return bleach.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
    )
