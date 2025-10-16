# SPDX-License-Identifier: GPL-2.0-or-later
"""
Collection of tests for the update feature
"""

import os

from .udm_cmd import udm_cmd
from .playground import Playground
from .mocks.svn_with_deps import mock_svn_with_deps
from .mocks.git_with_deps import mock_git_with_deps


def test_update_svn():
    """
    Test that it can update an svn repository with udm deps already defined
    """
    with Playground() as playground:
        # Create svn repository with udm deps
        digests = playground.repos_create_from_mock(mock_svn_with_deps)
        playground.repos_local_clear()

        # Checkout svn repository
        main_local_path = playground.svn_checkout("repo_main", "trunk")

        # Run udm convert
        prev_path = os.getcwd()
        os.chdir(main_local_path)

        udm_cmd(
            [
                "update",
            ]
        )
        os.chdir(prev_path)

        # Verify svn status
        expected_status = {
            "libs": "added",
        }
        assert playground.svn_compare_status("repo_main", expected_status)

        # Verify generated deps file
        expected_deps = {
            "libs/lib1": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib1")}/trunk',
            },
            "libs/lib2": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib2")}/trunk',
            },
            "libs/lib3": {
                "url": f'file://{playground.repo_get_remote_path("repo_lib3")}/trunk',
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


def test_update_git():
    """
    Test that it can update a git repository with udm deps already defined
    """
    with Playground() as playground:
        # Create git repository with udm deps
        digests = playground.repos_create_from_mock(mock_git_with_deps)
        playground.repos_local_clear()

        # Checkout svn repository
        main_local_path = playground.git_clone("repo_main")

        # Run udm convert
        prev_path = os.getcwd()
        os.chdir(main_local_path)
        udm_cmd(
            [
                "update",
            ]
        )
        os.chdir(prev_path)

        # Verify git status
        expected_status = {
            ".gitignore": "added",
        }
        assert playground.git_compare_status("repo_main", expected_status)

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
