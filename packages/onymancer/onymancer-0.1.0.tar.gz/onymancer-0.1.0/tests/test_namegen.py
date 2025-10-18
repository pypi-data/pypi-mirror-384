"""Tests for name generator."""


from onymancer import generate, load_tokens_from_json, set_token, set_tokens


def test_generate_simple() -> None:
    """Test simple name generation."""
    name = generate("s", seed=42)
    assert isinstance(name, str)
    assert len(name) > 0


def test_generate_with_literal() -> None:
    """Test generation with literals."""
    name = generate("s(dim)", seed=42)
    assert "dim" in name


def test_generate_with_capitalization() -> None:
    """Test generation with capitalization."""
    name = generate("!s", seed=42)
    assert name[0].isupper()


def test_generate_with_groups() -> None:
    """Test generation with groups."""
    name = generate("<s|v>", seed=42)
    assert isinstance(name, str)


def test_generate_empty_pattern() -> None:
    """Test generation with empty pattern."""
    name = generate("", seed=42)
    assert name == ""


def test_set_token() -> None:
    """Test setting a token."""
    set_token("x", ["test"])
    name = generate("x", seed=42)
    assert name == "test"


def test_set_tokens() -> None:
    """Test setting multiple tokens."""
    tokens = {"y": ["hello"], "z": ["world"]}
    set_tokens(tokens)
    name1 = generate("y", seed=42)
    name2 = generate("z", seed=42)
    assert name1 == "hello"
    assert name2 == "world"


def test_load_tokens_from_json_invalid() -> None:
    """Test loading invalid JSON."""
    result = load_tokens_from_json("nonexistent.json")
    assert result is False


def test_generate_reproducibility() -> None:
    """Test that same seed produces same result."""
    name1 = generate("s!v", seed=123)
    name2 = generate("s!v", seed=123)
    assert name1 == name2


def test_generate_complex_pattern() -> None:
    """Test complex pattern generation."""
    pattern = "!s<v|c>!C"
    name = generate(pattern, seed=456)
    assert isinstance(name, str)
    assert len(name) > 0
