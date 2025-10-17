"""Tests for StringMatch schema."""

import pytest
from agentci.client_config import StringMatch


class TestStringMatchCreation:
    """Test StringMatch object creation."""

    def test_exact_match(self):
        """Test exact string matching."""
        match = StringMatch(exact="test string")
        assert match.exact == "test string"
        assert match.contains is None
        assert match.startswith is None
        assert match.endswith is None
        assert match.match is None
        assert match.similar is None

    def test_contains_single(self):
        """Test contains with single string."""
        match = StringMatch(contains="substring")
        assert match.contains == "substring"
        assert match.exact is None

    def test_contains_multiple(self):
        """Test contains with multiple strings (ALL semantics)."""
        match = StringMatch(contains=["foo", "bar", "baz"])
        assert match.contains == ["foo", "bar", "baz"]

    def test_contains_any(self):
        """Test contains_any with multiple strings (ANY semantics)."""
        match = StringMatch(contains_any=["foo", "bar", "baz"])
        assert match.contains_any == ["foo", "bar", "baz"]
        assert match.exact is None
        assert match.contains is None

    def test_startswith_single(self):
        """Test startswith with single string."""
        match = StringMatch(startswith="prefix")
        assert match.startswith == "prefix"

    def test_startswith_multiple(self):
        """Test startswith with multiple strings."""
        match = StringMatch(startswith=["Hello", "Hi", "Hey"])
        assert match.startswith == ["Hello", "Hi", "Hey"]

    def test_endswith_single(self):
        """Test endswith with single string."""
        match = StringMatch(endswith="suffix")
        assert match.endswith == "suffix"

    def test_endswith_multiple(self):
        """Test endswith with multiple strings."""
        match = StringMatch(endswith=["!", "?", "."])
        assert match.endswith == ["!", "?", "."]

    def test_regex_match(self):
        """Test regex pattern matching."""
        match = StringMatch(match=r"^\d{3}-\d{3}-\d{4}$")
        assert match.match == r"^\d{3}-\d{3}-\d{4}$"

    def test_semantic_similarity(self):
        """Test semantic similarity matching."""
        match = StringMatch(similar="reference text", threshold=0.8)
        assert match.similar == "reference text"
        assert match.threshold == 0.8


class TestStringMatchFactory:
    """Test StringMatch.from_string() factory method."""

    def test_from_string(self):
        """Test creating StringMatch from bare string."""
        match = StringMatch.from_string("test")
        assert match.exact == "test"
        assert match.contains is None
        assert match.startswith is None


class TestStringMatchValidation:
    """Test StringMatch validation rules."""

    def test_single_strategy_required(self):
        """Test that at least one strategy must be specified."""
        with pytest.raises(ValueError):
            StringMatch()

    def test_only_one_strategy_allowed(self):
        """Test that only one strategy can be specified."""
        with pytest.raises(ValueError):
            StringMatch(exact="test", contains="other")

    def test_multiple_strategies_not_allowed(self):
        """Test that multiple strategies are rejected."""
        with pytest.raises(ValueError):
            StringMatch(startswith="prefix", endswith="suffix")

    def test_contains_and_contains_any_conflict(self):
        """Test that contains and contains_any cannot both be specified."""
        with pytest.raises(ValueError):
            StringMatch(contains="foo", contains_any=["bar"])

    def test_semantic_requires_threshold(self):
        """Test that semantic similarity requires threshold."""
        with pytest.raises(ValueError):
            StringMatch(similar="reference text")

    def test_threshold_requires_similar(self):
        """Test that threshold can only be used with similar."""
        with pytest.raises(ValueError):
            StringMatch(exact="test", threshold=0.8)

    def test_threshold_bounds(self):
        """Test that threshold must be between 0.0 and 1.0."""
        with pytest.raises(ValueError):
            StringMatch(similar="reference", threshold=1.5)

        with pytest.raises(ValueError):
            StringMatch(similar="reference", threshold=-0.1)
