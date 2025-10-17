from typing import Optional, List
from pydantic import ValidationError

from sai_rl.api.requestor import APIRequestor
from sai_rl.types import PackageType
from sai_rl.error import InternalError


def parse_package(package: dict) -> PackageType:
    try:
        return PackageType.model_validate(package)
    except ValidationError as e:
        raise InternalError(f"Error parsing package: {e}", cause=e) from e


class PackageAPI:
    def __init__(self, api: APIRequestor):
        self._api = api

    def get(self, package_name: str) -> Optional[PackageType]:
        response = self._api.get(f"/v1/packages/{package_name}")

        raw_package = response.json()
        if not raw_package:
            return None

        return parse_package(raw_package)

    def list(self) -> Optional[List[PackageType]]:
        response = self._api.get("/v1/packages")

        raw_packages = response.json()
        if not raw_packages:
            return None

        packages: List[PackageType] = []

        for raw_package in raw_packages:
            packages.append(parse_package(raw_package))

        return packages
