"""Tests for the pure name_value letter-sum logic.

These run under plain CPython (no Pyodide / Workers runtime needed) because
the logic lives in `src/name_value.py`, free of any worker-specific imports.
"""

import pytest

from name_value import compute_name_value


class TestBasicLetters:
    def test_single_uppercase_a(self):
        result = compute_name_value("A")
        assert result == {"input": "A", "letters_counted": 1, "total": 1}

    def test_single_uppercase_z(self):
        result = compute_name_value("Z")
        assert result == {"input": "Z", "letters_counted": 1, "total": 26}

    def test_full_uppercase_alphabet(self):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        result = compute_name_value(alphabet)
        assert result["letters_counted"] == 26
        assert result["total"] == 26 * 27 // 2

    def test_full_lowercase_alphabet(self):
        result = compute_name_value("abcdefghijklmnopqrstuvwxyz")
        assert result["total"] == 351
        assert result["letters_counted"] == 26


class TestCaseInsensitivity:
    def test_lowercase_matches_uppercase(self):
        assert compute_name_value("cat")["total"] == compute_name_value("CAT")["total"]

    def test_mixed_case(self):
        assert compute_name_value("Cat")["total"] == 24

    def test_mixed_case_longer(self):
        assert compute_name_value("HelloWorld")["total"] == 124


class TestKnownExamples:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Cat", 24),
            ("Dog", 26),
            ("Hello", 52),
            ("World", 72),
            ("Python", 98),
            ("Cloudflare", 97),
            ("MCP", 32),
        ],
    )
    def test_known_totals(self, name: str, expected: int):
        assert compute_name_value(name)["total"] == expected


class TestNonLetters:
    def test_empty_string(self):
        result = compute_name_value("")
        assert result == {"input": "", "letters_counted": 0, "total": 0}

    def test_only_digits(self):
        result = compute_name_value("12345")
        assert result["total"] == 0
        assert result["letters_counted"] == 0

    def test_only_whitespace(self):
        result = compute_name_value("   \t\n")
        assert result["total"] == 0
        assert result["letters_counted"] == 0

    def test_only_punctuation(self):
        result = compute_name_value("!@#$%^&*()")
        assert result["total"] == 0
        assert result["letters_counted"] == 0

    def test_letters_with_punctuation(self):
        result = compute_name_value("Hello, World!")
        assert result["total"] == 124
        assert result["letters_counted"] == 10

    def test_letters_with_digits(self):
        result = compute_name_value("Cat42")
        assert result["total"] == 24
        assert result["letters_counted"] == 3


class TestUnicode:
    def test_accented_letters_are_ignored(self):
        result = compute_name_value("café")
        assert result["letters_counted"] == 3
        assert result["total"] == 3 + 1 + 6

    def test_non_latin_script_is_ignored(self):
        result = compute_name_value("こんにちは")
        assert result["total"] == 0
        assert result["letters_counted"] == 0

    def test_emoji_is_ignored(self):
        result = compute_name_value("Hi👋")
        assert result["total"] == 8 + 9
        assert result["letters_counted"] == 2

    def test_input_preserves_original_string(self):
        result = compute_name_value("Café 42!")
        assert result["input"] == "Café 42!"


class TestTypeValidation:
    @pytest.mark.parametrize("bad_input", [None, 42, 3.14, [], {}, b"bytes"])
    def test_non_string_raises(self, bad_input):
        with pytest.raises(TypeError, match="must be a string"):
            compute_name_value(bad_input)
