from pathlib import Path

import pytest

from code_review.schemas import SemanticVersion


class TestSemanticVersion:
    """Tests for the SemanticVersion class."""

    def setup_method(self):
        """Set up a common file path for tests."""
        self.test_path = Path("test_file.py")

    def test_init(self):
        """Test the initialization of a SemanticVersion object."""
        version = SemanticVersion(major=1, minor=2, patch=3, source=self.test_path, name="my-lib")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.source == self.test_path
        assert str(version) == "1.2.3"

    def test_parse_valid_version(self):
        """Test parsing a valid version string."""
        version_str = "1.2.3"
        version = SemanticVersion.parse_version(version_str, "my-lib", self.test_path)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.source == self.test_path

    @pytest.mark.parametrize("version_str", ["1.2.3.4", "1.2", "abc.def.ghi", "1.a.3"])
    def test_parse_invalid_version(self, version_str):
        """Test parsing invalid version strings returns a default object."""
        version = SemanticVersion.parse_version(version_str, "my-lib", self.test_path)
        assert version.major == 0
        assert version.minor == 0
        assert version.patch == 0
        assert version.source == self.test_path

    def test_parse_invalid_version_with_error_raised(self):
        """Test that parsing an invalid version string raises an error when specified."""
        with pytest.raises(ValueError, match="Invalid version format: 1.2.3.4"):
            SemanticVersion.parse_version("1.2.3.4", "my-lib", self.test_path, raise_error=True)

    def test_comparison_major_version(self):
        """Test comparison based on major version."""
        v1 = SemanticVersion(major=1, minor=0, patch=0, source=self.test_path, name="my-lib")
        v2 = SemanticVersion(major=2, minor=0, patch=0, source=self.test_path, name="my-lib")
        assert v1 < v2
        assert not (v2 < v1)

    def test_comparison_minor_version(self):
        """Test comparison based on minor version."""
        v1 = SemanticVersion(major=1, minor=1, patch=0, source=self.test_path, name="my-lib")
        v2 = SemanticVersion(major=1, minor=2, patch=0, source=self.test_path, name="my-lib")
        assert v1 < v2
        assert not (v2 < v1)

    def test_comparison_patch_version(self):
        """Test comparison based on patch version."""
        v1 = SemanticVersion(major=1, minor=1, patch=1, source=self.test_path, name="my-lib")
        v2 = SemanticVersion(major=1, minor=1, patch=2, source=self.test_path, name="my-lib")
        assert v1 < v2
        assert not (v2 < v1)

    def test_comparison_equal_versions(self):
        """Test that identical versions are not less than each other."""
        v1 = SemanticVersion(major=1, minor=1, patch=1, source=self.test_path, name="my-lib")
        v2 = SemanticVersion(major=1, minor=1, patch=1, source=self.test_path, name="my-lib")
        assert not (v1 < v2)
        assert not (v2 < v1)
