from dataclasses import dataclass

from src.tool_set import ToolSet


@dataclass
class Role:
    system_prompt: str | None
    tool_set: ToolSet | None
