from typing import Optional

import os

from sai_rl.sai_console import SAIConsole
from sai_rl.error import ConfigurationError
from sai_rl.utils import config


class RequestorOptions(object):
    def __init__(
        self,
        console: SAIConsole,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        max_network_retries: Optional[int] = None,
    ):
        self._console = console
        self._api_key = api_key
        self._api_base = self._get_api_base(api_base)
        self._validate_api_base(self._api_base or "")

        self._max_network_retries = self._get_max_network_retries(max_network_retries)

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key is not None:
            return self._api_key
        elif os.getenv("SAI_API_KEY") is not None:
            self._api_key = os.getenv("SAI_API_KEY")
        else:
            self._api_key = config.api_token

        return self._api_key

    @staticmethod
    def _get_api_base(api_base: Optional[str] = None) -> Optional[str]:
        if api_base:
            return api_base

        env_api_base = os.getenv("SAI_API_BASE")
        if env_api_base:
            return env_api_base

        return config.api_url

    @staticmethod
    def _validate_api_base(api_base: str):
        if not api_base.startswith("http"):
            raise ConfigurationError("API base must start with 'http'")

    @property
    def api_base(self) -> str:
        assert self._api_base is not None
        return self._api_base

    @staticmethod
    def _get_max_network_retries(
        max_network_retries: Optional[int] = None,
    ) -> Optional[int]:
        if max_network_retries:
            return max_network_retries

        return config.max_network_retries

    @property
    def max_network_retries(self) -> int:
        assert self._max_network_retries is not None
        return self._max_network_retries

    def to_dict(self):
        """
        Returns a dict representation of the object.
        """
        return {
            "api_key": self.api_key,
            "api_base": self.api_base,
            "max_network_retries": self.max_network_retries,
        }
