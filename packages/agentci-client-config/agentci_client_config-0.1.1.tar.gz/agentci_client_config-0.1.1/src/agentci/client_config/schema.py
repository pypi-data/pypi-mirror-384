from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, model_validator

__all__ = [
    "EvaluationConfig",
    "EvaluationType",
    "EvaluationTargets",
    "LatencyThreshold",
    "TokenThreshold",
    "ScoreThreshold",
    "ToolCallSpec",
    "LLMConfig",
    "ConsistencyConfig",
    "CustomConfig",
    "SchemaField",
    "EvaluationCase",
    "StringMatch",
]


class EvaluationType(str, Enum):
    """Supported evaluation types."""

    ACCURACY = "accuracy"
    PERFORMANCE = "performance"
    SEMANTIC = "semantic"
    SAFETY = "safety"
    CONSISTENCY = "consistency"
    LLM = "llm"
    CUSTOM = "custom"


class EvaluationTargets(BaseModel):
    """Target specification for agents and tools."""

    agents: List[str] = Field(default_factory=list, description="Agent names to evaluate")
    tools: List[str] = Field(default_factory=list, description="Tool names to evaluate")

    def targets_agent(self, agent_name: str) -> bool:
        """Check if this evaluation targets a specific agent."""
        if "*" in self.agents:
            return True

        return agent_name in self.agents

    def targets_tool(self, tool_name: str) -> bool:
        """Check if this evaluation targets a specific tool."""
        if "*" in self.tools:
            return True

        return tool_name in self.tools


