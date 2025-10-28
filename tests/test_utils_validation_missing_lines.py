"""Targeted tests for missing lines in utils/validation.py to reach 100% coverage."""

from mcpi.utils.validation import sanitize_filename


class TestMissingValidationCoverage:
    """Tests specifically targeting missing lines 185-187 in utils/validation.py."""

    def test_sanitize_filename_over_255_chars_with_extension(self):
        """Test sanitize_filename with filename over 255 characters having extension.

        This test specifically targets lines 185-187:
        - name, ext = Path(sanitized).stem, Path(sanitized).suffix
        - max_name_len = 255 - len(ext)
        - sanitized = name[:max_name_len] + ext
        """
        # Create a filename that's over 255 characters
        long_name = "a" * 252  # 252 chars
        extension = ".txt"  # 4 chars
        long_filename = long_name + extension  # Total: 256 chars (> 255)

        result = sanitize_filename(long_filename)

        # Should be exactly 255 characters
        assert len(result) == 255
        # Should end with the original extension
        assert result.endswith(extension)
        # Should start with the original name (truncated)
        assert result.startswith("aaaa")
        # Name part should be exactly 255 - 4 = 251 characters
        name_part = result[:-4]  # Remove .txt
        assert len(name_part) == 251

    def test_sanitize_filename_over_255_chars_with_long_extension(self):
        """Test sanitize_filename with long extension."""
        # Create filename with a longer extension
        long_name = "b" * 240
        long_extension = ".really_long_extension"
        long_filename = long_name + long_extension  # Should be > 255

        result = sanitize_filename(long_filename)

        # Should be exactly 255 characters
        assert len(result) == 255
        # Should end with the original extension
        assert result.endswith(long_extension)
        # Name part should be truncated appropriately
        expected_name_len = 255 - len(long_extension)
        name_part = result[: -len(long_extension)]
        assert len(name_part) == expected_name_len
        assert name_part == "b" * expected_name_len

    def test_sanitize_filename_exactly_256_chars(self):
        """Test sanitize_filename with exactly 256 characters (edge case)."""
        # Create exactly 256 character filename
        name_part = "c" * 252
        extension = ".doc"  # 4 chars
        filename_256 = name_part + extension  # Exactly 256 chars

        assert len(filename_256) == 256

        result = sanitize_filename(filename_256)

        # Should be truncated to exactly 255
        assert len(result) == 255
        assert result.endswith(extension)
        # Name should be truncated by 1 character
        expected_name = "c" * 251  # 252 - 1 = 251
        assert result.startswith(expected_name)

    def test_sanitize_filename_over_255_no_extension(self):
        """Test sanitize_filename with over 255 chars but no extension."""
        # Create filename with no extension over 255 chars
        long_filename_no_ext = "d" * 260

        result = sanitize_filename(long_filename_no_ext)

        # Should be truncated to 255 chars
        assert len(result) == 255
        # Should be all 'd' characters
        assert result == "d" * 255
        # Verify the Path logic works even without extension
        assert "." not in result  # No extension added

    def test_sanitize_filename_over_255_empty_extension(self):
        """Test sanitize_filename with filename ending with dot but no extension."""
        # Create filename ending with dot (empty extension)
        long_name_with_dot = "e" * 254 + "."  # 255 chars ending with dot

        result = sanitize_filename(long_name_with_dot)

        # Should handle empty extension case
        # Since it's already at 255 chars, no truncation needed
        assert len(result) == 255
        assert result.endswith(".")

    def test_sanitize_filename_multiple_dots_over_255(self):
        """Test sanitize_filename with multiple dots and over 255 chars."""
        # Test case with multiple dots (only last one should be considered extension)
        long_name = "f" * 248 + ".backup.txt"  # > 255 chars with multiple dots

        result = sanitize_filename(long_name)

        assert len(result) == 255
        assert result.endswith(".txt")  # Should preserve the final extension
        # The stem should include the .backup part
        expected_stem_len = 255 - 4  # 255 - len(".txt")
        stem_part = result[:-4]
        assert len(stem_part) == expected_stem_len
        assert ".backup" in stem_part  # Should include the .backup part in stem
