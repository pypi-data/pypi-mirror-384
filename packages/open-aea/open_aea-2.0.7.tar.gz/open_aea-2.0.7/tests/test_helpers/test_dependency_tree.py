# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests for the helper module 'dependency_tree'."""

import re
import shutil
import subprocess  # nosec
import tempfile
from collections import OrderedDict
from pathlib import Path

import pytest

from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.exceptions import AEAPackageLoadingError
from aea.helpers.base import cd
from aea.helpers.dependency_tree import DependencyTree, dump_yaml, load_yaml

from tests.conftest import PACKAGES_DIR


def test_generation_of_dependency_tree_of_repo_packages() -> None:
    """Test we can generate the dependency tree of the package directory of the repository."""
    dependency_tree = DependencyTree.generate(Path(PACKAGES_DIR))
    assert len(dependency_tree) > 0


def test_generation_of_dependency_tree_of_project() -> None:
    """Test we can generate the dependency tree of the project directory."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        source_path = Path(PACKAGES_DIR)
        shutil.copytree(source_path, Path(tmp_dir) / source_path.parts[-1])
        with cd(tmp_dir):
            cmd = ["aea", "create", "dummy_project"]
            project_path = Path(tmp_dir) / "dummy_project"
            stdout, stderr = subprocess.Popen(cmd).communicate()  # nosec
            assert stdout is stderr is None
            dependency_tree = DependencyTree.generate(project_path, from_project=True)
            assert len(dependency_tree) > 0


def test_case_when_dependency_tree_has_a_self_loop() -> None:
    """Test we raise error when dependency tree has a node with a self-loop."""
    dummy_package_id = PackageId(
        PackageType.PROTOCOL, PublicId.from_str("author/pkg_name:0.1.0")
    )
    # self-loop: dummy_package -> dummy_package
    dependency_list = {dummy_package_id: [dummy_package_id]}
    with pytest.raises(
        AEAPackageLoadingError,
        match=re.escape(
            f"Found a self-loop dependency while resolving dependency tree in package {dummy_package_id}"
        ),
    ):
        DependencyTree.resolve_tree(dependency_list)


def test_case_when_dependency_tree_has_a_cycle() -> None:
    """Test we raise error when dependency tree has a cycle (length > 1)."""
    package_a_id = PackageId(
        PackageType.PROTOCOL, PublicId.from_str("author/pkg_a:0.1.0")
    )
    package_b_id = PackageId(
        PackageType.PROTOCOL, PublicId.from_str("author/pkg_b:0.1.0")
    )
    package_c_id = PackageId(
        PackageType.PROTOCOL, PublicId.from_str("author/pkg_c:0.1.0")
    )
    # cycle: package_a -> package_b -> package_c -> package_a
    dependency_list = {
        package_a_id: [package_b_id],
        package_b_id: [package_c_id],
        package_c_id: [package_a_id],
    }
    with pytest.raises(
        AEAPackageLoadingError,
        match=re.escape(
            f"Found a circular dependency while resolving dependency tree: {package_a_id} -> {package_b_id} -> {package_c_id} -> {package_a_id}"
        ),
    ):
        DependencyTree.resolve_tree(dependency_list)


@pytest.mark.parametrize("extra_data", [None, [{}] * 3])
def test_dump_yaml(extra_data) -> None:
    """Test dump yaml"""

    with tempfile.TemporaryDirectory() as tmp_dir:
        filepath = Path(tmp_dir) / "dump_dummy.yaml"
        data = dict.fromkeys(reversed(range(3)))
        dump_yaml(filepath, data, extra_data)
        reconstituted_data, reconstituted_extra_data = load_yaml(filepath)
        assert isinstance(reconstituted_data, OrderedDict)
        assert list(reconstituted_data.keys()) == list(range(3))
        assert all(map(lambda o: isinstance(o, OrderedDict), reconstituted_extra_data))
