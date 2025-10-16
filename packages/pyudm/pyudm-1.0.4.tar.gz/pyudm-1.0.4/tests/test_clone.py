# SPDX-License-Identifier: GPL-2.0-or-later
"""
Collection of tests for the clone feature
"""
from udm.dependency import DEFAULT_DEPS_FILE
from .udm_cmd import udm_cmd
from .playground import Playground
from .mocks.svn_simple import mock_svn_simple
from .mocks.git_simple import mock_git_simple
from .mocks.svn_with_externals import mock_svn_with_externals
from .mocks.git_with_submodules import mock_git_with_submodules
from .mocks.svn_with_deps import mock_svn_with_deps
from .mocks.git_with_deps import mock_git_with_deps
from .mocks.svn_with_deps_nested import mock_svn_with_deps_nested
from .mocks.git_with_deps_nested import mock_git_with_deps_nested


def test_clone_svn():
    """
    Test that it can clone an svn repository
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_svn_simple)
        playground.repos_local_clear()

        udm_cmd(
            [
                "clone",
                playground.svn_get_remote_url("repo_main"),
                playground.repo_get_local_path("repo_main"),
            ]
        )

        assert (
            playground.repo_ftree_get_digest("repo_main", "newfile.txt")
            == digests["repo_main"]["trunk/newfile.txt"]
        )


def test_clone_git():
    """
    Test that it can clone a git repository
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_git_simple)
        playground.repos_local_clear()

        udm_cmd(
            [
                "clone",
                playground.repo_get_remote_path("repo_main"),
                playground.repo_get_local_path("repo_main"),
            ]
        )

        assert (
            playground.repo_ftree_get_digest("repo_main", "newfile.txt")
            == digests["repo_main"]["newfile.txt"]
        )


def test_clone_svn_with_convert():
    """
    Test that it can clone a svn repository with externals and convert it with deps
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_svn_with_externals)
        playground.repos_local_clear()
        main_local_path = playground.repo_get_local_path("repo_main")
        udm_cmd(
            [
                "clone",
                "--convert",
                playground.svn_get_remote_url("repo_main"),
                main_local_path,
            ]
        )
        expected_status = {
            ".": "modified",
            str(DEFAULT_DEPS_FILE): "added",
            "libs": "added",
        }
        assert playground.svn_compare_status("repo_main", expected_status)

        expected_deps = {
            "libs/lib1": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib1")}',
            },
            "libs/lib2": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib2")}',
            },
            "libs/lib3": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib3")}',
            },
        }
        assert playground.repo_compare_deps("repo_main", expected_deps)

        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib1/lib1.h")
            == digests["repo_lib1"]["trunk/lib1.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib2/lib2.h")
            == digests["repo_lib2"]["trunk/lib2.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib3/lib3.h")
            == digests["repo_lib3"]["trunk/lib3.h"]
        )


def test_clone_git_with_convert():
    """
    Test that it can clone a git repository with submodules and convert it with deps
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_git_with_submodules)
        playground.repos_local_clear()
        udm_cmd(
            [
                "clone",
                "--convert",
                playground.repo_get_remote_path("repo_main"),
                playground.repo_get_local_path("repo_main"),
            ]
        )
        expected_status = {
            str(DEFAULT_DEPS_FILE): "added",
            ".gitignore": "added",
            ".gitmodules": "deleted",
            "libs/lib1": "deleted",
            "libs/lib2": "deleted",
            "libs/lib3": "deleted",
        }
        assert playground.git_compare_status("repo_main", expected_status)

        # Verify deps file
        expected_deps = {
            "libs/lib1": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib1")}',
                "commit": playground.git_get_last_remote_commit("repo_lib1"),
            },
            "libs/lib2": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib2")}',
                "commit": playground.git_get_last_remote_commit("repo_lib2"),
            },
            "libs/lib3": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib3")}',
                "commit": playground.git_get_last_remote_commit("repo_lib3"),
            },
        }
        assert playground.repo_compare_deps("repo_main", expected_deps)

        # Verify generated .gitignore file
        expected_gitignore = "\n".join(
            [
                "### automatic handled block START, do not edit following lines",
                "libs/lib1",
                "libs/lib2",
                "libs/lib3",
                "### automatic handled block END, do not edit previous lines",
            ]
        )
        assert playground.repo_compare_file_content(
            "repo_main", ".gitignore", expected_gitignore
        )

        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib1/lib1.h")
            == digests["repo_lib1"]["lib1.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib2/lib2.h")
            == digests["repo_lib2"]["lib2.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib3/lib3.h")
            == digests["repo_lib3"]["lib3.h"]
        )


