from typing import Optional

from sai_rl.sai_console import SAIConsole

from sai_rl.api.requestor_options import RequestorOptions
from sai_rl.api.requestor import APIRequestor

from sai_rl.api.routes.scene import SceneAPI
from sai_rl.api.routes.competition import CompetitionAPI
from sai_rl.api.routes.environment import EnvironmentAPI
from sai_rl.api.routes.package import PackageAPI
from sai_rl.api.routes.submission import SubmissionAPI


class APIClient:
    def __init__(
        self,
        console: SAIConsole,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        max_network_retries: Optional[int] = None,
    ):
        self._console = console

        self._options = RequestorOptions(
            self._console, api_key, api_base, max_network_retries
        )
        self._requestor = APIRequestor(self._console, self._options)

        self.scene = SceneAPI(self._requestor)
        self.competition = CompetitionAPI(self._requestor)
        self.environment = EnvironmentAPI(self._requestor)
        self.package = PackageAPI(self._requestor)
        self.submission = SubmissionAPI(self._requestor)

    @property
    def api_key(self) -> Optional[str]:
        return self._options.api_key

    @property
    def api_base(self) -> Optional[str]:
        return self._options.api_base

    @property
    def max_network_retries(self) -> Optional[int]:
        return self._options.max_network_retries
