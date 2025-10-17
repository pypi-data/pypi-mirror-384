from functools import wraps

import click

from funstall.application_context import (
    ApplicationContext,
    create_application_context,
)
from funstall.config import Settings
from funstall.custom_click_types import string_list
from funstall.installation.installation import install, update, update_all
from funstall.packages.installs import is_installed
from funstall.packages.package_definitions import available_packages

# Command options and arguments


def package_name_argument(f):
    return click.argument("package")(f)


# Options to modify Settings


def package_file_url_option(f):
    return click.option(
        "--package-list-url",
        default=None,
        help="URL to the package list file to use",
    )(f)


def verbosity_option(f):
    return click.option(
        "--verbosity",
        default=None,
        help=(
            "Configure informative messages which will be written to stderr. "
            "May be set to 'silent', 'error', 'info', or 'debug'. Default is "
            "'info'."
        ),
    )(f)


def skip_self_update_option(f):
    return click.option(
        "--skip-self-update",
        is_flag=True,
        help=("Skip the automatic self update."),
    )(f)


def self_update_strategy_option(f):
    return click.option(
        "--self-update-strategy",
        default=None,
        help=(
            "How to run the self update, either 'pypi' (download the latest "
            "release from pypi) or 'noop' (don't do anything; useful only "
            "during development)"
        ),
    )(f)


def package_file_option(f):
    return click.option(
        "--package-file",
        default=None,
        help=(
            "Path to a custom packages.yaml file to use instead of "
            "downloading the latest one from the repository."
        ),
    )(f)


def with_application_context(f):
    """Adds the application context to a CLI command.

    This decorator adds command options that modify common application
    settings. It then adds the application context (settings and services) to
    the decorated functions' arguments.
    """

    @package_file_url_option
    @verbosity_option
    @skip_self_update_option
    @self_update_strategy_option
    @package_file_option
    @wraps(f)
    def g(
        *args,
        package_list_url: str | None,
        verbosity: str | None,
        skip_self_update: bool,
        self_update_strategy: str | None,
        package_file: str | None,
        **kwargs,
    ) -> None:
        settings_kwargs = {
            "package_file_url": package_list_url,
            "verbosity": verbosity,
            "skip_self_update": skip_self_update,
            "self_update_strategy": self_update_strategy,
        }
        if package_file:
            settings_kwargs |= {
                "package_definitions_file": package_file,
                "skip_package_definitions_file_download": True,
            }
        settings = Settings.model_validate(
            {k: v for k, v in settings_kwargs.items() if v is not None}
        )
        ctx = create_application_context(settings)
        return f(*args, ctx=ctx, **kwargs)

    return g


@click.group()
def funstall():
    pass


@funstall.command("config", help="Show the active configuration")
@with_application_context
def show_config(ctx: ApplicationContext) -> None:
    for k, v in ctx["settings"].model_dump().items():
        print(f"{k} = '{v}'")


@funstall.command("list", help="List available packages")
@with_application_context
def list_packages(ctx: ApplicationContext) -> None:
    ctx["logger"].info("Available packages:")

    for p in available_packages(ctx["settings"]):
        print(p.name)


@funstall.command("update", help="Update packages")
@click.option(
    "--install-missing",
    is_flag=True,
    help="Install missing packages, if any passed with the --packages option",
)
@click.option(
    "--packages",
    type=string_list,
    default=None,
    help=(
        "Packages to update; pass multiple packages separated by commas, e.g. "
        "'foo,bar,baz'"
    ),
)
@with_application_context
@click.pass_context
def update_packages(
    click_context: click.Context,
    packages: list[str] | None,
    install_missing: bool,
    ctx: ApplicationContext,
) -> None:
    if packages:
        for package in packages:
            if not is_installed(package):
                if install_missing:
                    install(ctx, package)
                else:
                    click_context.fail(
                        f"Package {package} is marked to be updated, but it "
                        "is not installed. Pass the --install-missing flag to "
                        "automatically install missing packages."
                    )
        update(ctx, packages)
    else:
        update_all(ctx)


@funstall.command("install", help="Install a package")
@package_name_argument
@with_application_context
def install_package(
    package: str,
    ctx: ApplicationContext,
) -> None:
    install(ctx, package)