class LatencyThreshold(BaseModel):
    """Latency threshold configuration (all values stored in seconds)."""

    min: Optional[float] = Field(None, description="Minimum latency in seconds")
    max: Optional[float] = Field(None, description="Maximum latency in seconds")
    min_ms: Optional[float] = Field(
        None, description="Minimum latency in milliseconds (will be converted to min)"
    )
    max_ms: Optional[float] = Field(
        None, description="Maximum latency in milliseconds (will be converted to max)"
    )
    equal: Optional[float] = Field(None, description="Exact latency in seconds")

    @model_validator(mode="before")
    @classmethod
    def normalize_milliseconds(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Convert millisecond values to seconds and store in min/max fields."""
        if isinstance(values, dict):
            # Convert min_ms to min (in seconds)
            if "min_ms" in values and values["min_ms"] is not None:
                if "min" not in values or values["min"] is None:
                    values["min"] = values["min_ms"] / 1000.0
                # Remove min_ms after conversion
                del values["min_ms"]

            # Convert max_ms to max (in seconds)
            if "max_ms" in values and values["max_ms"] is not None:
                if "max" not in values or values["max"] is None:
                    values["max"] = values["max_ms"] / 1000.0
                # Remove max_ms after conversion
                del values["max_ms"]

        return values


class TokenThreshold(BaseModel):
    """Token usage threshold configuration."""

    min: Optional[int] = None
    max: Optional[int] = None
    equal: Optional[int] = None


class ScoreThreshold(BaseModel):
    """Score threshold configuration."""

    min: Optional[float] = None
    max: Optional[float] = None
    equal: Optional[float] = None


class ToolCallSpec(BaseModel):
    """Tool call specification for validation."""

    name: str = Field(description="Name of the tool to validate")
    args: List[Any] | Dict[str, Any] = Field(description="Expected arguments (positional list or named dict)")


class LLMConfig(BaseModel):
    """LLM evaluation configuration."""

    model: str = Field(
        min_length=1,
        description="LiteLLM model string (e.g., 'anthropic/claude-3-sonnet-20240229', 'openai/gpt-4')",
    )
    prompt: str = Field(min_length=1, description="Evaluation prompt template for LLM judge")
    output_schema: Optional[str] = Field(
        None,
        description="JSON schema for LLM output (e.g., structured score + reasoning)",
    )


class ConsistencyConfig(BaseModel):
    """Consistency evaluation configuration."""

    model: str = Field(
        default="openai/text-embedding-3-small",
        description="Embedding model for semantic similarity",
    )


class CustomConfig(BaseModel):
    """Custom evaluation configuration."""

    module: str = Field(min_length=1, description="Python module path")
    function: str = Field(min_length=1, description="Function name within module")


class SchemaField(BaseModel):
    """Schema field definition with type and validation constraints."""

    # Type specification
    type: Optional[Union[str, List[str], Dict[str, "SchemaField"]]] = Field(
        None, description="Field type(s) or nested schema definition (dict of SchemaFields)"
    )

    # Required/optional
    required: bool = Field(True, description="Whether field is required")
    default: Optional[Any] = Field(None, description="Default value if field is missing")

    # Content validation with StringMatch
    value: Optional[Union[str, "StringMatch"]] = Field(
        None, description="String matching strategy for field content (exact string or StringMatch object)"
    )

    # Enum/literal constraints
    enum: Optional[List[Any]] = Field(None, description="Allowed values for enum/literal types")

    # String validation
    min_length: Optional[int] = Field(None, ge=0, description="Minimum string length")
    max_length: Optional[int] = Field(None, ge=0, description="Maximum string length")

    # Number validation
    min: Optional[Union[int, float]] = Field(None, description="Minimum value (inclusive)")
    max: Optional[Union[int, float]] = Field(None, description="Maximum value (inclusive)")

    # Array validation
    min_items: Optional[int] = Field(None, ge=0, description="Minimum array length")
    max_items: Optional[int] = Field(None, ge=0, description="Maximum array length")

    # Nested schema (for list/array items only)
    # For object schemas, use type = {...} directly
    items: Optional[Dict[str, "SchemaField"]] = Field(None, description="Schema for list/array items")

    @model_validator(mode="after")
    def normalize_value_string(self):
        """Convert bare string value to StringMatch with exact strategy."""
        if isinstance(self.value, str):
            # Import here to avoid circular dependency
            self.value = StringMatch.from_string(self.value)
        return self

    @model_validator(mode="after")
    def validate_constraints(self):
        """Validate that constraints are appropriate for the field type."""
        if self.type is None:
            # If no type specified, this is likely a nested object definition
            return self

        # If type is a dict, it's a nested schema definition - no constraint validation needed
        if isinstance(self.type, dict):
            return self

        # Normalize type to string for checking
        type_str = self.type if isinstance(self.type, str) else str(self.type)

        # String constraints only valid for str type
        if (self.min_length is not None or self.max_length is not None) and "str" not in type_str:
            raise ValueError("min_length/max_length only valid for str types")

        # Number constraints only valid for int/float types
        if (self.min is not None or self.max is not None) and not any(
            t in type_str for t in ["int", "float"]
        ):
            raise ValueError("min/max only valid for int/float types")

        # Array constraints only valid for list/set types
        if (self.min_items is not None or self.max_items is not None) and not any(
            t in type_str for t in ["list", "set"]
        ):
            raise ValueError("min_items/max_items only valid for list/set types")

        # Items only valid for list/set types
        if self.items is not None and not any(t in type_str for t in ["list", "set"]):
            raise ValueError("items only valid for list/set types")

        return self


class StringMatch(BaseModel):
    """String matching configuration with multiple strategies.

    Supports exact matching, substring containment, prefix/suffix matching,
    regex patterns, semantic similarity, and schema validation.
    """

    # Allow field name "schema" to shadow BaseModel attribute
    # TODO: Find a way to eliminate this warning in the future while keeping the "schema" field name
    # We use protected_namespaces=() to allow shadowing BaseModel.schema()
    # This is safe because we don't use the inherited schema() method
    model_config = {"protected_namespaces": ()}

    # Exact match
    exact: Optional[str] = Field(None, description="Exact string match")

    # Substring matching
    contains: Optional[Union[str, List[str]]] = Field(
        None, description="Must contain substring(s) - single value or ALL in list"
    )
    contains_any: Optional[List[str]] = Field(
        None, description="Must contain at least one of these substrings (ANY match)"
    )

    # Prefix/suffix matching
    startswith: Optional[Union[str, List[str]]] = Field(
        None, description="Must start with prefix(es) - matches if ANY match"
    )
    endswith: Optional[Union[str, List[str]]] = Field(
        None, description="Must end with suffix(es) - matches if ANY match"
    )

    # Regex matching
    match: Optional[str] = Field(None, description="Must match regex pattern")

    # Semantic similarity
    similar: Optional[str] = Field(None, description="Reference text for semantic similarity")
    threshold: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0) for semantic matching"
    )

    # Schema matching
    schema: Optional[Dict[str, SchemaField]] = Field(
        None, description="Schema definition for structured output validation"
    )

    @classmethod
    def from_string(cls, exact: str) -> "StringMatch":
        """Create a StringMatch with exact matching strategy from a bare string.

        Args:
            exact: The string to match exactly

        Returns:
            StringMatch configured for exact matching
        """
        return cls(exact=exact)


    @model_validator(mode="after")
    def validate_single_strategy(self):
        """Ensure only one matching strategy is specified."""
        strategies = [
            self.exact,
            self.contains,
            self.contains_any,
            self.startswith,
            self.endswith,
            self.match,
            self.similar,
            self.schema,
        ]
        non_none = [s for s in strategies if s is not None]

        if len(non_none) > 1:
            raise ValueError("Only one matching strategy can be specified")

        if len(non_none) == 0:
            raise ValueError("At least one matching strategy must be specified")

        return self

    @model_validator(mode="after")
    def validate_semantic_threshold(self):
        """Ensure threshold and similar are used together."""
        if (self.similar is None) != (self.threshold is None):
            raise ValueError("similar and threshold must be used together")

        return self


class EvaluationCase(BaseModel):
    """Individual test case configuration."""

    # Metadata (set during execution)
    index: Optional[int] = Field(None, description="Case index (0-based), set during execution")

    # Input configuration
    prompt: Optional[str] = Field(None, description="Input prompt for agents")
    context: Optional[Dict[str, Any]] = Field(None, description="Context/parameters for tools")

    # Expected output configuration
    output: Optional[Union[str, StringMatch]] = Field(
        None,
        description="Expected output - string for exact match or StringMatch object for other strategies",
    )
    blocked: Optional[bool] = Field(None, description="Whether output should be blocked (safety)")
    tools: Optional[List[ToolCallSpec]] = Field(
        None, description="Expected tool calls for validation (accuracy)"
    )

    # Performance thresholds
    latency: Optional[LatencyThreshold] = None
    tokens: Optional[TokenThreshold] = None

    # Consistency configuration
    min_similarity: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Minimum similarity threshold (0.0-1.0)"
    )

    # LLM evaluation
    score: Optional[ScoreThreshold] = None

    # Custom evaluation parameters
    parameters: Optional[Dict[str, Any]] = Field(None, description="Custom evaluation parameters")

    @model_validator(mode="before")
    @classmethod
    def normalize_output(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize output field to StringMatch."""
        if isinstance(values, dict) and "output" in values:
            output = values["output"]
            # If output is already a StringMatch or None, leave it alone
            if output is None or isinstance(output, StringMatch):
                return values
            # If it's a bare string, it will be handled by Pydantic + post-validator
            if isinstance(output, str):
                return values
            # If it's a dict, convert it to a StringMatch
            if isinstance(output, dict):
                values["output"] = StringMatch(**output)
        return values

    @model_validator(mode="after")
    def normalize_output_string(self):
        """Convert bare string output to StringMatch with exact strategy."""
        if isinstance(self.output, str):
            self.output = StringMatch.from_string(self.output)
        return self


class EvaluationConfig(BaseModel):
    """Core evaluation configuration."""

    # Metadata (populated during parsing)
    name: str = Field(description="Evaluation name derived from filename")
    file_path: str = Field(description="Path to source configuration file")

    # Configuration content
    description: str = Field(description="Brief description of what this evaluation tests")
    type: EvaluationType = Field(description="Type of evaluation to perform")
    targets: EvaluationTargets = Field(description="Agents and tools to evaluate")
    iterations: int = Field(default=1, ge=1, description="Number of times to execute each test case")

    # Type-specific configuration
    template: Optional[str] = Field(None, description="Built-in template name (safety evaluations)")
    consistency: Optional[ConsistencyConfig] = None
    llm: Optional[LLMConfig] = None
    custom: Optional[CustomConfig] = None

    # Test cases
    cases: List[EvaluationCase] = Field(default_factory=list, description="Test cases to execute")

    @model_validator(mode="after")
    def validate_targets_specified(self):
        """Ensure at least one target is specified."""
        if not self.targets.agents and not self.targets.tools:
            raise ValueError("At least one agent or tool target must be specified")
        return self

    @model_validator(mode="after")
    def validate_type_specific_config(self):
        """Validate that required configuration is present for specific evaluation types."""
        if self.type == EvaluationType.LLM and self.llm is None:
            raise ValueError("LLM evaluations require llm configuration")
        return self

    @model_validator(mode="after")
    def validate_type_specific_requirements(self):
        """Validate type-specific configuration requirements."""

        # Safety evaluations need either template or test cases
        if self.type == EvaluationType.SAFETY:
            if not self.template and not self.cases:
                raise ValueError("Safety evaluations require either a template or test cases")

        # Custom evaluations require custom configuration
        if self.type == EvaluationType.CUSTOM:
            if not self.custom:
                raise ValueError("Custom evaluations require custom configuration")

        # Other evaluation types require test cases
        # NOTE: This might be too restrictive - some evaluation types might work with templates in the future
        if self.type in [
            EvaluationType.ACCURACY,
            EvaluationType.PERFORMANCE,
            EvaluationType.SEMANTIC,
            EvaluationType.CONSISTENCY,
        ]:
            if not self.cases:
                raise ValueError(f"{self.type.value} evaluations require test cases")

        return self

    @model_validator(mode="after")
    def validate_case_requirements(self):
        """Validate test cases match evaluation type requirements and set case indices."""
        for i, test_case in enumerate(self.cases):
            case_num = i + 1

            # Set the case index during parsing
            test_case.index = i

            # Type-specific case validation
            if self.type == EvaluationType.ACCURACY:
                if not test_case.output and not test_case.tools:
                    raise ValueError(
                        f"Case {case_num}: Accuracy evaluations require output or tools"
                    )

            elif self.type == EvaluationType.PERFORMANCE:
                if not test_case.latency and not test_case.tokens:
                    raise ValueError(
                        f"Case {case_num}: Performance evaluations require latency or tokens thresholds"
                    )

            elif self.type == EvaluationType.SAFETY:
                if test_case.blocked is None:
                    raise ValueError(f"Case {case_num}: Safety evaluations require blocked field")

            # Consistency evaluations: min_similarity is optional (defaults to 1.0 in runner)

            elif self.type == EvaluationType.LLM:
                if not test_case.score:
                    raise ValueError(f"Case {case_num}: LLM evaluations require score thresholds")

        return self
