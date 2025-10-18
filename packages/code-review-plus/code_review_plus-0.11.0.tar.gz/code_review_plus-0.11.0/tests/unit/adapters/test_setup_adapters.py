import pytest

from code_review.adapters.setup_adapters import setup_to_dict


class TestSetupToDict:
    # Pytest fixture to create a temporary directory and files
    @pytest.fixture
    def setup_config_files(self, tmp_path):
        # Create a valid .cfg file
        valid_cfg_content = """
        [section_one]
        key1 = value1
        key2 = value2

        [section_two]
        key3 = 123
        key4 = True
        """
        valid_file = tmp_path / "valid.cfg"
        valid_file.write_text(valid_cfg_content)

        # Create a .cfg file with a 'bumpversion' section
        bumpversion_cfg_content = """
        [bumpversion]
        tag = True
        commit = False
        """
        bumpversion_file = tmp_path / "bumpversion.cfg"
        bumpversion_file.write_text(bumpversion_cfg_content)

        # Create an invalid file without a section header
        invalid_cfg_content = "key=value"
        invalid_file = tmp_path / "invalid.cfg"
        invalid_file.write_text(invalid_cfg_content)

        return {
            "valid": valid_file,
            "bumpversion": bumpversion_file,
            "invalid": invalid_file,
            "non_existent": tmp_path / "non_existent.cfg",
        }

    def test_valid_file_parsing(self, setup_config_files):
        """Tests that a valid .cfg file is parsed correctly into a dictionary."""
        file_path = setup_config_files["valid"]
        result = setup_to_dict(file_path)
        expected = {
            "section_one": {"key1": "value1", "key2": "value2"},
            "section_two": {"key3": "123", "key4": "True"},
        }
        assert result == expected, "The function should correctly parse a standard .cfg file."

    def test_bumpversion_section_parsing(self, setup_config_files):
        """Tests that the 'bumpversion' section's boolean values are parsed correctly."""
        file_path = setup_config_files["bumpversion"]
        result = setup_to_dict(file_path)
        expected = {"bumpversion": {"tag": True, "commit": False}}
        assert result == expected, "The function should parse 'bumpversion' boolean values correctly."

    def test_file_not_found_no_error(self, setup_config_files):
        """Tests that a non-existent file returns an empty dictionary when raise_error is False."""
        file_path = setup_config_files["non_existent"]
        result = setup_to_dict(file_path)
        assert result == {}, "A non-existent file should return an empty dictionary."

    def test_file_not_found_with_error(self, setup_config_files):
        """Tests that a FileNotFoundError is raised when a file is not found and raise_error is True."""
        file_path = setup_config_files["non_existent"]
        with pytest.raises(FileNotFoundError, match=f"Error: The file '{file_path}' was not found."):
            setup_to_dict(file_path, raise_error=True)

    def test_invalid_file_format(self, setup_config_files):
        """Tests that a ValueError is raised for an invalid INI-style file."""
        file_path = setup_config_files["invalid"]
        with pytest.raises(ValueError, match=f"Error: The file '{file_path}' is not a valid INI-style file."):
            setup_to_dict(file_path)

    def test_empty_file_parsing(self, tmp_path):
        """Tests that an empty file returns an empty dictionary."""
        empty_file = tmp_path / "empty.cfg"
        empty_file.touch()
        result = setup_to_dict(empty_file)
        assert result == {}, "An empty file should return an empty dictionary."

    def test_bumpversion_file(self, fixtures_folder):
        bumpversion_file = fixtures_folder / "bumpversion.cfg"
        result = setup_to_dict(bumpversion_file)
        assert result["bumpversion"]["current_version"] == "3.1.4"
