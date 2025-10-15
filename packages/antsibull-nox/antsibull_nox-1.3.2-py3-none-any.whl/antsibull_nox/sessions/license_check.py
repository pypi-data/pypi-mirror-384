# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025, Ansible Project

"""
Create nox license check session.
"""

from __future__ import annotations

import nox

from .utils import (
    compose_description,
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


def add_license_check(
    *,
    make_license_check_default: bool = True,
    run_reuse: bool = True,
    reuse_package: PackageTypeOrList = "reuse",
    run_license_check: bool = True,
    license_check_extra_ignore_paths: list[str] | None = None,
) -> None:
    """
    Add license-check session for license checks.
    """

    def compose_dependencies(session: nox.Session) -> list[PackageType]:
        deps = []
        if run_reuse:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.license_check.reuse_package",
                    normalize_package_type(reuse_package),
                )
            )
        return deps

    def license_check(session: nox.Session) -> None:
        install(session, *compose_dependencies(session))
        if run_reuse:
            session.run("reuse", "lint")
        if run_license_check:
            run_bare_script(
                session,
                "license-check",
                extra_data={
                    "extra_ignore_paths": license_check_extra_ignore_paths or [],
                },
                with_cd=True,
            )

    license_check.__doc__ = compose_description(
        prefix={
            "one": "Run license checker:",
            "other": "Run license checkers:",
        },
        programs={
            "reuse": run_reuse,
            "license-check": (
                "ensure GPLv3+ for plugins" if run_license_check else False
            ),
        },
    )
    nox.session(
        name="license-check",
        default=make_license_check_default,
    )(license_check)


__all__ = [
    "add_license_check",
]