def test_clone_svn_with_deps():
    """
    Test that it can clone an svn repository with udm deps
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_svn_with_deps)
        playground.repos_local_clear()

        udm_cmd(
            [
                "clone",
                playground.svn_get_remote_url("repo_main"),
                playground.repo_get_local_path("repo_main"),
            ]
        )

        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib1/lib1.h")
            == digests["repo_lib1"]["trunk/lib1.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib2/lib2.h")
            == digests["repo_lib2"]["trunk/lib2.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib3/lib3.h")
            == digests["repo_lib3"]["trunk/lib3.h"]
        )


def test_clone_git_with_deps():
    """
    Test that it can clone a git repository with udm deps
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_git_with_deps)
        playground.repos_local_clear()

        udm_cmd(
            [
                "clone",
                playground.svn_get_remote_url("repo_main"),
                playground.repo_get_local_path("repo_main"),
            ]
        )

        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib1/lib1.h")
            == digests["repo_lib1"]["lib1.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib2/lib2.h")
            == digests["repo_lib2"]["lib2.h"]
        )
        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib3/lib3.h")
            == digests["repo_lib3"]["lib3.h"]
        )


def test_clone_svn_with_deps_nested():
    """
    Test that it can clone an svn repository with nested udm deps
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_svn_with_deps_nested)
        playground.repos_local_clear()

        udm_cmd(
            [
                "clone",
                playground.svn_get_remote_url("repo_main"),
                playground.repo_get_local_path("repo_main"),
            ]
        )

        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib1/lib1.h")
            == digests["repo_lib1"]["trunk/lib1.h"]
        )
        assert (
            playground.repo_ftree_get_digest(
                "repo_main", "libs/lib1/libs/lib1_1/lib1_1.h"
            )
            == digests["repo_lib1_1"]["trunk/lib1_1.h"]
        )
        assert (
            playground.repo_ftree_get_digest(
                "repo_main", "libs/lib1/libs/lib1_2/lib1_2.h"
            )
            == digests["repo_lib1_2"]["trunk/lib1_2.h"]
        )
        assert (
            playground.repo_ftree_get_digest(
                "repo_main", "libs/lib1/libs/lib1_3/lib1_3.h"
            )
            == digests["repo_lib1_3"]["trunk/lib1_3.h"]
        )


def test_clone_git_with_deps_nested():
    """
    Test that it can clone a git repository with nested udm deps
    """
    with Playground() as playground:
        digests = playground.repos_create_from_mock(mock_git_with_deps_nested)
        playground.repos_local_clear()

        udm_cmd(
            [
                "clone",
                playground.repo_get_remote_path("repo_main"),
                playground.repo_get_local_path("repo_main"),
            ]
        )

        assert (
            playground.repo_ftree_get_digest("repo_main", "libs/lib1/lib1.h")
            == digests["repo_lib1"]["lib1.h"]
        )
        assert (
            playground.repo_ftree_get_digest(
                "repo_main", "libs/lib1/libs/lib1_1/lib1_1.h"
            )
            == digests["repo_lib1_1"]["lib1_1.h"]
        )
        assert (
            playground.repo_ftree_get_digest(
                "repo_main", "libs/lib1/libs/lib1_2/lib1_2.h"
            )
            == digests["repo_lib1_2"]["lib1_2.h"]
        )
        assert (
            playground.repo_ftree_get_digest(
                "repo_main", "libs/lib1/libs/lib1_3/lib1_3.h"
            )
            == digests["repo_lib1_3"]["lib1_3.h"]
        )
