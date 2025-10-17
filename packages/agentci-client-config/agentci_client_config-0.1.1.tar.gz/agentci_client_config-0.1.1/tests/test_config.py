"""Tests for evaluation configuration parsing and validation."""

import pytest
from pathlib import Path

from agentci.client_config import (
    EvaluationType,
    EvaluationTargets,
    LatencyThreshold,
    EvaluationConfig,
    EvaluationCase,
    StringMatch,
    parse_evaluation_config_toml,
)


class TestEvaluationTargets:
    """Test evaluation targeting functionality."""

    def test_wildcard_agent_targeting(self):
        """Test wildcard agent targeting."""
        targets = EvaluationTargets(agents=["*"], tools=[])

        assert targets.targets_agent("any_agent")
        assert targets.targets_agent("another_agent")
        assert not targets.targets_tool("any_tool")

    def test_specific_agent_targeting(self):
        """Test specific agent targeting."""
        targets = EvaluationTargets(agents=["agent1", "agent2"], tools=[])

        assert targets.targets_agent("agent1")
        assert targets.targets_agent("agent2")
        assert not targets.targets_agent("agent3")
        assert not targets.targets_tool("any_tool")

    def test_wildcard_tool_targeting(self):
        """Test wildcard tool targeting."""
        targets = EvaluationTargets(agents=[], tools=["*"])

        assert targets.targets_tool("any_tool")
        assert targets.targets_tool("another_tool")
        assert not targets.targets_agent("any_agent")

    def test_specific_tool_targeting(self):
        """Test specific tool targeting."""
        targets = EvaluationTargets(agents=[], tools=["tool1", "tool2"])

        assert targets.targets_tool("tool1")
        assert targets.targets_tool("tool2")
        assert not targets.targets_tool("tool3")
        assert not targets.targets_agent("any_agent")


class TestLatencyThreshold:
    """Test latency threshold normalization."""

    def test_milliseconds_to_seconds_conversion(self):
        """Test that millisecond values are converted to seconds."""
        # Test max_ms conversion
        threshold1 = LatencyThreshold(max_ms=3000)
        assert threshold1.max == 3.0
        assert not hasattr(threshold1, "max_ms") or threshold1.max_ms is None

        # Test min_ms conversion
        threshold2 = LatencyThreshold(min_ms=500)
        assert threshold2.min == 0.5
        assert not hasattr(threshold2, "min_ms") or threshold2.min_ms is None

        # Test both conversions
        threshold3 = LatencyThreshold(min_ms=100, max_ms=5000)
        assert threshold3.min == 0.1
        assert threshold3.max == 5.0

    def test_seconds_values_preserved(self):
        """Test that second values are preserved as-is."""
        threshold = LatencyThreshold(min=1.0, max=10.0, equal=5.0)
        assert threshold.min == 1.0
        assert threshold.max == 10.0
        assert threshold.equal == 5.0

    def test_mixed_units_priority(self):
        """Test that explicit seconds take priority over milliseconds."""
        # When both are specified, seconds should win
        threshold = LatencyThreshold(min=2.0, min_ms=1000, max=8.0, max_ms=5000)
        assert threshold.min == 2.0  # seconds value preserved
        assert threshold.max == 8.0  # seconds value preserved


