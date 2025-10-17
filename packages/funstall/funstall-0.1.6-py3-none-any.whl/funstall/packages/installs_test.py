import logging
import textwrap
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from funstall.config import Settings
from funstall.packages import installs
from funstall.packages.model import Package


@pytest.fixture
def app_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_dir))
    monkeypatch.setattr(
        installs.system_paths, "user_data_dir", lambda: data_dir / "funstall"
    )
    return data_dir / "funstall"


@pytest.fixture(name="ctx")
def mock_ctx(mocker: MockerFixture):
    return {
        "logger": mocker.MagicMock(spec=logging.Logger),
        "settings": mocker.MagicMock(spec=Settings),
    }


def test_add_to_empty_installs_file(
    app_data_dir: Path,
    mocker: MockerFixture,
    ctx,
) -> None:
    installs_file = app_data_dir / "installed.toml"

    assert not installs_file.exists()
    assert not installs.is_installed("my-app")
    # The check should have created an empty file
    assert installs_file.exists()
    assert installs_file.read_text() == "installed=[]"

    package1 = Package(name="my-app", sources=[])
    installs.add_installed(ctx, package1, source_kind="pip")

    expected_content_1 = textwrap.dedent(
        """\
        installed = [
            { name = "my-app", source_kind = "pip" },
        ]
        """
    )
    assert installs_file.read_text() == expected_content_1
    assert installs.is_installed("my-app")


def test_add_to_nonempty_installs_file(
    app_data_dir: Path,
    mocker: MockerFixture,
    ctx,
) -> None:
    installs_file = app_data_dir / "installed.toml"

    installs_file.parent.mkdir(parents=True)
    installs_file.write_text(
        textwrap.dedent(
            """\
            installed = [
                { name = "package-1", source_kind = "pip" },
            ]
        """
        )
    )

    package1 = Package(name="package-2", sources=[])
    installs.add_installed(ctx, package1, source_kind="pacman")

    expected_content_1 = textwrap.dedent(
        """\
        installed = [
            { name = "package-1", source_kind = "pip" },
            { name = "package-2", source_kind = "pacman" },
        ]
        """
    )
    assert installs_file.read_text() == expected_content_1
    assert installs.is_installed("package-1")
    assert installs.is_installed("package-2")
    assert installs.get_install_source("package-2") == "pacman"


def test_get_install_source(app_data_dir: Path) -> None:
    installs_file = app_data_dir / "installed.toml"
    installs_file.parent.mkdir(parents=True)
    content = textwrap.dedent(
        """\
        installed = [
            { name = "tool-a", source_kind = "pip" },
            { name = "tool-b", source_kind = "brew" },
        ]
        """
    )
    installs_file.write_text(content)

    assert installs.get_install_source("tool-a") == "pip"
    assert installs.get_install_source("tool-b") == "brew"
    assert installs.get_install_source("non-existent-tool") is None


def test_warn_about_missing_package(
    app_data_dir: Path, mocker: MockerFixture, ctx
) -> None:
    installs_file = app_data_dir / "installed.toml"
    installs_file.parent.mkdir(parents=True)
    content = textwrap.dedent(
        """\
        installed = [
            { name = "tool_1", source_kind = "pip" },
            { name = "old_tool", source_kind = "pacman" },
            { name = "tool_2", source_kind = "pip" },
        ]
        """
    )
    installs_file.write_text(content)

    package_tool_1 = Package(name="tool_1", sources=[])
    package_tool_2 = Package(name="tool_2", sources=[])

    def get_package_fake(settings: Settings, name: str) -> Package | None:
        return {"tool_1": package_tool_1, "tool_2": package_tool_2}.get(name)

    mock_get_package = mocker.patch(
        "funstall.packages.installs.get_package",
        side_effect=get_package_fake,
    )

    result = installs.installed_packages(ctx)
    assert result == [package_tool_1, package_tool_2]

    assert mock_get_package.call_count == 3
    mock_get_package.assert_any_call(ctx["settings"], "tool_1")
    mock_get_package.assert_any_call(ctx["settings"], "old_tool")
    mock_get_package.assert_any_call(ctx["settings"], "tool_2")

    ctx["logger"].warning.assert_called_once()
    warning_args = ctx["logger"].warning.call_args[0]
    assert "Package %s is installed" in warning_args[0]
    assert warning_args[1].name == "old_tool"


def test_installed_packages_empty(
    app_data_dir: Path, mocker: MockerFixture, ctx
) -> None:
    result = installs.installed_packages(ctx)
    assert result == []
