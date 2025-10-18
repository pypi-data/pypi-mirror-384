import logging
from datetime import datetime
from pathlib import Path

from code_review.adapters.changelog import parse_changelog
from code_review.adapters.setup_adapters import setup_to_dict
from code_review.plugins.dependencies.pip.handlers import requirements_updated
from code_review.handlers.file_handlers import change_directory, get_not_ignored
from code_review.plugins.linting.ruff.handlers import _check_and_format_ruff, count_ruff_issues
from code_review.plugins.coverage.main import get_makefile, get_minimum_coverage
from code_review.plugins.docker.docker_files.handlers import parse_dockerfile
from code_review.plugins.git.adapters import get_git_flow_source_branch, is_rebased
from code_review.plugins.git.handlers import branch_line_to_dict, check_out_and_pull, get_branch_info
from code_review.plugins.gitlab.ci.rules import validate_ci_rules
from code_review.review.rules.git_rules import rebase_rule, validate_master_develop_sync
from code_review.review.rules.linting_rules import check_and_format_ruff
from code_review.review.rules.version_rules import check_change_log_version
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import BranchSchema, SemanticVersion

logger = logging.getLogger(__name__)


def build_code_review_schema(folder: Path, target_branch_name: str) -> CodeReviewSchema:
    """Build a CodeReviewSchema for the given folder and target branch.

    Args:
        folder: Path to the folder containing the code review data.
        target_branch_name: Name of the target branch to compare against the base branch.
    """
    change_directory(folder)

    makefile = get_makefile(folder)  # Assuming this function is defined elsewhere to get the makefile path
    base_name = "master"
    check_out_and_pull(base_name, check=False)
    base_count = count_ruff_issues(folder)
    get_branch_info(base_name)
    base_branch_info = branch_line_to_dict(base_name)
    base_cov = get_minimum_coverage(makefile)
    base_branch_info["linting_errors"] = base_count
    base_branch_info["min_coverage"] = base_cov

    base_branch = BranchSchema(**base_branch_info)
    base_branch.version = get_version_from_config_file(folder, folder.stem)
    base_branch.changelog_versions = parse_changelog(folder / "CHANGELOG.md", folder.stem)

    check_out_and_pull(target_branch_name, check=False)
    get_branch_info(target_branch_name)
    target_branch_info = branch_line_to_dict(target_branch_name)
    target_count = count_ruff_issues(folder)
    target_cov = get_minimum_coverage(makefile)
    target_branch_info["linting_errors"] = target_count
    target_branch_info["min_coverage"] = target_cov

    target_branch = BranchSchema(**target_branch_info)
    target_branch.version = get_version_from_config_file(folder, folder.stem)
    target_branch.changelog_versions = parse_changelog(folder / "CHANGELOG.md", folder.stem)
    target_branch.requirements_to_update = requirements_updated(folder)

    target_branch.formatting_errors = _check_and_format_ruff(folder)

    # Dockerfiles
    docker_files = get_not_ignored(folder, "Dockerfile")
    docker_info_list = []
    for file in docker_files:
        docker_info = parse_dockerfile(file)
        if docker_info:
            docker_info_list.append(docker_info)
    source_branch_name = get_git_flow_source_branch(target_branch.name)
    if not source_branch_name:
        logger.warning("No source branch in target branch for target branch. %s", target_branch.name)

    rules = []
    code_review_schema = CodeReviewSchema(
        name=folder.name,
        source_folder=folder,
        makefile_path=makefile,
        target_branch=target_branch,
        source_branch_name=source_branch_name,
        base_branch=base_branch,
        date_created=datetime.now(),
        docker_files=docker_info_list,
        rules_validated=rules,
    )

    code_review_schema.is_rebased = is_rebased(code_review_schema.target_branch.name, source_branch_name)

    # CI rules
    ci_rules = validate_ci_rules(folder / ".gitlab-ci.yml")
    if ci_rules:
        rules.extend(ci_rules)
    # Ruff linting rules
    linting_rules = check_and_format_ruff(base_branch, target_branch)
    if linting_rules:
        rules.extend(linting_rules)
    # Git rules
    git_rules = validate_master_develop_sync(*["master", "develop"])
    if git_rules:
        rules.extend(git_rules)
    # Git sync rules
    git_sync_rules = rebase_rule(code_review_schema)
    if git_sync_rules:
        rules.extend(git_sync_rules)
    # Changelog version rules
    change_log_rules = check_change_log_version(base_branch, target_branch)
    if change_log_rules:
        rules.extend(change_log_rules)

    code_review_schema.rules_validated = rules
    return code_review_schema


def get_version_from_config_file(folder: Path, app_name: str) -> SemanticVersion | None:
    """Extract the version string from a given file."""
    setup_file = folder / "setup.cfg"
    if not setup_file.exists():
        setup_file = folder / ".bumpversion.cfg"

    setup_dict = setup_to_dict(setup_file)
    if setup_dict.get("bumpversion", {}).get("current_version"):
        version_str = setup_dict["bumpversion"]["current_version"]
        return SemanticVersion.parse_version(version_str, app_name, setup_file)

    return None
