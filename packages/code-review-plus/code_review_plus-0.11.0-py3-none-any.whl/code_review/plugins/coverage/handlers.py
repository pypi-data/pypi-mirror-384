import os
import re
import subprocess
from pathlib import Path, PosixPath
from typing import Any

import yaml

from code_review.plugins.coverage.schemas import TestConfiguration
from code_review.handlers.file_handlers import change_directory


def run_tests_and_get_coverage(
    folder: Path, unit_tests: str, minimum_coverage: int, settings_module: str = "config.settings.test"
) -> dict[str, Any]:
    """Changes to a specified folder, runs a Django test suite with coverage,
    reports the coverage, and extracts the coverage percentage.

    Args:
        folder (str): The path to the directory containing the docker-compose file.
        unit_tests (str): A string of space-separated paths to unit tests.
        minimum_coverage (int): The minimum acceptable code coverage percentage.

    Returns:
        float: The extracted code coverage percentage.

    Raises:
        subprocess.CalledProcessError: If either the test or coverage report command fails.
        ValueError: If the coverage percentage cannot be extracted from the output.
    """
    original_cwd = os.getcwd()
    try:
        change_directory(folder)

        # Command to run unit tests with coverage
        test_command = (
            f"docker-compose -f local.yml run --rm django coverage run "
            f"manage.py test {unit_tests} --settings={settings_module} "
            f"--exclude-tag=INTEGRATION"
        )
        print(f"Running command: {test_command}")
        subprocess.run(test_command, shell=True, check=True)

        # Command to report coverage and check against minimum
        report_command = (
            f"docker-compose -f local.yml run --rm django coverage report -m --fail-under={minimum_coverage}"
        )
        print(f"Running command: {report_command}")
        result = subprocess.run(report_command, shell=True, check=False, text=True, capture_output=True)

        # Extract coverage from the output
        coverage_output = result.stdout
        with open(os.path.join(folder, "__coverage.txt"), "w") as f:
            f.write(coverage_output)

        test_count_match = re.search(
            r"Ran\s+(?P<test_count>\d+)\s+tests\s+in\s+(?P<running_time>[\d\.]+)s", coverage_output
        )

        test_count = -1
        running_time = -1.0
        coverage_percentage = -1.0

        if test_count_match:
            test_count = int(test_count_match.group("test_count"))
            running_time = float(test_count_match.group("running_time"))
        # Regular expression to find the total coverage percentage
        # It looks for a line with "TOTAL" and a number ending with "%"
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%", coverage_output)
        if match:
            coverage_percentage = float(match.group(1))

        return {"test_count": test_count, "running_time": running_time, "coverage_percentage": coverage_percentage}
    finally:
        os.chdir(original_cwd)


# Example Usage:
if __name__ == "__main__":
    try:
        # Replace these with your actual folder, test paths, and desired coverage
        target_folder = Path.home() / "adelantos" / "payment-options-vue"
        tests_to_run = "pay_options_middleware.middleware.tests.unit pay_options_middleware.users.tests"
        min_coverage = 85

        target_folder = Path.home() / "adelantos" / "wu-integration"
        tests_to_run = "wu_integration.rest.tests.unit"
        min_coverage = 85

        target_folder = Path.home() / "adelantos" / "payment-collector"
        tests_to_run = [
            "payment_collector.api.tests.unit payment_collector.users.tests",
            " payment_collector.reconciliation.tests",
        ]
        min_coverage = 85.0
        settings_module_t = "config.settings.local"

        test_configuration = TestConfiguration(
            folder=target_folder, unit_tests=tests_to_run, min_coverage=min_coverage, settings_module=settings_module_t
        )

        config_data = test_configuration.model_dump()
        yaml_file_path: PosixPath = Path("test_configuration.yml")

        with open(yaml_file_path, "w") as file:
            # `sort_keys=False` is often used to maintain the order from the model/dictionary
            # `default_flow_style=False` ensures a block-style (multi-line) YAML output for readability
            yaml.dump(config_data, file, sort_keys=False, default_flow_style=False)

        coverage = run_tests_and_get_coverage(
            target_folder, tests_to_run, min_coverage, settings_module=settings_module_t
        )
        print(f"\n>>>>>>>>>>>>>>>>>>>> Successfully completed. Final coverage: {coverage}%")

    except subprocess.CalledProcessError as e:
        print("\nXXXXXXXXXXXXX An error occurred during a command execution:")
        print(f"Return code: {e.returncode}")
        print(f"Command: {e.cmd}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        print("\nTests failed or coverage was below the minimum. Exiting.")
    except FileNotFoundError:
        print(f"\nError: The specified folder '{target_folder}' does not exist.")
    except ValueError as e:
        print(f"\nError: {e}")
