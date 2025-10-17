from pathlib import Path

import yaml  # type:ignore[import-untyped]

from funstall.packages.model import PackageData


def main() -> None:
    packages_file_content = Path("./packages.yaml").read_text()
    data = yaml.safe_load(packages_file_content)

    print(PackageData.model_validate(data))


if __name__ == "__main__":
    main()
