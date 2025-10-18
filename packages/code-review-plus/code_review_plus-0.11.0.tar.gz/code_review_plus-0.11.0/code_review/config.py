import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import toml
import tomllib

logger = logging.getLogger(__name__)
# Define a dictionary of default configuration settings.
# These values will be used if the TOML file is not found or
# specific settings are missing.
DEFAULT_CONFIG = {
    "doc_folder": Path.home() / "Documents" / "code_review_plus",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "max_lines_to_display": 100,
    "docker_images": {
        "python": "3.12.11-slim-bookworm",
        "node": "20.19.4-alpine3",
        "postgres": "16.10-bookworm",
    },
    "default_branches": ["master", "develop"],
}


class TomlConfigManager:
    """A class to manage reading and writing TOML configuration files."""

    def __init__(
        self,
        config_dir: Path = Path.home() / ".config" / "code_review_plus",
        config_file_name: str = "config.toml",
        default_config: dict[str, Any] = None,
    ) -> None:
        """Initializes the TomlConfigManager.

        Args:
            config_dir (Path): The directory where the config file is located.
            config_file_name (str): The name of the main config file.
            default_config (dict[str, Any]): The default configuration dictionary.
        """
        self.config_dir = config_dir
        self.config_file = self.config_dir / config_file_name
        self.config_data: dict[str, Any] = default_config.copy() if default_config else DEFAULT_CONFIG.copy()

    def load_config(self) -> dict[str, Any]:
        """Reads the application's configuration from a TOML file.

        The function looks for a 'config.toml' file in the user's
        recommended configuration directory. It merges the settings from the file
        with a set of default values, ensuring all variables are always set.

        Returns:
            dict: A dictionary containing the complete application configuration.
        """
        if not self.config_file.is_file():
            logger.debug("Configuration file not found. Using default settings.")
            return self.config_data

        try:
            with open(self.config_file, "rb") as f:
                toml_data = tomllib.load(f)

            # Extract the settings for our application.
            app_settings = toml_data.get("tool", {}).get("cli_app", {})

            # Update the configuration with values from the TOML file.
            self.config_data.update(
                {
                    "doc_folder": Path(app_settings.get("doc_folder", self.config_data["doc_folder"])).expanduser(),
                    "date_format": app_settings.get("date_format", self.config_data["date_format"]),
                    "max_lines_to_display": app_settings.get(
                        "max_lines_to_display",
                        self.config_data["max_lines_to_display"],
                    ),
                    "docker_images": app_settings.get("docker_images", self.config_data["docker_images"]),
                }
            )

        except tomllib.TOMLDecodeError as e:
            logger.error("Error decoding TOML file: %s. Using default settings.", e)
        except Exception as e:
            logger.error(
                "An unexpected error occurred while reading the config: %s. Using default settings.",
                e,
            )

        return self.config_data

    def save_config(self, data: dict[str, Any] = None, create_backup: bool = True) -> None:
        """Saves the current configuration to a TOML file.

        Args:
            data (dict): The dictionary to save. If None, the current
                         config_data of the instance will be saved.
            create_backup (bool): If True, a timestamped backup file will be created.
        """
        data_to_save = data if data is not None else self.config_data

        # Create a nested dictionary structure for the TOML file
        config_to_write = {"tool": {"cli_app": {}}}
        # Filter out the docker_images from the root level
        root_data = {k: v for k, v in data_to_save.items() if k not in ["docker_images"]}

        config_to_write["tool"]["cli_app"].update(root_data)

        # Add the docker_images section
        config_to_write["tool"]["cli_app"]["docker_images"] = data_to_save.get("docker_images", {})

        self.config_dir.mkdir(parents=True, exist_ok=True)

        if create_backup and self.config_file.is_file():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_file = self.config_dir / f"config-{timestamp}.toml"
            try:
                self.config_file.rename(backup_file)
                logger.info("Created backup file: %s", backup_file)
            except OSError as e:
                logger.error("Error creating backup file: %s", e)

        try:
            with open(self.config_file, "w") as f:
                toml.dump(config_to_write, f)
            logger.info("Configuration saved to %s", self.config_file)
        except Exception as e:
            logger.error("An unexpected error occurred while saving the config: %s", e)


CONFIG_MANAGER = TomlConfigManager()


def get_config(manager: TomlConfigManager = CONFIG_MANAGER) -> dict[str, Any]:
    """Reads the application's configuration from a TOML file.

    The function looks for a 'config.toml' file in the user's
    recommended configuration directory. It merges the settings from the file
    with a set of default values, ensuring all variables are always set.

    Returns:
        dict: A dictionary containing the complete application configuration.
    """
    config = manager.load_config()
    if not manager.config_file.exists():
        manager.save_config(config, create_backup=True)
    return config
