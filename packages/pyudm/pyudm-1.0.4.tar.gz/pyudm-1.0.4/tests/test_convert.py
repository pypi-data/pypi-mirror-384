# SPDX-License-Identifier: GPL-2.0-or-later
"""
Collection of tests for the convert feature
"""

import os

from udm.dependency import DEFAULT_DEPS_FILE
from .udm_cmd import udm_cmd
from .playground import Playground
from .mocks.svn_with_externals import mock_svn_with_externals
from .mocks.git_with_submodules import mock_git_with_submodules


def test_covert_svn():
    """
    Test that it can convert an svn repository with externals
    """
    with Playground() as playground:
        # Create svn repository with externals
        playground.repos_create_from_mock(mock_svn_with_externals)
        playground.repos_local_clear()

        # Checkout svn repository
        main_local_path = playground.svn_checkout("repo_main", "trunk")

        # Run udm convert
        prev_path = os.getcwd()
        os.chdir(main_local_path)
        udm_cmd(
            [
                "convert",
            ]
        )
        os.chdir(prev_path)

        # Verify svn status
        expected_status = {
            ".": "modified",
            str(DEFAULT_DEPS_FILE): "added",
            "libs": "added",
        }
        assert playground.svn_compare_status("repo_main", expected_status)

        # Verify generated deps file
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


def test_covert_svn_noupdate():
    """
    Test that it can convert an svn repository with externals
    """
    with Playground() as playground:
        # Create svn repository with externals
        playground.repos_create_from_mock(mock_svn_with_externals)
        playground.repos_local_clear()

        # Checkout svn repository
        main_local_path = playground.svn_checkout("repo_main", "trunk")

        # Run udm convert
        prev_path = os.getcwd()
        os.chdir(main_local_path)
        udm_cmd(["convert", "--no-update"])
        os.chdir(prev_path)

        # Verify svn status
        expected_status = {
            ".": "modified",
            str(DEFAULT_DEPS_FILE): "added",
        }
        assert playground.svn_compare_status("repo_main", expected_status)

        # Verify generated deps file
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


def test_covert_git():
    """
    Test that it can convert a git repository with submodules
    """
    with Playground() as playground:
        # Create git repository with submodules
        playground.repos_create_from_mock(mock_git_with_submodules)
        playground.repos_local_clear()

        # Clone git repository
        main_local_path = playground.git_clone("repo_main")

        # Run udm convert
        prev_path = os.getcwd()
        os.chdir(main_local_path)
        udm_cmd(
            [
                "convert",
            ]
        )
        os.chdir(prev_path)

        # Verify git status
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


def test_covert_git_noupdate():
    """
    Test that it can convert a git repository with submodules without updating
    """
    with Playground() as playground:
        # Create git repository with submodules
        playground.repos_create_from_mock(mock_git_with_submodules)
        playground.repos_local_clear()

        # Clone git repository
        main_local_path = playground.git_clone("repo_main")

        # Run udm convert
        prev_path = os.getcwd()
        os.chdir(main_local_path)
        udm_cmd(["convert", "--no-update"])
        os.chdir(prev_path)

        # Verify git status
        expected_status = {
            str(DEFAULT_DEPS_FILE): "added",
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
