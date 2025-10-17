"""Tests for evaluation discovery functionality."""

import pytest
from pathlib import Path

from agentci.client_config import discover_evaluations, EvaluationType, config


class TestEvaluationDiscovery:
    """Test evaluation discovery functionality."""

    @pytest.fixture
    def repo_with_evals(self, tmp_path):
        """Create a temporary repository with evals."""
        # Create the evaluation directory structure using config
        evals_dir = tmp_path / config.evaluation_path_name
        evals_dir.mkdir(parents=True)

        # Copy test fixtures
        fixtures_path = Path(__file__).parent / "fixtures" / "evals"
        for toml_file in fixtures_path.glob("*.toml"):
            (evals_dir / toml_file.name).write_text(toml_file.read_text())

        return tmp_path

    @pytest.fixture
    def empty_repo(self, tmp_path):
        """Create a temporary repository without evals."""
        return tmp_path

    @pytest.fixture
    def repo_no_evals_dir(self, tmp_path):
        """Create a temporary repository without evals directory."""
        return tmp_path

    def test_discover_evaluations_success(self, repo_with_evals):
        """Test successful evaluation discovery."""
        evaluations = discover_evaluations(repo_with_evals)

        # Should find all 7 evaluation files
        assert len(evaluations) == 7

        # Check evaluation names match filenames (without .toml)
        eval_names = {eval.name for eval in evaluations}
        assert eval_names == {
            "accuracy_test",
            "performance_test",
            "safety_template_test",
            "safety_custom_test",
            "consistency_test",
            "llm_test",
            "custom_test",
        }

        # Check types are parsed correctly
        eval_types = {eval.type for eval in evaluations}
        assert eval_types == {
            EvaluationType.ACCURACY,
            EvaluationType.PERFORMANCE,
            EvaluationType.SAFETY,
            EvaluationType.CONSISTENCY,
            EvaluationType.LLM,
            EvaluationType.CUSTOM,
        }

    def test_discover_evaluations_no_directory(self, repo_no_evals_dir):
        """Test discovery when evals directory doesn't exist."""
        evaluations = discover_evaluations(repo_no_evals_dir)

        assert len(evaluations) == 0

    def test_discover_evaluations_empty_directory(self, empty_repo):
        """Test discovery with empty evals directory."""
        # Create empty evals directory
        evals_dir = empty_repo / config.evaluation_path_name
        evals_dir.mkdir(parents=True)

        evaluations = discover_evaluations(empty_repo)

        assert len(evaluations) == 0

    def test_get_evaluations_for_agent(self, repo_with_evals):
        """Test filtering evaluations that target specific agents."""
        evaluations = discover_evaluations(repo_with_evals)

        # All test evals target "*" (all agents)
        evals_for_any_agent = [e for e in evaluations if e.targets.targets_agent("test_agent")]
        assert len(evals_for_any_agent) == 7  # All evals should target this agent

        # Test with specific agent targeting
        evals_dir = repo_with_evals / config.evaluation_path_name
        specific_toml = evals_dir / "specific_agent_test.toml"
        specific_toml.write_text(
            """
[eval]
description = "Test specific agent"
type = "accuracy"
targets.agents = ["specific_agent"]
targets.tools = []

[[eval.cases]]
prompt = "Test"
output = "Expected"
        """
        )

        # Re-discover to pick up new file
        evaluations = discover_evaluations(repo_with_evals)

        evals_for_specific = [e for e in evaluations if e.targets.targets_agent("specific_agent")]
        evals_for_other = [e for e in evaluations if e.targets.targets_agent("other_agent")]

        # specific_agent should get both wildcard evals + specific eval
        assert len(evals_for_specific) == 8
        # other_agent should only get wildcard evals
        assert len(evals_for_other) == 7

    def test_get_evaluations_for_tool(self, repo_with_evals):
        """Test filtering evaluations that target specific tools."""
        evaluations = discover_evaluations(repo_with_evals)

        # Default test evals target agents only, not tools
        evals_for_tool = [e for e in evaluations if e.targets.targets_tool("test_tool")]
        assert len(evals_for_tool) == 0

        # Add a tool-specific evaluation
        evals_dir = repo_with_evals / config.evaluation_path_name
        tool_toml = evals_dir / "tool_test.toml"
        tool_toml.write_text(
            """
[eval]
description = "Test tool"
type = "accuracy"
targets.agents = []
targets.tools = ["*"]

[[eval.cases]]
context = { param = "value" }
output = "Expected"
        """
        )

        # Re-discover to pick up new file
        evaluations = discover_evaluations(repo_with_evals)

        evals_for_tool = [e for e in evaluations if e.targets.targets_tool("test_tool")]
        assert len(evals_for_tool) == 1

    def test_validate_evaluation_configs_success(self, repo_with_evals):
        """Test validation of all evaluation configurations."""
        from agentci.client_config import validate_evaluation_configs

        # All fixture configs should be valid
        assert validate_evaluation_configs(repo_with_evals) is True

    def test_validate_evaluation_configs_failure(self, tmp_path):
        """Test validation with invalid configuration."""
        from agentci.client_config import validate_evaluation_configs

        # Create evals directory with invalid TOML
        evals_dir = tmp_path / config.evaluation_path_name
        evals_dir.mkdir(parents=True)

        invalid_toml = evals_dir / "invalid.toml"
        invalid_toml.write_text(
            """
[eval]
description = "Invalid config"
type = "accuracy"
# Missing targets - should cause validation error
        """
        )

        # Should return False due to invalid config
        assert validate_evaluation_configs(tmp_path) is False

    def test_config_path_customization(self):
        """Test that evaluation path can be customized via environment variable."""
        import os
        import importlib

        # Set environment variable BEFORE reloading the module
        os.environ["AGENTCI_CLIENT_BASE_PATH"] = ".custom"

        # Reload the config module to pick up the new env var
        import agentci.client_config._config
        importlib.reload(agentci.client_config._config)

        from agentci.client_config._config import config as custom_config

        # Verify config uses the custom env var
        assert custom_config.client_base_path == ".custom"
        assert custom_config.evaluation_path_name == ".custom/evals"
