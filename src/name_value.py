"""Pure letter-value logic.

Kept in its own module (free of any Cloudflare/Pyodide imports) so unit tests
can exercise it under plain CPython without spinning up a Worker.
"""

from typing import TypedDict


class NameValueResult(TypedDict):
    input: str
    letters_counted: int
    total: int


def compute_name_value(name: str) -> NameValueResult:
    """Sum letter values where A=1, B=2, ..., Z=26.

    Non-letter characters (digits, whitespace, punctuation, accented or
    non-ASCII letters) are ignored. The match is case-insensitive.

    Examples:
        >>> compute_name_value("Cat")["total"]
        24
        >>> compute_name_value("abc")["total"]
        6
        >>> compute_name_value("Hello, World!")["total"]
        124
        >>> compute_name_value("")["total"]
        0
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a string, got {type(name).__name__}")

    total = 0
    counted = 0
    for ch in name.upper():
        if "A" <= ch <= "Z":
            total += ord(ch) - ord("A") + 1
            counted += 1

    return {"input": name, "letters_counted": counted, "total": total}
