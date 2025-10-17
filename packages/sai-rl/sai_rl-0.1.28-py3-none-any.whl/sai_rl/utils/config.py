import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

DEFAULT_CONFIG = {
    "api": {
        "token": "",
        "platform_url": "https://competesai.com",
        "api_url": "https://api.competesai.com",
        "max_network_retries": 3,
        "timeout": 10,
        "retry_delay": 1,
    },
    "temp_path": Path.home() / ".sai" / "temp",
}


class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".sai"
        self.config_file = self.config_dir / "config.toml"
        self.config = self._load_config()

    def _create_default_config(self):
        """Create default configuration file if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, "w") as f:
            toml_str = "[api]\n"
            toml_str += f'token = "{DEFAULT_CONFIG["api"]["token"]}"\n'
            toml_str += f'platform_url = "{DEFAULT_CONFIG["api"]["platform_url"]}"\n'
            toml_str += f'api_url = "{DEFAULT_CONFIG["api"]["api_url"]}"\n'
            f.write(toml_str)

    def _load_config(self):
        """Load configuration from file if it exists, otherwise use defaults."""
        if not self.config_file.exists():
            self._create_default_config()
            return DEFAULT_CONFIG

        with open(self.config_file, "rb") as f:
            user_config = tomllib.load(f)

        # Merge user config with defaults, preserving user values
        merged_config = DEFAULT_CONFIG.copy()
        if "api" in user_config:
            merged_config["api"].update(user_config["api"])

        return merged_config

    @property
    def api_token(self):
        return self.config["api"]["token"]

    @property
    def platform_url(self):
        return self.config["api"]["platform_url"]

    @property
    def api_url(self):
        return self.config["api"]["api_url"]

    @property
    def max_network_retries(self):
        return self.config["api"]["max_network_retries"]

    @property
    def timeout(self):
        return self.config["api"]["timeout"]

    @property
    def retry_delay(self):
        return self.config["api"]["retry_delay"]

    @property
    def temp_path(self):
        return self.config["temp_path"]


config = Config()
