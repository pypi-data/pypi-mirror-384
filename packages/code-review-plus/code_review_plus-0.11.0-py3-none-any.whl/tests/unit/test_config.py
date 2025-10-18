import pytest

from code_review.config import DEFAULT_CONFIG, TomlConfigManager


class TestTomlConfigManager:
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create a TomlConfigManager with a temporary config directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return TomlConfigManager(config_dir=config_dir)

    def test_init_with_default_config(self, tmp_path):
        """Test initialization with default configuration."""
        manager = TomlConfigManager(config_dir=tmp_path)
        assert manager.config_data == DEFAULT_CONFIG
        assert manager.config_file == tmp_path / "config.toml"

    def test_init_with_custom_config(self, tmp_path):
        """Test initialization with custom configuration."""
        custom_config = {"test_key": "test_value"}
        TomlConfigManager(config_dir=tmp_path, config_file_name="custom.toml", default_config=custom_config)

    def test_save_and_load_config(self, config_manager, tmp_path):
        """Test saving and loading configuration."""
        config_manager.save_config()  # Create a sample config file
        print("Configuration file saved.", config_manager.config_file)
        assert config_manager.config_file.exists()
