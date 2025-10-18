import logging
import subprocess
from pathlib import Path

from code_review.plugins.dependencies.pip.schemas import RequirementInfo
from code_review.settings import CLI_CONSOLE

logger = logging.getLogger(__name__)


def requirements_updated(folder: Path, level: str = "minor") -> list[RequirementInfo]:
    """Updates minor version dependencies in requirement files within a specified folder
    and returns a list of updated packages.

    This function looks for a 'requirements' subdirectory inside the provided folder
    and processes all '.txt' files found there. It runs the 'pur --minor' command
    on each file, and then parses the command's output to identify which
    packages were updated.

    Args:
        folder (Path): The path to the root directory containing the 'requirements' folder.
        level (str): The level of updates to apply. Can be "major", "minor", or "patch".
                     Defaults to "minor".

    Returns:
        list[RequirementInfo]: A list of RequirementInfo
    """  # noqa: D205
    updated_packages = []
    requirements_folder = folder / "requirements"

    # Check if the requirements folder exists
    if not requirements_folder.is_dir():
        logger.error("Could not find requirements folder at %s", requirements_folder)
        return updated_packages

    # Iterate over all .txt files in the requirements directory
    for req_file in requirements_folder.glob("*.txt"):
        try:
            level_flag = []
            if level == "minor":
                level_flag = ["--minor", "*"]
            elif level == "patch":
                level_flag = ["--patch", "*"]
            # Run the pur command to update versions
            # `capture_output=True` gets the stdout and stderr
            # `text=True` decodes the output as text
            cmds = ["pur", "-r", str(req_file), "--dry-run-changed"] + level_flag
            logger.debug("Running %s", " ".join(cmds))
            result = subprocess.run(
                cmds,
                capture_output=True,
                text=True,
                check=True,  # Raise an exception if the command fails
            )

            # Process the output line by line
            splitlines = result.stdout.splitlines()
            for line in splitlines:
                if not line.startswith("==>") and len(line.strip()) > 0:
                    logger.debug("Pur output line: %s", line)

                    requirement_info = RequirementInfo(line=line.strip(), file=req_file)
                    if requirement_info not in updated_packages:
                        updated_packages.append(requirement_info)
        except FileNotFoundError:
            logger.error("Error: 'pur' command not found. Please ensure it is installed and in your PATH.")
            return []
        except subprocess.CalledProcessError as e:
            logger.error("Error running 'pur' on file %s: Stdout: %s Stderr: %s", req_file, e.stdout, e.stderr)
            return []
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)
            return []

    return updated_packages


# noqa: BLE001

# --- Example Usage ---

if __name__ == "__main__":
    # Simulate a project directory structure for demonstration
    projects_folder = Path.home() / "adelantos" / "refacil-payment-provider"
    logger.debug(f"Checking for requirements updates in {projects_folder}")
    updated = requirements_updated(projects_folder, level="major")
    if updated:
        CLI_CONSOLE.print("[green]Updated packages:[/green]")
        for pkg in updated:
            CLI_CONSOLE.print(f"- {pkg['library']}: {pkg['file'].stem}")
