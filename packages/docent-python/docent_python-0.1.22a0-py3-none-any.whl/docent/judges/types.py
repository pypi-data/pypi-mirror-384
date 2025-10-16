import enum
import json
from string import Formatter
from typing import Any, Callable, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator

from docent._llm_util.providers.preference_types import PUBLIC_PROVIDER_PREFERENCES, ModelOption
from docent._log_util import get_logger
from docent.data_models.agent_run import AgentRun
from docent.data_models.citation import parse_citations
from docent.data_models.transcript import TEXT_RANGE_CITE_INSTRUCTION
from docent.judges.util.meta_schema import validate_judge_result_schema

logger = get_logger(__name__)

DEFAULT_JUDGE_SYSTEM_PROMPT_TEMPLATE = """
Here is a rubric that we are using to judge transcripts of AI agent runs.

Rubric:
{rubric}

Agent run:
{agent_run}

Your response should convey your judgment of the agent run according to the criteria given in the rubric provided above. Your entire response must be a valid JSON string which can be parsed with python `json.loads` without any additional processing. Double quotes (`"`) in the middle of a string in the JSON object must be escaped with a backslash.

The JSON object you produce must adhere to the following schema:
{output_schema}

{citation_instructions}
""".strip()

DEFAULT_CITATION_INSTRUCTIONS = f"""
For strings which require citations (according to the `citations: True` property), you must also follow these instructions:
{TEXT_RANGE_CITE_INSTRUCTION}
""".strip()

DEFAULT_JUDGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": ["match", "no match"]},
        "explanation": {"type": "string", "citations": True},
    },
    # Require these properties to be present
    "required": ["label", "explanation"],
    # Allow additional properties though, as their presence is not breaking
}

DEFAULT_JUDGE_MODEL = PUBLIC_PROVIDER_PREFERENCES.default_judge_models[0]


class Rubric(BaseModel):
    """TODO(mengk): this should really be called JudgeConfig,
    but temporarily keeping this for consistency with docent_core."""

    class Config:
        frozen = True

    # Primary key
    id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 1

    # What the judge actually does
    rubric_text: str

    # Default instructions for the judge
    system_prompt_template: str = DEFAULT_JUDGE_SYSTEM_PROMPT_TEMPLATE
    citation_instructions: str = DEFAULT_CITATION_INSTRUCTIONS
    output_schema: dict[str, Any] = DEFAULT_JUDGE_OUTPUT_SCHEMA

    # How to run the judge
    judge_model: ModelOption = DEFAULT_JUDGE_MODEL

    def materialize_system_prompt(self, agent_run: AgentRun) -> str:
        """Construct the full prompt text for rubric evaluation.

        This is the canonical implementation of prompt construction - use this function
        anywhere you need to construct a rubric evaluation prompt (including cost estimation).
        """

        output_schema_text = json.dumps(self.output_schema, indent=2)

        # We've already validated that the system prompt template has these keys
        prompt = self.system_prompt_template.format(
            rubric=self.rubric_text,
            agent_run=agent_run.to_text_new(),
            output_schema=output_schema_text,
            # Only include citation instructions if the schema requests citations
            citation_instructions=(
                self.citation_instructions if _schema_requests_citations(self.output_schema) else ""
            ),
        ).strip()

        return prompt

    @field_validator("system_prompt_template")
    @classmethod
    def validate_system_prompt_template(cls, system_prompt_template: str):
        # Extract all field names from the template
        formatter = Formatter()
        field_names = {
            field_name
            for _, field_name, _, _ in formatter.parse(system_prompt_template)
            if field_name is not None
        }

        # Check for required fields
        required_fields = {"agent_run", "output_schema", "rubric", "citation_instructions"}
        missing_fields = required_fields - field_names

        if missing_fields:
            raise ValueError(
                f"system_prompt_template must contain the following placeholders: {missing_fields}"
            )

        return system_prompt_template

    @field_validator("output_schema")
    @classmethod
    def validate_output_schema(cls, output_schema: dict[str, Any]):
        """
        Raises:
            jsonschema.ValidationError: If the schema is invalid
            jsonschema.SchemaError: If the schema is not a valid 2020-12 schema
        """
        validate_judge_result_schema(output_schema)
        return output_schema


class ResultType(enum.Enum):
    """Enum for the type of result that a judge result can have."""

    DIRECT_RESULT = "direct_result"
    NEAR_MISS = "near_miss"


class JudgeResult(BaseModel):
    class Config:
        frozen = True

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_run_id: str
    rubric_id: str
    rubric_version: int

    # Outputs
    output: dict[str, Any]
    result_metadata: dict[str, Any] | None = None
    result_type: ResultType

    # Deprecated
    value: str | None = None

    @field_serializer("result_type")
    def serialize_result_type(self, result_type: ResultType) -> str:
        return result_type.value


class JudgeResultWithCitations(JudgeResult):
    @classmethod
    def from_judge_result(
        cls, result: JudgeResult, schema: dict[str, Any]
    ) -> "JudgeResultWithCitations":
        """Judge result must be validated against the schema before calling this function!"""

        def _parse_citation_string(output: str) -> dict[str, Any]:
            text, citations = parse_citations(output)
            return {"text": text, "citations": citations}

        data = result.model_dump()
        try:
            data["output"] = traverse_schema_and_transform(
                data["output"], schema, _parse_citation_string
            )
        except Exception as e:
            logger.error(f"Failed to parse citations: {e}")
            logger.error(f"Output: {data['output']}")
            data["output"] = {"raw": data["output"]}
        return cls(**data)


class JudgeResultCompletionCallback(Protocol):
    """Called when some batch of judge results is completed.
    Supports batched calls for cases where many results are pre-computed.
    This avoids invoking the callback separately for each datapoint.
    """

    async def __call__(
        self,
        batch_index: int,
        judge_results: list[JudgeResult] | None,
    ) -> None: ...


def traverse_schema_and_transform(
    output: Any,
    schema: dict[str, Any],
    citation_string_handler: Callable[[str], Any],
) -> Any:
    """Recursively traverse output based on schema, applying citation_string_handler to citation strings."""
    if schema.get("type") == "string" and schema.get("citations"):  # type: ignore
        return citation_string_handler(output)
    elif schema.get("type") == "object":
        properties: dict[str, Any] = schema.get("properties", {})
        result: dict[str, Any] = {}
        for key in properties:
            if key in output:
                result[key] = traverse_schema_and_transform(
                    output[key], properties[key], citation_string_handler
                )
        return result
    elif schema.get("type") == "array":
        item_schema: dict[str, Any] = schema.get("items", {})
        return [
            traverse_schema_and_transform(item, item_schema, citation_string_handler)
            for item in output
        ]
    else:
        return output


def _schema_requests_citations(schema: dict[str, Any]) -> bool:
    """Check if any field in the schema requests citations by having 'citations': 'true'."""

    def _check_field(field_schema: Any) -> bool:
        if isinstance(field_schema, dict):
            if field_schema.get("citations"):  # type: ignore
                return True
            for value in field_schema.values():  # type: ignore
                if isinstance(value, dict) and _check_field(value):
                    return True
                elif isinstance(value, list):
                    for item in value:  # type: ignore
                        if isinstance(item, dict) and _check_field(item):
                            return True
        return False

    return _check_field(schema)
