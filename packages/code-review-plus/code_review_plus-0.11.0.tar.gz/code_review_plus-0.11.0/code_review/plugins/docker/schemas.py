from pathlib import Path

from pydantic import BaseModel, Field


class DockerfileSchema(BaseModel):
    version: str = Field(description="The version found in the Dockerfile")
    expected_version: str | None = Field(default=None, description="The expected version to update to, if applicable")
    product: str = Field(description="The product name, e.g., python, node, etc.")
    file: Path = Field(description="Path to the Dockerfile")