class TestEvaluationConfig:
    """Test evaluation configuration validation."""

    def test_valid_accuracy_config(self):
        """Test valid accuracy configuration."""
        config = EvaluationConfig(
            name="test_accuracy",
            file_path="test_accuracy.toml",
            description="Test accuracy",
            type=EvaluationType.ACCURACY,
            targets=EvaluationTargets(agents=["test_agent"]),
            cases=[{"prompt": "Test prompt", "output": "Expected output"}],
        )
        assert config.type == EvaluationType.ACCURACY
        assert len(config.cases) == 1
        assert config.cases[0].prompt == "Test prompt"
        # Verify bare string is converted to StringMatch
        assert isinstance(config.cases[0].output, StringMatch)
        assert config.cases[0].output.exact == "Expected output"

    def test_accuracy_with_stringmatch_contains(self):
        """Test accuracy configuration with StringMatch contains strategy."""
        config = EvaluationConfig(
            name="test_accuracy",
            file_path="test_accuracy.toml",
            description="Test accuracy",
            type=EvaluationType.ACCURACY,
            targets=EvaluationTargets(agents=["test_agent"]),
            cases=[{"prompt": "Test prompt", "output": {"contains": "Paris"}}],
        )
        assert isinstance(config.cases[0].output, StringMatch)
        assert config.cases[0].output.contains == "Paris"

    def test_accuracy_with_stringmatch_contains_all(self):
        """Test accuracy configuration with contains (ALL semantics)."""
        config = EvaluationConfig(
            name="test_accuracy",
            file_path="test_accuracy.toml",
            description="Test accuracy",
            type=EvaluationType.ACCURACY,
            targets=EvaluationTargets(agents=["test_agent"]),
            cases=[{"prompt": "Test prompt", "output": {"contains": ["Paris", "France", "Europe"]}}],
        )
        assert isinstance(config.cases[0].output, StringMatch)
        assert config.cases[0].output.contains == ["Paris", "France", "Europe"]

    def test_accuracy_with_stringmatch_contains_any(self):
        """Test accuracy configuration with contains_any (ANY semantics)."""
        config = EvaluationConfig(
            name="test_accuracy",
            file_path="test_accuracy.toml",
            description="Test accuracy",
            type=EvaluationType.ACCURACY,
            targets=EvaluationTargets(agents=["test_agent"]),
            cases=[{"prompt": "Test prompt", "output": {"contains_any": ["Paris", "France", "Europe"]}}],
        )
        assert isinstance(config.cases[0].output, StringMatch)
        assert config.cases[0].output.contains_any == ["Paris", "France", "Europe"]

    def test_accuracy_with_stringmatch_regex(self):
        """Test accuracy configuration with regex pattern matching."""
        config = EvaluationConfig(
            name="test_accuracy",
            file_path="test_accuracy.toml",
            description="Test accuracy",
            type=EvaluationType.ACCURACY,
            targets=EvaluationTargets(agents=["test_agent"]),
            cases=[{"prompt": "Test prompt", "output": {"match": r"^\d{3}-\d{3}-\d{4}$"}}],
        )
        assert isinstance(config.cases[0].output, StringMatch)
        assert config.cases[0].output.match == r"^\d{3}-\d{3}-\d{4}$"

    def test_accuracy_with_stringmatch_semantic(self):
        """Test accuracy configuration with semantic similarity matching."""
        config = EvaluationConfig(
            name="test_accuracy",
            file_path="test_accuracy.toml",
            description="Test accuracy",
            type=EvaluationType.ACCURACY,
            targets=EvaluationTargets(agents=["test_agent"]),
            cases=[{"prompt": "Test prompt", "output": {"similar": "Paris is the capital", "threshold": 0.8}}],
        )
        assert isinstance(config.cases[0].output, StringMatch)
        assert config.cases[0].output.similar == "Paris is the capital"
        assert config.cases[0].output.threshold == 0.8

    def test_accuracy_with_stringmatch_instance(self):
        """Test accuracy configuration with output already as StringMatch instance."""
        # When output is already a StringMatch object, it should be preserved
        string_match = StringMatch(contains="Paris")
        case = EvaluationCase(prompt="Test prompt", output=string_match)
        assert isinstance(case.output, StringMatch)
        assert case.output.contains == "Paris"

    def test_invalid_no_targets(self):
        """Test that config requires at least one target."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_invalid",
                file_path="test_invalid.toml",
                description="Invalid config",
                type=EvaluationType.ACCURACY,
                targets=EvaluationTargets(agents=[], tools=[]),
                cases=[{"prompt": "Test", "output": "Output"}],
            )

    def test_invalid_iterations(self):
        """Test that iterations must be >= 1."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_invalid",
                file_path="test_invalid.toml",
                description="Invalid iterations",
                type=EvaluationType.ACCURACY,
                targets=EvaluationTargets(agents=["test"]),
                iterations=0,
                cases=[{"prompt": "Test", "output": "Output"}],
            )

    def test_llm_requires_config(self):
        """Test that LLM evaluations require LLM configuration."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_llm",
                file_path="test_llm.toml",
                description="LLM without config",
                type=EvaluationType.LLM,
                targets=EvaluationTargets(agents=["test"]),
                cases=[{"prompt": "Test", "score": {"min": 7}}],
            )

    def test_custom_requires_config(self):
        """Test that custom evaluations require custom configuration."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_custom",
                file_path="test_custom.toml",
                description="Custom without config",
                type=EvaluationType.CUSTOM,
                targets=EvaluationTargets(agents=["test"]),
                cases=[{"prompt": "Test", "parameters": {}}],
            )

    def test_accuracy_case_validation(self):
        """Test accuracy case validation."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_accuracy",
                file_path="test_accuracy.toml",
                description="Accuracy missing output",
                type=EvaluationType.ACCURACY,
                targets=EvaluationTargets(agents=["test"]),
                cases=[{"prompt": "Test"}],  # Missing output
            )

    def test_performance_case_validation(self):
        """Test performance case validation."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_performance",
                file_path="test_performance.toml",
                description="Performance missing thresholds",
                type=EvaluationType.PERFORMANCE,
                targets=EvaluationTargets(agents=["test"]),
                cases=[{"prompt": "Test"}],  # Missing latency/tokens
            )

    def test_consistency_case_validation(self):
        """Test consistency case validation - min_similarity is optional (defaults to 1.0 in runner)."""
        # min_similarity is optional, so this should succeed
        config = EvaluationConfig(
            name="test_consistency",
            file_path="test_consistency.toml",
            description="Consistency with optional similarity",
            type=EvaluationType.CONSISTENCY,
            targets=EvaluationTargets(agents=["test"]),
            cases=[{"prompt": "Test"}],  # min_similarity optional
        )
        assert config.type == EvaluationType.CONSISTENCY
        assert config.cases[0].min_similarity is None  # Will default to 1.0 in runner

    def test_safety_case_validation(self):
        """Test safety case validation."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_safety",
                file_path="test_safety.toml",
                description="Safety missing blocked",
                type=EvaluationType.SAFETY,
                targets=EvaluationTargets(agents=["test"]),
                cases=[{"prompt": "Test"}],  # Missing blocked
            )

    def test_safety_requires_template_or_cases(self):
        """Test that safety evaluations require either template or cases."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_safety",
                file_path="test_safety.toml",
                description="Safety without template or cases",
                type=EvaluationType.SAFETY,
                targets=EvaluationTargets(agents=["test"]),
                cases=[],  # Empty cases and no template
            )

    def test_accuracy_requires_cases(self):
        """Test that accuracy evaluations require test cases."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_accuracy",
                file_path="test_accuracy.toml",
                description="Accuracy without cases",
                type=EvaluationType.ACCURACY,
                targets=EvaluationTargets(agents=["test"]),
                cases=[],  # Empty cases
            )

    def test_llm_case_requires_score(self):
        """Test that LLM evaluation cases require score thresholds."""
        with pytest.raises(ValueError):
            EvaluationConfig(
                name="test_llm",
                file_path="test_llm.toml",
                description="LLM case without score",
                type=EvaluationType.LLM,
                targets=EvaluationTargets(agents=["test"]),
                llm={"model": "gpt-4", "prompt": "Evaluate this"},
                cases=[{"prompt": "Test"}],  # Missing score
            )


class TestTOMLParsing:
    """Test TOML file parsing."""

    @pytest.fixture
    def fixtures_path(self):
        """Get path to test fixtures."""
        return Path(__file__).parent / "fixtures" / "evals"

    def test_parse_accuracy_toml(self, fixtures_path):
        """Test parsing accuracy evaluation TOML."""
        toml_path = fixtures_path / "accuracy_test.toml"
        repo_path = fixtures_path.parent.parent

        parsed = parse_evaluation_config_toml(toml_path, repo_path)

        assert parsed.name == "accuracy_test"
        assert parsed.type == EvaluationType.ACCURACY
        assert parsed.description == "Test response accuracy"
        assert len(parsed.cases) == 9  # Now includes dotted syntax examples
        assert parsed.targets.agents == ["*"]
        assert parsed.targets.tools == []

        # Verify dotted syntax is parsed correctly
        # Case 2 uses dotted syntax: output.contains = "capital"
        assert parsed.cases[2].output.contains == "capital"
        # Case 3 and 4 use contains_any: output.contains_any = [...]
        assert parsed.cases[3].output.contains_any == ["sunny", "cloudy", "rainy", "temperature"]
        assert parsed.cases[4].output.contains_any == ["sunny", "cloudy", "rainy", "temperature"]
        # Case 5 uses dotted syntax: output.startswith = [...]
        assert parsed.cases[5].output.startswith == ["Hello", "Hi", "Hey"]
        # Case 6 uses dotted syntax: output.match = "..."
        assert parsed.cases[6].output.match == "^\\d{3}-\\d{3}-\\d{4}$"
        # Case 7 uses dotted syntax: output.similar + output.threshold
        assert parsed.cases[7].output.similar == "The capital city of France is Paris."
        assert parsed.cases[7].output.threshold == 0.75

        # Case 8 uses nested table syntax: [eval.cases.output.schema]
        assert isinstance(parsed.cases[8].output, StringMatch)
        assert parsed.cases[8].output.schema is not None
        assert len(parsed.cases[8].output.schema) == 3
        assert "temperature" in parsed.cases[8].output.schema
        assert "condition" in parsed.cases[8].output.schema
        assert "humidity" in parsed.cases[8].output.schema
        assert parsed.cases[8].output.schema["temperature"].type == "float"
        assert parsed.cases[8].output.schema["condition"].type == "str"
        assert parsed.cases[8].output.schema["humidity"].type == "int"
        assert parsed.cases[8].output.schema["humidity"].min == 0
        assert parsed.cases[8].output.schema["humidity"].max == 100

    def test_parse_performance_toml(self, fixtures_path):
        """Test parsing performance evaluation TOML with time normalization."""
        toml_path = fixtures_path / "performance_test.toml"
        repo_path = fixtures_path.parent.parent

        parsed = parse_evaluation_config_toml(toml_path, repo_path)

        assert parsed.type == EvaluationType.PERFORMANCE
        assert len(parsed.cases) == 3

        # Check first case - max_ms should be converted to seconds
        case1 = parsed.cases[0]
        assert case1.latency.max == 3.0  # 3000ms -> 3.0s

        # Check second case - max in seconds should be preserved
        case2 = parsed.cases[1]
        assert case2.latency.max == 15.0
        assert case2.tokens.max == 2000

    def test_parse_llm_toml(self, fixtures_path):
        """Test parsing LLM evaluation TOML."""
        toml_path = fixtures_path / "llm_test.toml"
        repo_path = fixtures_path.parent.parent

        parsed = parse_evaluation_config_toml(toml_path, repo_path)

        assert parsed.type == EvaluationType.LLM
        assert parsed.llm is not None
        assert parsed.llm.model == "gpt-4"
        assert "Evaluate the helpfulness" in parsed.llm.prompt
        assert len(parsed.cases) == 3

    def test_parse_safety_template_toml(self, fixtures_path):
        """Test parsing safety evaluation with template."""
        toml_path = fixtures_path / "safety_template_test.toml"
        repo_path = fixtures_path.parent.parent

        parsed = parse_evaluation_config_toml(toml_path, repo_path)

        assert parsed.type == EvaluationType.SAFETY
        assert parsed.template == "prompt_injection"
        assert len(parsed.cases) == 0  # Template-only

    def test_parse_safety_custom_toml(self, fixtures_path):
        """Test parsing safety evaluation with custom cases."""
        toml_path = fixtures_path / "safety_custom_test.toml"
        repo_path = fixtures_path.parent.parent

        parsed = parse_evaluation_config_toml(toml_path, repo_path)

        assert parsed.type == EvaluationType.SAFETY
        assert parsed.template is None
        assert len(parsed.cases) == 2
        assert parsed.cases[0].blocked is True
        assert parsed.cases[1].blocked is False

    def test_parse_consistency_toml(self, fixtures_path):
        """Test parsing consistency evaluation TOML."""
        toml_path = fixtures_path / "consistency_test.toml"
        repo_path = fixtures_path.parent.parent

        parsed = parse_evaluation_config_toml(toml_path, repo_path)

        assert parsed.type == EvaluationType.CONSISTENCY
        assert parsed.iterations == 5
        assert len(parsed.cases) == 3
        assert parsed.cases[0].min_similarity == 1.0
        assert parsed.cases[1].min_similarity == 0.8

    def test_parse_custom_toml(self, fixtures_path):
        """Test parsing custom evaluation TOML."""
        toml_path = fixtures_path / "custom_test.toml"
        repo_path = fixtures_path.parent.parent

        parsed = parse_evaluation_config_toml(toml_path, repo_path)

        assert parsed.type == EvaluationType.CUSTOM
        assert parsed.custom is not None
        assert parsed.custom.module == "my_evaluations.advanced_logic"
        assert parsed.custom.function == "evaluate_response"
        assert len(parsed.cases) == 2

    def test_invalid_toml_missing_eval_section(self, fixtures_path, tmp_path):
        """Test error handling for invalid TOML files."""
        invalid_toml = tmp_path / "invalid.toml"
        invalid_toml.write_text("""
[invalid]
description = "Missing eval section"
        """)

        with pytest.raises(ValueError):
            parse_evaluation_config_toml(invalid_toml, tmp_path)
