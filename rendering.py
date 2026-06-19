from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

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
