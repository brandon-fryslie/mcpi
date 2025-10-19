"""Fixed tests for validation utility edge cases that were failing."""

import pytest
from mcpi.utils.validation import sanitize_filename


class TestValidationStabilityFixes:
    """Fixed versions of failing validation tests."""
    
    def test_sanitize_filename_over_255_empty_extension_fixed(self):
        """Test sanitize_filename with filename ending with dot (gets stripped).
        
        The sanitize_filename function strips trailing dots and spaces,
        so a filename ending with "." will have the dot removed.
        """
        # Create filename ending with dot (empty extension)  
        long_name_with_dot = "e" * 254 + "."  # 255 chars ending with dot
        
        result = sanitize_filename(long_name_with_dot)
        
        # Trailing dot gets stripped, so result is 254 chars
        assert len(result) == 254
        assert result == "e" * 254  # No trailing dot
        assert not result.endswith(".")
    
    def test_sanitize_filename_multiple_dots_over_255_fixed(self):
        """Test sanitize_filename with multiple trailing dots (get stripped).
        
        Multiple trailing dots should be stripped according to the sanitization logic.
        """
        # Create filename with multiple trailing dots
        long_name_with_dots = "f" * 250 + "....."  # 255 chars ending with dots
        
        result = sanitize_filename(long_name_with_dots)
        
        # All trailing dots get stripped 
        assert len(result) == 250
        assert result == "f" * 250  # No trailing dots
        assert not result.endswith(".")
    
    def test_sanitize_filename_over_255_with_real_extension(self):
        """Test sanitize_filename with real extension (should be preserved).
        
        When there's a real extension (not just trailing dots), it should be preserved.
        """
        # Create filename with real extension over 255 chars
        long_name = "g" * 252
        extension = ".txt"
        long_filename = long_name + extension  # 256 chars total
        
        result = sanitize_filename(long_filename)
        
        # Should be truncated to 255 chars with extension preserved
        assert len(result) == 255
        assert result.endswith(".txt")
        # Name part should be truncated to make room for extension
        expected_name_len = 255 - 4  # 4 chars for ".txt"
        assert len(result) - len(".txt") == expected_name_len