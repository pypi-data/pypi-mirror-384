from pathlib import Path

from pydantic import BaseModel, Field


class TestConfiguration(BaseModel):
    """Schema for test configurations."""

    folder: Path = Field(description="Test folder path.")
    unit_tests: list[str] = Field(default_factory=list, description="List of unit test to run.")
    min_coverage: float = Field(default=85.0, description="Minimum coverage percentage required.")
    settings_module: str = Field(default="config.settings.local", description="Django settings module to use.")
    tags_to_exclude: list[str] = Field(
        default_factory=lambda: ["INTEGRATION"], description="List of test tags to exclude."
    )
