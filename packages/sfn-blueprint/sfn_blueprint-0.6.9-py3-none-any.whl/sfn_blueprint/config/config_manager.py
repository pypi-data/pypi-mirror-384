import json
import yaml
from typing import Optional
from sfn_blueprint.utils.logging import setup_logger

class SFNConfigManager:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.logger, _ = setup_logger(logger_name="SFNConfigManager")
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> dict:
        """
        Load configuration from the specified path.
        
        :param path: Path to the configuration file (supports JSON and YAML).
        :return: Loaded configuration as a dictionary.
        """
        try:
            with open(path, "r") as file:
                if path.endswith(".json"):
                    self.logger.info("Loading configuration from JSON file.")
                    return json.load(file)
                elif path.endswith(".yaml") or path.endswith(".yml"):
                    self.logger.info("Loading configuration from YAML file.")
                    return yaml.safe_load(file)
                else:
                    self.logger.error(f"Unsupported file format for path: {path}")
                    raise ValueError("Unsupported configuration file format")
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON configuration file: {str(e)}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error decoding YAML configuration file: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while loading config: {str(e)}")
            raise

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve the value for a given key from the configuration.
        :param key: Configuration key to look up.
        :param default: Default value to return if key is not found.
        :return: Value associated with the key, or default if key is not present.
        """
        value = self.config.get(key, default)
        if value is default:
            self.logger.warning(f"Key '{key}' not found, returning default: {default}")
        return value
