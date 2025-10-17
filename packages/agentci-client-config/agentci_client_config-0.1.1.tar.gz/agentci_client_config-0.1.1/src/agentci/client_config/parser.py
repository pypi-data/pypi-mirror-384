from __future__ import annotations
from pathlib import Path
import tomllib

from agentci.client_config import config
from agentci.client_config.schema import EvaluationConfig


DISCOVER_EXTENSIONS: list[str] = [
    "toml",
]


def discover_evaluations(repository_path: Path) -> list[EvaluationConfig]:
    """Discover all evaluation configurations in the repository.

    Args:
        repository_path: Root path of the repository.

    Returns:
        List of parsed EvaluationConfig objects.

    Raises:
        ValueError: If any evaluation configuration file fails to parse or validate.
    """
    eval_path = repository_path / config.evaluation_path_name

    if not eval_path.exists():
        return []

    evaluations = []
    for extension in DISCOVER_EXTENSIONS:
        for config_file in eval_path.glob(f"*.{extension}"):
            parsed_eval = parse_evaluation_config_toml(config_file, repository_path)
            evaluations.append(parsed_eval)

    return evaluations


def validate_evaluation_configs(repository_path: Path) -> bool:
    """Validate all evaluation configurations in the repository.

    Args:
        repository_path: Root path of the repository.

    Returns:
        True if all evaluation configurations are valid, False otherwise.
    """
    try:
        discover_evaluations(repository_path)
        return True
    except ValueError:
        return False


def parse_evaluation_config_toml(toml_path: Path, repository_path: Path) -> EvaluationConfig:
    """Parse a single TOML evaluation configuration file.

    Reads a TOML file containing an evaluation configuration, validates its structure,
    and returns a fully populated EvaluationConfig object. The function automatically
    derives the evaluation name from the filename and calculates the relative file path.

    Args:
        toml_path: Absolute path to the TOML configuration file.
        repository_path: Root path of the repository, used to calculate relative file paths.

    Returns:
        EvaluationConfig: Validated evaluation configuration object.

    Raises:
        ValueError: If the TOML file is missing the required 'eval' section or if
                   validation fails for any configuration fields.

    Example:
        >>> from pathlib import Path
        >>> eval_config = parse_evaluation_toml(
        ...     Path("/repo/.agentci/evals/accuracy_test.toml"),
        ...     Path("/repo")
        ... )
        >>> print(eval_config.name)  # 'accuracy_test'
        >>> print(eval_config.file_path)  # '.agentci/evals/accuracy_test.toml'
    """
    try:
        with open(toml_path, "rb") as f:
            toml_data = tomllib.load(f)

        if "eval" not in toml_data:
            raise ValueError(f"Missing 'eval' section in {toml_path}")

        eval_data = toml_data["eval"]

        # Add metadata to the eval data
        eval_data["name"] = toml_path.stem
        eval_data["file_path"] = str(toml_path.relative_to(repository_path))

        return EvaluationConfig(**eval_data)

    except Exception as e:
        raise ValueError(f"Failed to parse evaluation config {toml_path}: {str(e)}")
