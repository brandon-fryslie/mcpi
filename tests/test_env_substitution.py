"""Tests for environment variable substitution utilities."""

import os
from unittest.mock import patch

import pytest

from mcpi.utils.env_substitution import (
    substitute_env_vars,
    substitute_env_vars_in_dict,
    substitute_headers,
    has_env_var_reference,
    get_referenced_env_vars,
    check_missing_env_vars,
)


class TestSubstituteEnvVars:
    """Tests for substitute_env_vars function."""

    def test_simple_substitution(self):
        """Test basic ${VAR} substitution."""
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            result = substitute_env_vars("Bearer ${API_KEY}")
            assert result == "Bearer secret123"

    def test_multiple_vars(self):
        """Test multiple variables in one string."""
        with patch.dict(os.environ, {"USER": "alice", "TOKEN": "abc123"}):
            result = substitute_env_vars("${USER}:${TOKEN}")
            assert result == "alice:abc123"

    def test_missing_var_becomes_empty(self):
        """Test that missing vars become empty strings."""
        with patch.dict(os.environ, {}, clear=True):
            result = substitute_env_vars("prefix${MISSING}suffix")
            assert result == "prefixsuffix"

    def test_default_value(self):
        """Test ${VAR:-default} syntax."""
        with patch.dict(os.environ, {}, clear=True):
            result = substitute_env_vars("${MISSING:-fallback}")
            assert result == "fallback"

    def test_default_not_used_when_set(self):
        """Test that default is ignored when var is set."""
        with patch.dict(os.environ, {"PRESENT": "actual"}):
            result = substitute_env_vars("${PRESENT:-fallback}")
            assert result == "actual"

    def test_empty_default(self):
        """Test ${VAR:-} with empty default."""
        with patch.dict(os.environ, {}, clear=True):
            result = substitute_env_vars("${MISSING:-}")
            assert result == ""

    def test_no_vars(self):
        """Test string without any variables."""
        result = substitute_env_vars("plain text")
        assert result == "plain text"

    def test_partial_match_not_substituted(self):
        """Test that incomplete patterns are not matched."""
        result = substitute_env_vars("$VAR and ${incomplete")
        assert result == "$VAR and ${incomplete"

    def test_underscore_in_var_name(self):
        """Test variables with underscores."""
        with patch.dict(os.environ, {"MY_API_KEY": "key123"}):
            result = substitute_env_vars("${MY_API_KEY}")
            assert result == "key123"

    def test_numbers_in_var_name(self):
        """Test variables with numbers (not at start)."""
        with patch.dict(os.environ, {"API_KEY_2": "key2"}):
            result = substitute_env_vars("${API_KEY_2}")
            assert result == "key2"


class TestSubstituteEnvVarsInDict:
    """Tests for substitute_env_vars_in_dict function."""

    def test_simple_dict(self):
        """Test substitution in simple dict."""
        with patch.dict(os.environ, {"KEY": "value"}):
            data = {"header": "${KEY}"}
            result = substitute_env_vars_in_dict(data)
            assert result == {"header": "value"}

    def test_nested_dict(self):
        """Test substitution in nested dict."""
        with patch.dict(os.environ, {"INNER": "innerval"}):
            data = {"outer": {"inner": "${INNER}"}}
            result = substitute_env_vars_in_dict(data)
            assert result == {"outer": {"inner": "innerval"}}

    def test_list_values(self):
        """Test substitution in list values."""
        with patch.dict(os.environ, {"VAL": "replaced"}):
            data = {"items": ["${VAL}", "plain", "${VAL}"]}
            result = substitute_env_vars_in_dict(data)
            assert result == {"items": ["replaced", "plain", "replaced"]}

    def test_non_string_values_unchanged(self):
        """Test that non-string values are preserved."""
        data = {"count": 42, "enabled": True, "ratio": 3.14}
        result = substitute_env_vars_in_dict(data)
        assert result == data

    def test_original_dict_unchanged(self):
        """Test that original dict is not modified."""
        with patch.dict(os.environ, {"KEY": "value"}):
            original = {"header": "${KEY}"}
            result = substitute_env_vars_in_dict(original)
            assert original == {"header": "${KEY}"}
            assert result == {"header": "value"}


