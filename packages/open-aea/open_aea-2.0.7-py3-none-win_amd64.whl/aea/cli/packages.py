# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Package manager."""


import sys
from pathlib import Path
from typing import List, cast
from warnings import warn

import click

from aea.cli.utils.click_utils import PackagesSource
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.configurations.constants import PACKAGES
from aea.package_manager.base import BasePackageManager, PackageFileNotValid
from aea.package_manager.v0 import PackageManagerV0
from aea.package_manager.v1 import PackageManagerV1


try:
    from aea_cli_ipfs.registry import (  # type: ignore # noqa: F401 # pylint: disable=unused-import
        fetch_ipfs,
    )

    IS_IPFS_PLUGIN_INSTALLED = True
except ModuleNotFoundError:  # pragma: nocover  # cause obvious
    IS_IPFS_PLUGIN_INSTALLED = False


class SyncTypes:  # pylint: disable=too-few-public-methods
    """Types of syncs."""

    DEV = "dev"
    THIRD_PARTY = "third_party"
    ALL = "all"


def package_type_selector_prompt() -> str:
    """Selector prompt for local package type."""
    return click.prompt(
        "Select package type",
        type=click.Choice(
            (
                PackageManagerV1.LocalPackageType.DEV.value,
                PackageManagerV1.LocalPackageType.THIRD_PARTY.value,
            )
        ),
    )


@click.group("packages")
@click.pass_context
def package_manager(
    click_context: click.Context,  # pylint: disable=unused-argument
) -> None:
    """Local package manager."""


@package_manager.command()
@pass_ctx
@click.option(
    "--update-packages",
    is_flag=True,
    help="Download packages from a remote registry so that local packages match the hashes in packages.json.",
)
@click.option(
    "--update-hashes",
    is_flag=True,
    help="Recalculate hashes in packages.json so that they match the local packages.",
)
@click.option(
    "--dev",
    "sync_type",
    flag_value=SyncTypes.DEV,
    help="To sync dev packages.",
    default=False,
)
@click.option(
    "--third-party",
    "sync_type",
    flag_value=SyncTypes.THIRD_PARTY,
    help="To sync third party packages (default).",
    default=True,
)
@click.option(
    "--all",
    "sync_type",
    flag_value=SyncTypes.ALL,
    help="To sync all available packages.",
    default=False,
)
@click.option(
    "-s",
    "--source",
    "sources",
    type=PackagesSource(),
    help="Provide source name from where hashes can be synced.",
    multiple=True,
)
def sync(
    ctx: Context,
    update_packages: bool,
    update_hashes: bool,
    sync_type: str,
    sources: List[str],
) -> None:
    """Sync packages between packages.json and a local registry."""

    if not IS_IPFS_PLUGIN_INSTALLED:
        raise click.ClickException(
            "Please install ipfs plugin using `pip3 install open-aea-cli-ipfs`"
        )

    if update_hashes and update_packages:
        raise click.ClickException(
            "You cannot use both `--update-hashes` and `--update-packages` at the same time."
        )

    packages_dir = Path(ctx.registry_path)
    try:
        manager = get_package_manager(packages_dir)
        if isinstance(manager, PackageManagerV0):
            cast(PackageManagerV0, manager).sync(
                dev=(sync_type == SyncTypes.DEV or sync_type == SyncTypes.ALL),
                third_party=(
                    sync_type == SyncTypes.THIRD_PARTY or sync_type == SyncTypes.ALL
                ),
                update_packages=update_packages,
                update_hashes=update_hashes,
            )
        else:
            cast(PackageManagerV1, manager).sync(
                dev=(sync_type == SyncTypes.DEV or sync_type == SyncTypes.ALL),
                third_party=(
                    sync_type == SyncTypes.THIRD_PARTY or sync_type == SyncTypes.ALL
                ),
                update_packages=update_packages,
                update_hashes=update_hashes,
                sources=sources,
            )
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@package_manager.command(name="lock")
@click.option(
    "--check",
    is_flag=True,
    help="Check packages.json",
)
@click.option(
    "--skip-missing",
    is_flag=True,
    help="Skip packages missing from the `packages.json` file.",
)
@pass_ctx
def lock_packages(ctx: Context, check: bool, skip_missing: bool) -> None:
    """Lock packages. Updates hashes in packages.json so that they match the local packages."""

    packages_dir = Path(ctx.registry_path)

    try:
        if check:
            packages_dir = Path(ctx.registry_path)
            click.echo("Verifying packages.json")
            return_code = get_package_manager(packages_dir).verify()
            if return_code:
                click.echo("Verification failed.")
            else:
                click.echo("Verification successful")
            sys.exit(return_code)

        click.echo("Updating hashes")
        get_package_manager(packages_dir).update_package_hashes(
            selector_prompt=package_type_selector_prompt, skip_missing=skip_missing
        ).dump()

        click.echo("Done")
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e)) from e


@package_manager.command(name="init")
def _init_packages_repo() -> None:
    """Initialize packages repository."""

    packages_dir = Path.cwd() / PACKAGES
    if packages_dir.exists():
        raise click.ClickException(
            f"Packages repository already exists @ {packages_dir}"
        )

    packages_dir.mkdir()
    PackageManagerV1(path=packages_dir).dump()
    click.echo(f"Initialized packages repository @ {packages_dir}")


def get_package_manager(package_dir: Path) -> BasePackageManager:
    """Get package manager."""

    try:
        return PackageManagerV1.from_dir(package_dir)
    except PackageFileNotValid:
        warn(
            "The provided `packages.json` still follows an older format which will be deprecated on v2.0.0",
            DeprecationWarning,
            stacklevel=2,
        )
        click.echo(
            "The provided `packages.json` still follows an older format which will be deprecated on v2.0.0"
        )
        return PackageManagerV0.from_dir(package_dir)
