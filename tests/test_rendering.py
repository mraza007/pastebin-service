from rendering import normalize_language


def test_known_language_passes_through():
    assert normalize_language("python") == "python"


def test_unknown_language_falls_back_to_text():
    assert normalize_language("not-a-real-lang") == "text"


def test_empty_language_falls_back_to_text():
    assert normalize_language("") == "text"
