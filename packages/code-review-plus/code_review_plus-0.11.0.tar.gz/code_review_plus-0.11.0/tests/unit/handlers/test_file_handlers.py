import os
from pathlib import Path

import pytest

from code_review.handlers.file_handlers import get_all_project_folder, get_not_ignored

# Assuming your function is in a file named `my_module.py`


# You can use `tmp_path` as a fixture for each test method.
# Pytest will automatically create a unique, temporary directory for each test
# and clean it up afterward.
# The class name must start with `Test` for pytest to discover it.
class TestGetNotIgnored:
    def test_no_gitignore_all_files_included(self, tmp_path: Path):
        """
        Test case where there is no .gitignore file.
        All files matching the pattern should be returned.
        """
        # Create a nested directory structure and files
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "Dockerfile").touch()
        (tmp_path / "web").mkdir()
        (tmp_path / "web" / "Dockerfile").touch()
        (tmp_path / "README.md").touch()  # A file that doesn't match the pattern

        # Expected list of files
        expected_files = [
            tmp_path / "app" / "Dockerfile",
            tmp_path / "web" / "Dockerfile",
        ]

        found_files = get_not_ignored(tmp_path, "Dockerfile")

        # Convert to sets for easy comparison, as the order is not guaranteed by rglob
        assert set(found_files) == set(expected_files)

    def test_simple_gitignore_file_ignored(self, tmp_path: Path):
        """
        Test case where a specific file is ignored by .gitignore.
        """
        # Create the .gitignore file
        (tmp_path / ".gitignore").write_text("app/")

        # Create the files
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "Dockerfile").touch()
        (tmp_path / "web").mkdir()
        (tmp_path / "web" / "Dockerfile").touch()

        # Only the web/Dockerfile should be returned
        expected_files = [tmp_path / "web" / "Dockerfile"]

        found_files = get_not_ignored(tmp_path, "Dockerfile")

        assert set(found_files) == set(expected_files)

    def test_gitignore_folder_ignored(self, tmp_path: Path):
        """
        Test case where an entire folder is ignored.
        """
        # Create the .gitignore file to ignore the 'app' directory
        (tmp_path / ".gitignore").write_text("app/")

        # Create the directory structure and files
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "Dockerfile").touch()
        (tmp_path / "app" / "sub_dir").mkdir()
        (tmp_path / "app" / "sub_dir" / "Dockerfile").touch()
        (tmp_path / "web").mkdir()
        (tmp_path / "web" / "Dockerfile").touch()

        # Only the web/Dockerfile should be returned
        expected_files = [tmp_path / "web" / "Dockerfile"]

        found_files = get_not_ignored(tmp_path, "Dockerfile")

        assert set(found_files) == set(expected_files)

    def test_gitignore_with_negation(self, tmp_path: Path):
        """
        Test case where a file is explicitly un-ignored using '!'.
        """
        # Create the .gitignore file with a negation
        (tmp_path / ".gitignore").write_text("app/\n!app/Dockerfile_special")

        # Create the files
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "Dockerfile").touch()
        (tmp_path / "app" / "Dockerfile_special").touch()
        (tmp_path / "web").mkdir()
        (tmp_path / "web" / "Dockerfile").touch()

        # The web/Dockerfile and the special Dockerfile should be returned
        expected_files = [
            tmp_path / "web" / "Dockerfile",
            tmp_path / "app" / "Dockerfile_special",
        ]

        found_files = get_not_ignored(tmp_path, "Dockerfile*")

        assert set(found_files) == set(expected_files)

    def test_non_existent_folder_raises_error(self, tmp_path: Path):
        """
        Test case to ensure a FileNotFoundError is raised for a non-existent folder.
        """
        non_existent_path = tmp_path / "non_existent_folder"

        # Use pytest.raises to check for the specific exception
        with pytest.raises(FileNotFoundError):
            get_not_ignored(non_existent_path, "Dockerfile")

    def test_empty_folder(self, tmp_path: Path):
        """
        Test case for an empty folder.
        """
        found_files = get_not_ignored(tmp_path, "Dockerfile")

        assert found_files == []


def test_env_vars_set(load_environment_vars):
    folder_var = os.getenv("PROJECTS_FOLDER")
    folder = Path(folder_var).expanduser().resolve()
    assert folder_var == "~/PycharmProjects"
    assert folder.exists()


def test_get_all_project_folder(load_environment_vars):
    folder_var = os.getenv("PROJECTS_FOLDER")
    folder = Path(folder_var).expanduser().resolve()
    project_folders = get_all_project_folder(folder)

    assert len(project_folders) > 0