class TestSubstituteHeaders:
    """Tests for substitute_headers function."""

    def test_authorization_header(self):
        """Test typical Authorization header pattern."""
        with patch.dict(os.environ, {"API_KEY": "sk-12345"}):
            headers = {"Authorization": "Bearer ${API_KEY}"}
            result = substitute_headers(headers)
            assert result == {"Authorization": "Bearer sk-12345"}

    def test_multiple_headers(self):
        """Test multiple headers with variables."""
        with patch.dict(os.environ, {"TOKEN": "abc", "USER": "bob"}):
            headers = {
                "Authorization": "Bearer ${TOKEN}",
                "X-User": "${USER}",
            }
            result = substitute_headers(headers)
            assert result == {
                "Authorization": "Bearer abc",
                "X-User": "bob",
            }

    def test_headers_without_vars(self):
        """Test headers without any variables."""
        headers = {"Content-Type": "application/json"}
        result = substitute_headers(headers)
        assert result == {"Content-Type": "application/json"}

    def test_original_headers_unchanged(self):
        """Test that original headers dict is not modified."""
        with patch.dict(os.environ, {"KEY": "value"}):
            original = {"Auth": "${KEY}"}
            result = substitute_headers(original)
            assert original == {"Auth": "${KEY}"}
            assert result == {"Auth": "value"}


class TestHasEnvVarReference:
    """Tests for has_env_var_reference function."""

    def test_with_reference(self):
        """Test detection of env var reference."""
        assert has_env_var_reference("Bearer ${API_KEY}") is True

    def test_without_reference(self):
        """Test no false positives."""
        assert has_env_var_reference("plain text") is False

    def test_partial_pattern(self):
        """Test incomplete patterns are not matched."""
        assert has_env_var_reference("$VAR") is False
        assert has_env_var_reference("${incomplete") is False


class TestGetReferencedEnvVars:
    """Tests for get_referenced_env_vars function."""

    def test_single_var(self):
        """Test extracting single variable."""
        result = get_referenced_env_vars("Bearer ${API_KEY}")
        assert result == ["API_KEY"]

    def test_multiple_vars(self):
        """Test extracting multiple variables."""
        result = get_referenced_env_vars("${USER}:${TOKEN}")
        assert result == ["USER", "TOKEN"]

    def test_no_vars(self):
        """Test empty result for no variables."""
        result = get_referenced_env_vars("plain text")
        assert result == []

    def test_duplicate_vars(self):
        """Test that duplicates are included (for checking)."""
        result = get_referenced_env_vars("${VAR} and ${VAR}")
        assert result == ["VAR", "VAR"]


class TestCheckMissingEnvVars:
    """Tests for check_missing_env_vars function."""

    def test_all_present(self):
        """Test no missing vars when all are set."""
        with patch.dict(os.environ, {"API_KEY": "secret"}):
            headers = {"Auth": "Bearer ${API_KEY}"}
            result = check_missing_env_vars(headers)
            assert result == []

    def test_missing_vars(self):
        """Test detection of missing vars."""
        with patch.dict(os.environ, {}, clear=True):
            headers = {"Auth": "Bearer ${MISSING_KEY}"}
            result = check_missing_env_vars(headers)
            assert result == ["MISSING_KEY"]

    def test_some_missing(self):
        """Test partial missing vars."""
        with patch.dict(os.environ, {"PRESENT": "value"}, clear=True):
            headers = {
                "Auth": "${PRESENT}",
                "Other": "${MISSING}",
            }
            result = check_missing_env_vars(headers)
            assert result == ["MISSING"]

    def test_no_duplicates_in_result(self):
        """Test that missing vars are not duplicated in result."""
        with patch.dict(os.environ, {}, clear=True):
            headers = {
                "Auth": "${MISSING}",
                "Other": "${MISSING}",
            }
            result = check_missing_env_vars(headers)
            assert result == ["MISSING"]
