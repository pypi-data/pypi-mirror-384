import httpx
import yaml  # type:ignore[import-untyped]

from funstall.config import Settings
from funstall.packages.model import (
    InvalidPackageFileError,
    Package,
    PackageData,
)


def available_packages(settings: Settings) -> list[Package]:
    return [p for p in _package_data(settings).packages]


def get_package(settings: Settings, name: str) -> Package | None:
    for p in available_packages(settings):
        if p.name == name:
            return p
    return None


def update_package_definitions(settings: Settings) -> None:
    package_file_url = str(settings.package_file_url)
    try:
        new_content = httpx.get(package_file_url).text
    except httpx.HTTPError:
        pass

    try:
        yaml.safe_load(new_content)
    except yaml.YAMLError:
        raise InvalidPackageFileError(
            "Can't update the package file list right now because the "
            "remote package file is not valid."
        )

    # Path.write_text overwrites a file
    settings.package_definitions_file.write_text(new_content)


def _package_data(settings: Settings) -> PackageData:
    packages_file_content = settings.package_definitions_file.read_text()
    data = yaml.safe_load(packages_file_content)

    return PackageData.model_validate(data)
