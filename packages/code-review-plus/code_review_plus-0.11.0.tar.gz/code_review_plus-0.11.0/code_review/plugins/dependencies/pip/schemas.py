from pathlib import Path

from pydantic import BaseModel, Field


class RequirementInfo(BaseModel):
    """Schema for a pip requirement."""

    name: str = ""
    line: str = Field(description="The full line from the requirements file")
    file: Path

    def __eq__(self, other):
        return self.line == other.line and self.name == other.name
