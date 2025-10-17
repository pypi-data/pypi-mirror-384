"""Test the arts of Uwuification."""

import pytest
from uwuifier import (
    char_replace,
    nyaify,
    stutter,
    tildify,
    word_replace,
)


@pytest.mark.parametrize(
    ("in_text", "out_text"),
    [
        ("cats are small", "cats are smol"),
        ("I love dogs", "I luv dogs"),
    ],
)
def test_word_replace(in_text: str, out_text: str) -> None:
    """Test replacing words in text."""
    assert word_replace(in_text) == out_text


@pytest.mark.parametrize(
    ("in_text", "out_text"),
    [
        ("look", "wook"),
        ("rook", "wook"),
        ("lr", "ww"),
        ("rl", "ww"),
        ("wrl", "www"),
    ],
)
def test_char_replace(in_text: str, out_text: str) -> None:
    """Test replacing characters in text."""
    assert char_replace(in_text) == out_text


@pytest.mark.parametrize(
    ("strength", "in_text", "out_text"),
    [
        (0.0, "cats are small", "cats are small"),
        (1.0, "I love dogs", "I-I l-love d-dogs"),
    ],
)
def test_stutter(strength: float, in_text: str, out_text: str) -> None:
    """Test adding stutters to text."""
    assert stutter(in_text, strength) == out_text


@pytest.mark.parametrize(
    ("in_text", "out_text"),
    [
        ("naa", "naa"),
        ("nan", "nyan"),
    ],
)
def test_nyaify(in_text: str, out_text: str) -> None:
    """Test nyaifying text."""
    assert nyaify(in_text) == out_text


@pytest.mark.parametrize(
    ("strength", "in_text", "out_text"),
    [
        (0.0, "cats are small", "cats are small"),
        (1.0, "I love dogs", "I~ love~ dogs"),
    ],
)
def test_tildify(strength: float, in_text: str, out_text: str) -> None:
    """Test adding tildes."""
    assert tildify(in_text, strength) == out_text
