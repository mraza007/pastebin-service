from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound


def normalize_language(language: str) -> str:
    """Return language if Pygments knows it, else 'text'."""
    try:
        get_lexer_by_name(language)
        return language
    except ClassNotFound:
        return "text"
