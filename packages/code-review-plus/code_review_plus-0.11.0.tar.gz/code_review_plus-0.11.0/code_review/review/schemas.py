from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from code_review.plugins.docker.schemas import DockerfileSchema
from code_review.schemas import BranchSchema, RulesResult


class CodeReviewSchema(BaseModel):
    """Schema for code review requests."""

    name: str = Field(description="Name of the project to code review")
    is_rebased: bool = Field(
        default=False, description="Indicates if the target branch has been rebased onto the source branch"
    )
    source_folder: Path
    makefile_path: Path | None
    date_created: datetime | None
    ticket: str | None = Field(default=None, description="Ticket associated with the code review")
    target_branch: BranchSchema = Field(description="Details of the target branch. The branch to be reviewed.")
    base_branch: BranchSchema = Field(
        description="Details of the base branch. The branch to compare against usually master."
    )
    source_branch_name: str | None = Field(
        default=None, description="Name of the source branch from which the target branch was created."
    )
    docker_files: list[DockerfileSchema] | None = Field(
        default_factory=list, description="List of Dockerfiles found in the project"
    )
    rules_validated: list[RulesResult] | None = Field(
        default_factory=list, description="List of rule validation results"
    )


class CodeProject(BaseModel):
    """Schema for code projects."""

    path: Path = Field(description="Path to the project directory")
    tests_to_run: list[str] = Field(default_factory=list, description="List of test commands to run for the project")
