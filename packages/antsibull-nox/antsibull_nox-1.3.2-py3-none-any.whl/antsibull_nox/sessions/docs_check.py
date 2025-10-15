# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025, Ansible Project

"""
Create nox docs check session.
"""

from __future__ import annotations

import typing as t
from pathlib import Path

import nox

from ..cd import (
    get_changes,
)
from ..paths import (
    list_all_files,
)
from .collections import (
    CollectionSetup,
    prepare_collections,
)
from .utils.package_versions import (
    get_package_version,
    is_new_enough,
)
from .utils.packages import (
    PackageType,
    PackageTypeOrList,
    check_package_types,
    install,
    normalize_package_type,
)
from .utils.scripts import (
    run_bare_script,
)


def find_extra_docs_rst_files() -> list[Path]:
    """
    Find all RST extra document files.
    """
    all_files = list_all_files()
    cwd = Path.cwd()
    extra_docs_dir = cwd / "docs" / "docsite" / "rst"
    return [
        file
        for file in all_files
        if file.is_relative_to(extra_docs_dir) and file.name.lower().endswith((".rst"))
    ]


def file_of_interest(file: Path) -> bool:
    """
    Determine whether the file is relevant for the docs build.
    """
    if file.is_relative_to("docs/docsite"):
        return True
    if file in (Path("meta/runtime.yml"), Path("galaxy.yml")):
        return True
    if file.is_relative_to("plugins"):
        if file.is_relative_to("plugins/module_utils"):
            return False
        if file.is_relative_to("plugins/plugin_utils"):
            return False
        # Other Python and YAML plugin/ files often contain documentation.
        # Other files do not.
        return file.suffix in (".py", ".yml", ".yaml")
    if file.is_relative_to("roles"):
        # For roles, only files in <role>/meta/ are of interest for documentation.
        return file.match("roles/*/meta/*")
    # So far, no other files are of interest for documentation.
    return False


def add_docs_check(
    *,
    make_docs_check_default: bool = True,
    antsibull_docs_package: PackageTypeOrList = "antsibull-docs",
    ansible_core_package: PackageTypeOrList = "ansible-core",
    validate_collection_refs: t.Literal["self", "dependent", "all"] | None = None,
    extra_collections: list[str] | None = None,
    codeblocks_restrict_types: list[str] | None = None,
    codeblocks_restrict_type_exact_case: bool = True,
    codeblocks_allow_without_type: bool = True,
    codeblocks_allow_literal_blocks: bool = True,
    antsibull_docutils_package: PackageTypeOrList = "antsibull-docutils",
) -> None:
    """
    Add docs-check session for linting.
    """
    run_extra_checks = (
        codeblocks_restrict_types is not None
        or not codeblocks_allow_without_type
        or not codeblocks_allow_literal_blocks
    )

    def compose_dependencies(session: nox.Session) -> list[PackageType]:
        deps = []
        deps.extend(
            check_package_types(
                session,
                "sessions.docs_check.antsibull_docs_package",
                normalize_package_type(antsibull_docs_package),
            )
        )
        deps.extend(
            check_package_types(
                session,
                "sessions.docs_check.ansible_core_package",
                normalize_package_type(ansible_core_package),
            )
        )
        if run_extra_checks:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.docs_check.antsibull_docutils_package",
                    normalize_package_type(antsibull_docutils_package),
                )
            )
        return deps

    def execute_extra_checks(session: nox.Session) -> None:
        all_extra_docs = find_extra_docs_rst_files()
        if not all_extra_docs:
            session.warn(
                "Skipping codeblock checks since no appropriate RST file was found..."
            )
            return
        run_bare_script(
            session,
            "rst-extra",
            use_session_python=True,
            files=all_extra_docs,
            extra_data={
                "codeblocks_restrict_types": codeblocks_restrict_types,
                "codeblocks_restrict_type_exact_case": codeblocks_restrict_type_exact_case,
                "codeblocks_allow_without_type": codeblocks_allow_without_type,
                "codeblocks_allow_literal_blocks": codeblocks_allow_literal_blocks,
            },
            with_cd=True,
        )

    def execute_antsibull_docs(
        session: nox.Session, prepared_collections: CollectionSetup
    ) -> None:
        changes = get_changes()
        if changes is not None:
            if not any(file_of_interest(file) for file in changes):
                session.warn(
                    "Skip antsibull-docs lint-collection-docs (no files to process)"
                )
                return
        antsibull_docs_version = get_package_version(session, "antsibull-docs")
        if antsibull_docs_version is not None:
            session.log(f"Detected antsibull-docs version {antsibull_docs_version}")
        with session.chdir(prepared_collections.current_path):
            collections_path = f"{prepared_collections.current_place}"
            command = [
                "antsibull-docs",
                "lint-collection-docs",
                "--plugin-docs",
                "--skip-rstcheck",
                ".",
            ]
            if validate_collection_refs:
                command.extend(["--validate-collection-refs", validate_collection_refs])
            if is_new_enough(antsibull_docs_version, min_version="2.18.0"):
                command.append("--check-extra-docs-refs")
            session.run(*command, env={"ANSIBLE_COLLECTIONS_PATH": collections_path})

    def docs_check(session: nox.Session) -> None:
        install(session, *compose_dependencies(session))
        prepared_collections = prepare_collections(
            session,
            install_in_site_packages=False,
            extra_collections=extra_collections,
            install_out_of_tree=True,
        )
        if run_extra_checks:
            execute_extra_checks(session)
        if not prepared_collections:
            session.warn("Skipping antsibull-docs...")
        if prepared_collections:
            execute_antsibull_docs(session, prepared_collections)

    docs_check.__doc__ = "Run 'antsibull-docs lint-collection-docs'"
    nox.session(
        name="docs-check",
        default=make_docs_check_default,
    )(docs_check)


__all__ = [
    "add_docs_check",
]
