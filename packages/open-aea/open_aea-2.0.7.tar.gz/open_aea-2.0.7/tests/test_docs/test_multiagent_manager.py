# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
#   Copyright 2018-2019 Fetch.AI Limited
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

"""This module contains the tests for the content of multi-agent-manager.md file."""
import os
import shutil
import tempfile
from importlib import import_module
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest

from aea.cli.registry.settings import REMOTE_HTTP

from tests.conftest import (
    MAX_FLAKY_RERUNS,
    PACKAGES_DIR,
    ROOT_DIR,
    TEST_IPFS_REGISTRY_CONFIG,
)
from tests.test_docs.helper import BasePythonMarkdownDocs


def _import_module_mock(arg):
    """
    Mock importlib.import_module only if argument is a dummy one: 'some.dotted.path'.

    This choice is tight to the code examples in 'ledger-integration.md'.
    It helps to tests the cases in which the import path is not a fake one.
    """
    if arg.startswith("some.dotted.path"):
        return MagicMock()
    return import_module(arg)


@pytest.mark.skip  # need remote registry  # many issues with fingerprints, depdendencies, p2p build
@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)  # flaky on Windows
@mock.patch(
    "aea.cli.registry.utils.get_or_create_cli_config",
    return_value=TEST_IPFS_REGISTRY_CONFIG,
)
@mock.patch(
    "aea.manager.manager.MultiAgentManager._project_install_and_build",
    return_value=REMOTE_HTTP,
)
@mock.patch("aea.cli.add.get_default_remote_registry", return_value=REMOTE_HTTP)
@mock.patch("aea.cli.add.is_fingerprint_correct", return_value=True)
@mock.patch(
    "aea.configurations.base.ComponentConfiguration.check_fingerprint",
    return_value=True,
)
class TestMultiAgentManager(BasePythonMarkdownDocs):
    """Test the ledger integration code snippets."""

    DOC_PATH = Path(ROOT_DIR, "docs", "multi-agent-manager.md")

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        super().setup_class()
        cls.old_cwd = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp()
        shutil.copytree(PACKAGES_DIR, Path(cls.temp_dir, "packages"))
        os.chdir(cls.temp_dir)

    @classmethod
    def teardown_class(cls):
        """Teardown class."""
        os.chdir(cls.old_cwd)
        shutil.rmtree(cls.temp_dir)
