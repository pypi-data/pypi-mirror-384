import sys
import textwrap
from datetime import datetime
from typing import Any
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field, PrivateAttr, field_validator
from pydantic_core import to_jsonable_python

from docent.data_models._tiktoken_util import (
    get_token_count,
    group_messages_into_ranges,
    truncate_to_token_limit,
)
from docent.data_models.chat import AssistantMessage, ChatMessage, ContentReasoning
from docent.data_models.citation import RANGE_BEGIN, RANGE_END
from docent.data_models.metadata_util import dump_metadata

# Template for formatting individual transcript blocks
TRANSCRIPT_BLOCK_TEMPLATE = """
<|{index_label}; role: {role}|>
{content}
</|{index_label}; role: {role}|>
""".strip()

# Instructions for citing single transcript blocks
TEXT_RANGE_CITE_INSTRUCTION = f"""Anytime you quote the transcript, or refer to something that happened in the transcript, or make any claim about the transcript, add an inline citation. Each transcript and each block has a unique index. Cite the relevant indices in brackets. For example, to cite the entirety of transcript 0, block 1, write [T0B1].

A citation may include a specific range of text within a block. Use {RANGE_BEGIN} and {RANGE_END} to mark the specific range of text. Add it after the block ID separated by a colon. For example, to cite the part of transcript 0, block 1, where the agent says "I understand the task", write [T0B1:{RANGE_BEGIN}I understand the task{RANGE_END}]. Citations must follow this exact format. The markers {RANGE_BEGIN} and {RANGE_END} must be used ONLY inside the brackets of a citation.

- You may cite a top-level key in the agent run metadata like this: [M.task_description].
- You may cite a top-level key in transcript metadata. For example, for transcript 0: [T0M.start_time].
- You may cite a top-level key in message metadata for a block. For example, for transcript 0, block 1: [T0B1M.status].
- You may not cite nested keys. For example, [T0B1M.status.code] is invalid.
- Within a top-level metadata key you may cite a range of text that appears in the value. For example, [T0B1M.status:{RANGE_BEGIN}"running":false{RANGE_END}].

Important notes:
- You must include the full content of the text range {RANGE_BEGIN} and {RANGE_END}, EXACTLY as it appears in the transcript, word-for-word, including any markers or punctuation that appear in the middle of the text.
- Citations must be as specific as possible. This means you should usually cite a specific text range within a block.
- A citation is not a quote. For brevity, text ranges will not be rendered inline. The user will have to click on the citation to see the full text range.
- Citations are self-contained. Do NOT label them as citation or evidence. Just insert the citation by itself at the appropriate place in the text.
- Citations must come immediately after the part of a claim that they support. This may be in the middle of a sentence.
- Each pair of brackets must contain only one citation. To cite multiple blocks, use multiple pairs of brackets, like [T0B0] [T0B1].
- Outside of citations, do not refer to transcript numbers or block numbers.
- Outside of citations, avoid quoting or paraphrasing the transcript.
"""

BLOCK_CITE_INSTRUCTION = """Each transcript and each block has a unique index. Cite the relevant indices in brackets when relevant, like [T<idx>B<idx>]. Use multiple tags to cite multiple blocks, like [T<idx1>B<idx1>][T<idx2>B<idx2>]. Remember to cite specific blocks and NOT action units."""


def format_chat_message(
    message: ChatMessage,
    block_idx: int,
    transcript_idx: int = 0,
    agent_run_idx: int | None = None,
) -> str:
    if agent_run_idx is not None:
        index_label = f"R{agent_run_idx}T{transcript_idx}B{block_idx}"
    else:
        index_label = f"T{transcript_idx}B{block_idx}"

    cur_content = ""

    # Add reasoning at beginning if applicable
    if isinstance(message, AssistantMessage) and message.content:
        for content in message.content:
            if isinstance(content, ContentReasoning):
                cur_content = f"<reasoning>\n{content.reasoning}\n</reasoning>\n"

    # Main content text
    cur_content += message.text

    # Update content in case there's a view
    if isinstance(message, AssistantMessage) and message.tool_calls:
        for tool_call in message.tool_calls:
            if tool_call.view:
                cur_content += f"\n<tool call>\n{tool_call.view.content}\n</tool call>"
            else:
                args = ", ".join([f"{k}={v}" for k, v in tool_call.arguments.items()])
                cur_content += f"\n<tool call>\n{tool_call.function}({args})\n</tool call>"

    if message.metadata:
        metadata_text = dump_metadata(message.metadata)
        if metadata_text is not None:
            cur_content += f"\n<|message metadata|>\n{metadata_text}\n</|message metadata|>"

    return TRANSCRIPT_BLOCK_TEMPLATE.format(
        index_label=index_label, role=message.role, content=cur_content
    )


