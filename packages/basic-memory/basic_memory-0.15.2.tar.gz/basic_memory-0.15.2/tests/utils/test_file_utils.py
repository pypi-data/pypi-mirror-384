"""Tests for file utilities."""

from pathlib import Path

import pytest
import random
import string

from basic_memory.file_utils import (
    FileError,
    FileWriteError,
    ParseError,
    compute_checksum,
    ensure_directory,
    has_frontmatter,
    parse_frontmatter,
    remove_frontmatter,
    sanitize_for_filename,
    sanitize_for_folder,
    update_frontmatter,
    write_file_atomic,
)


def get_random_word(length: int = 12, necessary_char: str | None = None) -> str:
    letters = string.ascii_lowercase
    word_chars = [random.choice(letters) for i in range(length)]

    if necessary_char and length > 0:
        # Replace a character at a random position with the necessary character
        random_pos = random.randint(0, length - 1)
        word_chars[random_pos] = necessary_char

    return "".join(word_chars)


@pytest.mark.asyncio
async def test_compute_checksum():
    """Test checksum computation."""
    content = "test content"
    checksum = await compute_checksum(content)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 produces 64 char hex string


@pytest.mark.asyncio
async def test_compute_checksum_error():
    """Test checksum error handling."""
    with pytest.raises(FileError):
        # Try to hash an object that can't be encoded
        await compute_checksum(object())  # pyright: ignore [reportArgumentType]