class TranscriptGroup(BaseModel):
    """Represents a group of transcripts that are logically related.

    A transcript group can contain multiple transcripts and can have a hierarchical
    structure with parent groups. This is useful for organizing transcripts into
    logical units like experiments, tasks, or sessions.

    Attributes:
        id: Unique identifier for the transcript group, auto-generated by default.
        name: Optional human-readable name for the transcript group.
        description: Optional description of the transcript group.
        collection_id: ID of the collection this transcript group belongs to.
        agent_run_id: ID of the agent run this transcript group belongs to.
        parent_transcript_group_id: Optional ID of the parent transcript group.
        metadata: Additional structured metadata about the transcript group.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str | None = None
    description: str | None = None
    agent_run_id: str
    parent_transcript_group_id: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", mode="before")
    @classmethod
    def _validate_metadata_type(cls, v: Any) -> Any:
        if v is not None and not isinstance(v, dict):
            raise ValueError(f"metadata must be a dictionary, got {type(v).__name__}")
        return v  # type: ignore

    def to_text_new(self, children_text: str, indent: int = 0) -> str:
        """Render this transcript group with its children and metadata.

        Metadata appears below the rendered children content.

        Args:
            children_text: Pre-rendered text of this group's children (groups/transcripts).
            indent: Number of spaces to indent the rendered output.

        Returns:
            str: XML-like wrapped text including the group's metadata.
        """
        # Prepare YAML metadata
        metadata_text = dump_metadata(self.metadata)
        if metadata_text is not None:
            if indent > 0:
                metadata_text = textwrap.indent(metadata_text, " " * indent)
            inner = f"{children_text}\n<|{self.name} metadata|>\n{metadata_text}\n</|{self.name} metadata|>"
        else:
            inner = children_text

        # Compose final text: content first, then metadata, all inside the group wrapper
        if indent > 0:
            inner = textwrap.indent(inner, " " * indent)
        return f"<|{self.name}|>\n{inner}\n</|{self.name}|>"


class Transcript(BaseModel):
    """Represents a transcript of messages in a conversation with an AI agent.

    A transcript contains a sequence of messages exchanged between different roles
    (system, user, assistant, tool) and provides methods to organize these messages
    into logical units of action.

    Attributes:
        id: Unique identifier for the transcript, auto-generated by default.
        name: Optional human-readable name for the transcript.
        description: Optional description of the transcript.
        transcript_group_id: Optional ID of the transcript group this transcript belongs to.
        messages: List of chat messages in the transcript.
        metadata: Additional structured metadata about the transcript.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str | None = None
    description: str | None = None
    transcript_group_id: str | None = None
    created_at: datetime | None = None

    messages: list[ChatMessage]
    metadata: dict[str, Any] = Field(default_factory=dict)
    _units_of_action: list[list[int]] | None = PrivateAttr(default=None)

    @field_validator("metadata", mode="before")
    @classmethod
    def _validate_metadata_type(cls, v: Any) -> Any:
        if v is not None and not isinstance(v, dict):
            raise ValueError(f"metadata must be a dict, got {type(v).__name__}")
        return v  # type: ignore

    @property
    def units_of_action(self) -> list[list[int]]:
        """Get the units of action in the transcript.

        A unit of action represents a logical group of messages, such as a system message
        on its own or a user message followed by assistant responses and tool outputs.

        For precise details on how action units are determined, refer to the _compute_units_of_action method implementation.

        Returns:
            list[list[int]]: List of units of action, where each unit is a list of message indices.
        """
        if self._units_of_action is None:
            self._units_of_action = self._compute_units_of_action()
        return self._units_of_action

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._units_of_action = self._compute_units_of_action()

    def _compute_units_of_action(self) -> list[list[int]]:
        """Compute the units of action in the transcript.

        A unit of action is defined as:
        - A system prompt by itself
        - A group consisting of a user message, assistant response, and any associated tool outputs

        Returns:
            list[list[int]]: A list of units of action, where each unit is a list of message indices.
        """
        if not self.messages:
            return []

        units: list[list[int]] = []
        current_unit: list[int] = []

        def _start_new_unit():
            nonlocal current_unit
            if current_unit:
                units.append(current_unit.copy())
            current_unit = []

        for i, message in enumerate(self.messages):
            role = message.role
            prev_message = self.messages[i - 1] if i > 0 else None

            # System messages are their own unit
            if role == "system":
                # Start a new unit if there's a current unit in progress
                if current_unit:
                    _start_new_unit()
                units.append([i])

            # User message always starts a new unit UNLESS the previous message was a user message
            elif role == "user":
                if current_unit and prev_message and prev_message.role != "user":
                    _start_new_unit()
                current_unit.append(i)

            # Start a new unit if the previous message was not a user or assistant message
            elif role == "assistant":
                if (
                    current_unit
                    and prev_message
                    and prev_message.role != "user"
                    and prev_message.role != "assistant"
                ):
                    _start_new_unit()
                current_unit.append(i)

            # Tool messages are part of the current unit
            elif role == "tool":
                current_unit.append(i)

            else:
                raise ValueError(f"Unknown message role: {role}")

        # Add the last unit if it exists
        _start_new_unit()

        return units

    def get_first_block_in_action_unit(self, action_unit_idx: int) -> int | None:
        """Get the index of the first message in a given action unit.

        Args:
            action_unit_idx: The index of the action unit.

        Returns:
            int | None: The index of the first message in the action unit,
                        or None if the action unit doesn't exist.

        Raises:
            IndexError: If the action unit index is out of range.
        """
        if not self._units_of_action:
            self._units_of_action = self._compute_units_of_action()

        if 0 <= action_unit_idx < len(self._units_of_action):
            unit = self._units_of_action[action_unit_idx]
            return unit[0] if unit else None
        return None

    def get_action_unit_for_block(self, block_idx: int) -> int | None:
        """Find the action unit that contains the specified message block.

        Args:
            block_idx: The index of the message block to find.

        Returns:
            int | None: The index of the action unit containing the block,
                        or None if no action unit contains the block.
        """
        if not self._units_of_action:
            self._units_of_action = self._compute_units_of_action()

        for unit_idx, unit in enumerate(self._units_of_action):
            if block_idx in unit:
                return unit_idx
        return None

    def set_messages(self, messages: list[ChatMessage]):
        """Set the messages in the transcript and recompute units of action.

        Args:
            messages: The new list of chat messages to set.
        """
        self.messages = messages
        self._units_of_action = self._compute_units_of_action()

    def _generate_formatted_blocks(
        self,
        transcript_idx: int = 0,
        agent_run_idx: int | None = None,
        use_action_units: bool = True,
        highlight_action_unit: int | None = None,
    ) -> list[str]:
        """Generate formatted blocks for transcript representation.

        Args:
            transcript_idx: Index of the transcript
            agent_run_idx: Optional agent run index
            use_action_units: If True, group messages into action units. If False, use individual blocks.
            highlight_action_unit: Optional action unit to highlight (only used with action units)

        Returns:
            list[str]: List of formatted blocks
        """
        if use_action_units:
            if highlight_action_unit is not None and not (
                0 <= highlight_action_unit < len(self._units_of_action or [])
            ):
                raise ValueError(f"Invalid action unit index: {highlight_action_unit}")

            blocks: list[str] = []
            for unit_idx, unit in enumerate(self._units_of_action or []):
                unit_blocks: list[str] = []
                for msg_idx in unit:
                    unit_blocks.append(
                        format_chat_message(
                            self.messages[msg_idx],
                            msg_idx,
                            transcript_idx,
                            agent_run_idx,
                        )
                    )

                unit_content = "\n".join(unit_blocks)

                # Add highlighting if requested
                if highlight_action_unit and unit_idx == highlight_action_unit:
                    blocks_str_template = "<HIGHLIGHTED>\n{}\n</HIGHLIGHTED>"
                else:
                    blocks_str_template = "{}"
                blocks.append(
                    blocks_str_template.format(
                        f"<action unit {unit_idx}>\n{unit_content}\n</action unit {unit_idx}>"
                    )
                )
        else:
            # Individual message blocks
            blocks = []
            for msg_idx, message in enumerate(self.messages):
                blocks.append(
                    format_chat_message(
                        message,
                        msg_idx,
                        transcript_idx,
                        agent_run_idx,
                    )
                )

        return blocks

    def to_str(
        self,
        token_limit: int = sys.maxsize,
        transcript_idx: int = 0,
        agent_run_idx: int | None = None,
        use_action_units: bool = True,
        highlight_action_unit: int | None = None,
    ) -> list[str]:
        """Core implementation for string representation with token limits.

        Args:
            token_limit: Maximum tokens per returned string
            transcript_idx: Index of the transcript
            agent_run_idx: Optional agent run index
            use_action_units: If True, group messages into action units. If False, use individual blocks.
            highlight_action_unit: Optional action unit to highlight (only used with action units)

        Returns:
            list[str]: List of strings, each within token limit
        """
        blocks = self._generate_formatted_blocks(
            transcript_idx, agent_run_idx, use_action_units, highlight_action_unit
        )
        blocks_str = "\n".join(blocks)

        # Gather metadata
        metadata_obj = to_jsonable_python(self.metadata)
        yaml_width = float("inf")
        block_str = f"<blocks>\n{blocks_str}\n</blocks>\n"
        metadata_str = f"<|transcript metadata|>\n{yaml.dump(metadata_obj, width=yaml_width)}\n</|transcript metadata|>"

        if token_limit == sys.maxsize:
            return [f"{block_str}" f"{metadata_str}"]

        metadata_token_count = get_token_count(metadata_str)
        block_token_count = get_token_count(block_str)

        if metadata_token_count + block_token_count <= token_limit:
            return [f"{block_str}" f"{metadata_str}"]
        else:
            results: list[str] = []
            block_token_counts = [get_token_count(block) for block in blocks]
            ranges = group_messages_into_ranges(
                block_token_counts, metadata_token_count, token_limit
            )
            for msg_range in ranges:
                if msg_range.include_metadata:
                    cur_blocks = "\n".join(blocks[msg_range.start : msg_range.end])
                    results.append(f"<blocks>\n{cur_blocks}\n</blocks>\n" f"{metadata_str}")
                else:
                    assert (
                        msg_range.end == msg_range.start + 1
                    ), "Ranges without metadata should be a single message"
                    result = str(blocks[msg_range.start])
                    if msg_range.num_tokens > token_limit - 10:
                        result = truncate_to_token_limit(result, token_limit - 10)
                    results.append(f"<blocks>\n{result}\n</blocks>\n")

            return results

    ##############################
    # New text rendering methods #
    ##############################

    def to_text_new(self, transcript_idx: int = 0, indent: int = 0) -> str:
        # Format individual message blocks
        blocks: list[str] = []
        for msg_idx, message in enumerate(self.messages):
            block_text = format_chat_message(message, msg_idx, transcript_idx)
            blocks.append(block_text)
        blocks_str = "\n".join(blocks)
        if indent > 0:
            blocks_str = textwrap.indent(blocks_str, " " * indent)

        content_str = f"<|T{transcript_idx} blocks|>\n{blocks_str}\n</|T{transcript_idx} blocks|>"

        # Gather metadata and add to content
        metadata_text = dump_metadata(self.metadata)
        if metadata_text is not None:
            if indent > 0:
                metadata_text = textwrap.indent(metadata_text, " " * indent)
            content_str += f"\n<|T{transcript_idx} metadata|>\n{metadata_text}\n</|T{transcript_idx} metadata|>"

        # Format content and return
        if indent > 0:
            content_str = textwrap.indent(content_str, " " * indent)
        return f"<|T{transcript_idx}|>\n{content_str}\n</|T{transcript_idx}|>\n"