@pytest.mark.asyncio
async def test_ensure_directory(tmp_path: Path):
    """Test directory creation."""
    test_dir = tmp_path / "test_dir"
    await ensure_directory(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()


@pytest.mark.asyncio
async def test_write_file_atomic(tmp_path: Path):
    """Test atomic file writing."""
    test_file = tmp_path / "test.txt"
    content = "test content"

    await write_file_atomic(test_file, content)
    assert test_file.exists()
    assert test_file.read_text(encoding="utf-8") == content

    # Temp file should be cleaned up
    assert not test_file.with_suffix(".tmp").exists()


@pytest.mark.asyncio
async def test_write_file_atomic_error(tmp_path: Path):
    """Test atomic write error handling."""
    # Try to write to a directory that doesn't exist
    test_file = tmp_path / "nonexistent" / "test.txt"

    with pytest.raises(FileWriteError):
        await write_file_atomic(test_file, "test content")


def test_has_frontmatter():
    """Test frontmatter detection."""
    # Valid frontmatter
    assert has_frontmatter("""---
title: Test
---
content""")

    # Just content
    assert not has_frontmatter("Just content")

    # Empty content
    assert not has_frontmatter("")

    # Just delimiter
    assert not has_frontmatter("---")

    # Delimiter not at start
    assert not has_frontmatter("""
Some text
---
title: Test
---""")

    # Invalid format
    assert not has_frontmatter("--title: test--")


def test_parse_frontmatter():
    """Test parsing frontmatter."""
    # Valid frontmatter
    content = """---
title: Test
tags:
  - a
  - b
---
content"""

    result = parse_frontmatter(content)
    assert result == {"title": "Test", "tags": ["a", "b"]}

    # Empty frontmatter
    content = """---
---
content"""
    result = parse_frontmatter(content)
    assert result == {} or result == {}  # Handle both None and empty dict cases

    # Invalid YAML syntax
    with pytest.raises(ParseError) as exc:
        parse_frontmatter("""---
[: invalid yaml syntax :]
---
content""")
    assert "Invalid YAML in frontmatter" in str(exc.value)

    # Non-dict YAML content
    with pytest.raises(ParseError) as exc:
        parse_frontmatter("""---
- just
- a
- list
---
content""")
    assert "Frontmatter must be a YAML dictionary" in str(exc.value)

    # No frontmatter
    with pytest.raises(ParseError):
        parse_frontmatter("Just content")

    # Incomplete frontmatter
    with pytest.raises(ParseError):
        parse_frontmatter("""---
title: Test""")


def test_remove_frontmatter():
    """Test removing frontmatter."""
    # With frontmatter
    content = """---
title: Test
---
test content"""
    assert remove_frontmatter(content) == "test content"

    # No frontmatter
    content = "test content"
    assert remove_frontmatter(content) == "test content"

    # Only frontmatter
    content = """---
title: Test
---
"""
    assert remove_frontmatter(content) == ""

    # Invalid frontmatter - missing closing delimiter
    with pytest.raises(ParseError) as exc:
        remove_frontmatter("""---
title: Test""")
    assert "Invalid frontmatter format" in str(exc.value)


@pytest.mark.asyncio
async def test_update_frontmatter(tmp_path: Path):
    """Test updating frontmatter in a file."""
    test_file = tmp_path / "test.md"

    # Test 1: Add frontmatter to file without any
    content = "# Test Content\n\nSome content here"
    test_file.write_text(content)

    updates = {"title": "Test", "type": "note"}
    checksum = await update_frontmatter(test_file, updates)

    # Verify content
    updated = test_file.read_text(encoding="utf-8")
    assert "title: Test" in updated
    assert "type: note" in updated
    assert "Test Content" in updated
    assert "Some content here" in updated

    # Verify structure
    fm = parse_frontmatter(updated)
    assert fm == updates
    assert remove_frontmatter(updated).strip() == content

    # Test 2: Update existing frontmatter
    updates = {"type": "doc", "tags": ["test"]}
    new_checksum = await update_frontmatter(test_file, updates)

    # Verify checksum changed
    assert new_checksum != checksum

    # Verify content
    updated = test_file.read_text(encoding="utf-8")
    fm = parse_frontmatter(updated)
    assert fm == {"title": "Test", "type": "doc", "tags": ["test"]}
    assert "Test Content" in updated

    # Test 3: Update with empty dict shouldn't change anything
    checksum_before = await compute_checksum(test_file.read_text(encoding="utf-8"))
    new_checksum = await update_frontmatter(test_file, {})
    assert new_checksum == checksum_before

    # Test 4: Handle multi-line content properly
    content = """# Heading

Some content

## Section
- Point 1
- Point 2

### Subsection
More content here"""

    test_file.write_text(content)
    await update_frontmatter(test_file, {"title": "Test"})

    updated = test_file.read_text(encoding="utf-8")
    assert remove_frontmatter(updated).strip() == content


@pytest.mark.asyncio
async def test_update_frontmatter_errors(tmp_path: Path):
    """Test error handling in update_frontmatter."""

    # Test 1: Invalid file path
    nonexistent = tmp_path / "nonexistent" / "test.md"
    with pytest.raises(FileError):
        await update_frontmatter(nonexistent, {"title": "Test"})


@pytest.mark.asyncio
def test_sanitize_for_filename_removes_invalid_characters():
    # Test all invalid characters listed in the regex
    invalid_chars = '<>:"|?*'

    # All invalid characters should be replaced
    for char in invalid_chars:
        text = get_random_word(length=12, necessary_char=char)
        sanitized_text = sanitize_for_filename(text)

        assert char not in sanitized_text


@pytest.mark.parametrize(
    "input_folder,expected",
    [
        ("", ""),  # Empty string
        ("   ", ""),  # Whitespace only
        ("my-folder", "my-folder"),  # Simple folder
        ("my/folder", "my/folder"),  # Nested folder
        ("my//folder", "my/folder"),  # Double slash compressed
        ("my\\\\folder", "my/folder"),  # Windows-style double backslash compressed
        ("my/folder/", "my/folder"),  # Trailing slash removed
        ("/my/folder", "my/folder"),  # Leading slash removed
        ("./my/folder", "my/folder"),  # Leading ./ removed
        ("my<>folder", "myfolder"),  # Special chars removed
        ("my:folder|test", "myfoldertest"),  # More special chars removed
        ("my_folder-1", "my_folder-1"),  # Allowed chars preserved
        ("my folder", "my folder"),  # Space preserved
        ("my/folder//sub//", "my/folder/sub"),  # Multiple compressions and trims
        ("my\\folder\\sub", "my/folder/sub"),  # Windows-style separators normalized
        ("my/folder<>:|?*sub", "my/foldersub"),  # All invalid chars removed
        ("////my////folder////", "my/folder"),  # Excessive leading/trailing/multiple slashes
    ],
)
def test_sanitize_for_folder_edge_cases(input_folder, expected):
    assert sanitize_for_folder(input_folder) == expected
