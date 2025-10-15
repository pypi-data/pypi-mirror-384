# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025, Ansible Project

"""
Create nox lint sessions.
"""

from __future__ import annotations

import json
import os
import shlex
from pathlib import Path

import nox

from ..collection import (
    load_collection_data_from_disk,
)
from ..paths import (
    list_all_files,
)
from .collections import (
    CollectionSetup,
    prepare_collections,
)
from .docs_check import find_extra_docs_rst_files
from .utils import (
    IN_CI,
    compose_description,
    silence_run_verbosity,
)
from .utils.packages import (
    PackageType,
    PackageTypeOrList,
    check_package_types,
    install,
    normalize_package_type,
)
from .utils.paths import (
    filter_files_cd,
    filter_paths,
)
from .utils.scripts import (
    run_bare_script,
)

CODE_FILES = [
    "plugins",
    "tests/unit",
]

MODULE_PATHS = [
    "plugins/modules/",
    "plugins/module_utils/",
    "tests/unit/plugins/modules/",
    "tests/unit/plugins/module_utils/",
]


def _split_arg(
    session: nox.Session, arg: str | PackageType, arg_name: str, index: int
) -> list[str | PackageType]:
    if not isinstance(arg, str):
        return check_package_types(session, arg_name, [arg])
    args = shlex.split(arg)
    # How to resolve the deprecations:
    #   1. Eventually, make the following warnings errors (in 2.0.0 likely);
    #   2. Eventually, parse str as PackageName as for other
    #      package list arguments (do this in config.py) (in 2.x.0 likely).
    if args != [arg]:
        session.warn(
            f"DEPRECATION WARNING: {arg_name}[{index + 1}] is currently shell-split."
            " This behavior is deprecated and will change in a future release."
            " Specify the dependency as a dictionary with 'type' to avoid ambiguity;"
            " see PackageType in the config file documentation for details."
        )
    for part in args:
        if part.startswith("-"):
            session.warn(
                f"DEPRECATION WARNING: {arg_name}[{index + 1}] contains an argument"
                f" {part!r} starting with a dash."
                " This behavior is deprecated and will stop working in a future release."
                " Specify this dependency as a package type dictionary;"
                " see PackageType in the config file documentation for details."
            )
    return args  # type: ignore


def add_lint(
    *,
    make_lint_default: bool,
    has_formatters: bool,
    has_codeqa: bool,
    has_yamllint: bool,
    has_typing: bool,
    has_config_lint: bool,
) -> None:
    """
    Add nox meta session for linting.
    """

    def lint(session: nox.Session) -> None:  # pylint: disable=unused-argument
        pass  # this session is deliberately empty

    dependent_sessions = []
    if has_formatters:
        dependent_sessions.append("formatters")
    if has_codeqa:
        dependent_sessions.append("codeqa")
    if has_yamllint:
        dependent_sessions.append("yamllint")
    if has_typing:
        dependent_sessions.append("typing")
    if has_config_lint:
        dependent_sessions.append("antsibull-nox-config")

    lint.__doc__ = compose_description(
        prefix={
            "one": "Meta session for triggering the following session:",
            "other": "Meta session for triggering the following sessions:",
        },
        programs={
            "formatters": has_formatters,
            "codeqa": has_codeqa,
            "yamllint": has_yamllint,
            "typing": has_typing,
            "antsibull-nox-config": has_config_lint,
        },
    )
    nox.session(
        name="lint",
        default=make_lint_default,
        requires=dependent_sessions,
    )(lint)


def _execute_isort(
    session: nox.Session,
    *,
    root_dir: Path,
    collection_dir: Path,
    run_check: bool,
    extra_code_files: list[str],
    isort_config: str | os.PathLike | None,
) -> None:
    command: list[str] = [
        "isort",
        "--src",
        ".",
    ]
    if run_check:
        command.append("--check")
    if isort_config is not None:
        command.extend(
            [
                "--settings-file",
                str(Path(isort_config).resolve().relative_to(root_dir, walk_up=True)),
            ]
        )
    command.extend(session.posargs)
    files = filter_paths(CODE_FILES + ["noxfile.py"] + extra_code_files, with_cd=True)
    if not files:
        session.warn("Skipping isort (no files to process)")
        return

    relative_dir = collection_dir.relative_to(root_dir)
    with session.chdir(root_dir):
        for file in files:
            command.append(str(relative_dir / file))
        session.run(*command)


def _execute_black_for(
    session: nox.Session,
    *,
    paths: list[str],
    run_check: bool,
    black_config: str | os.PathLike | None,
    what_for: str = "",
) -> None:
    if not paths:
        session.warn(f"Skipping black{what_for} (no files to process)")
        return
    command = ["black"]
    if run_check:
        command.append("--check")
    if black_config is not None:
        command.extend(["--config", str(black_config)])
    command.extend(session.posargs)
    command.extend(paths)
    session.run(*command)


def _execute_black(
    session: nox.Session,
    *,
    run_check: bool,
    extra_code_files: list[str],
    run_black: bool,
    run_black_modules: bool | None,
    black_config: str | os.PathLike | None,
) -> None:
    if run_black and run_black_modules:
        _execute_black_for(
            session,
            paths=filter_paths(
                CODE_FILES + ["noxfile.py"] + extra_code_files, with_cd=True
            ),
            run_check=run_check,
            black_config=black_config,
        )
        return
    if run_black:
        paths = (
            filter_paths(
                CODE_FILES,
                remove=MODULE_PATHS,
                extensions=[".py"],
                with_cd=True,
            )
            + ["noxfile.py"]
            + extra_code_files
        )
        _execute_black_for(
            session,
            paths=paths,
            run_check=run_check,
            black_config=black_config,
            what_for=" for other plugins",
        )
    if run_black_modules:
        paths = filter_paths(
            CODE_FILES,
            restrict=MODULE_PATHS,
            extensions=[".py"],
            with_cd=True,
        )
        _execute_black_for(
            session,
            paths=paths,
            run_check=run_check,
            black_config=black_config,
            what_for=" for modules and module utils",
        )


def _execute_ruff_format(
    session: nox.Session,
    *,
    run_check: bool,
    extra_code_files: list[str],
    ruff_format_config: str | os.PathLike | None,
) -> None:
    command: list[str] = [
        "ruff",
        "format",
    ]
    if run_check:
        command.append("--check")
    if ruff_format_config is not None:
        command.extend(["--config", str(ruff_format_config)])
    command.extend(session.posargs)
    files = filter_paths(CODE_FILES + ["noxfile.py"] + extra_code_files, with_cd=True)
    if not files:
        session.warn("Skipping ruff format (no files to process)")
        return
    command.extend(files)
    session.run(*command)


def _execute_ruff_autofix(
    session: nox.Session,
    *,
    run_check: bool,
    extra_code_files: list[str],
    ruff_autofix_config: str | os.PathLike | None,
    ruff_autofix_select: list[str],
) -> None:
    command: list[str] = [
        "ruff",
        "check",
    ]
    if not run_check:
        command.append("--fix")
    if ruff_autofix_config is not None:
        command.extend(["--config", str(ruff_autofix_config)])
    if ruff_autofix_select:
        command.extend(["--select", ",".join(ruff_autofix_select)])
    command.extend(session.posargs)
    files = filter_paths(CODE_FILES + ["noxfile.py"] + extra_code_files, with_cd=True)
    if not files:
        session.warn("Skipping ruff autofix (no files to process)")
        return
    command.extend(files)
    session.run(*command)


def add_formatters(
    *,
    extra_code_files: list[str],
    # isort:
    run_isort: bool,
    isort_config: str | os.PathLike | None,
    isort_package: PackageTypeOrList,
    # black:
    run_black: bool,
    run_black_modules: bool | None,
    black_config: str | os.PathLike | None,
    black_package: PackageTypeOrList,
    # ruff format:
    run_ruff_format: bool,
    ruff_format_config: str | os.PathLike | None,
    ruff_format_package: PackageTypeOrList,
    # ruff autofix:
    run_ruff_autofix: bool,
    ruff_autofix_config: str | os.PathLike | None,
    ruff_autofix_package: PackageTypeOrList,
    ruff_autofix_select: list[str],
) -> None:
    """
    Add nox session for formatters.
    """
    if run_black_modules is None:
        run_black_modules = run_black
    run_check = IN_CI

    def compose_dependencies(session: nox.Session) -> list[PackageType]:
        deps = []
        if run_isort:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.isort_package",
                    normalize_package_type(isort_package),
                )
            )
        if run_black or run_black_modules:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.black_package",
                    normalize_package_type(black_package),
                )
            )
        if (
            run_ruff_format
            and run_ruff_autofix
            and ruff_format_package == ruff_autofix_package
        ):
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.ruff_format_package",
                    normalize_package_type(ruff_format_package),
                )
            )
        else:
            if run_ruff_format:
                deps.extend(
                    check_package_types(
                        session,
                        "sessions.lint.ruff_format_package",
                        normalize_package_type(ruff_format_package),
                    )
                )
            if run_ruff_autofix:
                deps.extend(
                    check_package_types(
                        session,
                        "sessions.lint.ruff_autofix_package",
                        normalize_package_type(ruff_autofix_package),
                    )
                )
        return deps

    def formatters(session: nox.Session) -> None:
        install(session, *compose_dependencies(session))
        if run_isort:
            cwd = Path.cwd()
            cd = load_collection_data_from_disk(cwd)
            root_dir = Path(session.create_tmp()).resolve() / "collection-root"
            namespace_dir = root_dir / "ansible_collections" / cd.namespace
            namespace_dir.mkdir(parents=True, exist_ok=True)
            collection_path = namespace_dir / cd.name
            if not collection_path.exists():
                collection_path.symlink_to(
                    cwd.relative_to(namespace_dir, walk_up=True),
                    target_is_directory=True,
                )
            _execute_isort(
                session,
                root_dir=root_dir,
                collection_dir=collection_path,
                run_check=run_check,
                extra_code_files=extra_code_files,
                isort_config=isort_config,
            )
        if run_black or run_black_modules:
            _execute_black(
                session,
                run_check=run_check,
                extra_code_files=extra_code_files,
                run_black=run_black,
                run_black_modules=run_black_modules,
                black_config=black_config,
            )
        if run_ruff_format:
            _execute_ruff_format(
                session,
                run_check=run_check,
                extra_code_files=extra_code_files,
                ruff_format_config=ruff_format_config,
            )
        if run_ruff_autofix:
            _execute_ruff_autofix(
                session,
                run_check=run_check,
                extra_code_files=extra_code_files,
                ruff_autofix_config=ruff_autofix_config,
                ruff_autofix_select=ruff_autofix_select,
            )

    formatters.__doc__ = compose_description(
        prefix={
            "one": "Run code formatter:",
            "other": "Run code formatters:",
        },
        programs={
            "isort": run_isort,
            "black": run_black,
            "ruff format": run_ruff_format,
            "ruff check --fix": run_ruff_autofix,
        },
    )
    nox.session(name="formatters", default=False)(formatters)


def process_pylint_errors(
    session: nox.Session,
    prepared_collections: CollectionSetup,
    output: str,
) -> None:
    """
    Process errors reported by pylint in 'json2' format.
    """
    data = json.loads(output)
    found_error = False
    if data["messages"]:
        for message in data["messages"]:
            path = os.path.relpath(
                message["absolutePath"], prepared_collections.current_path
            )
            prefix = f"{path}:{message['line']}:{message['column']}: [{message['messageId']}]"
            print(f"{prefix} {message['message']} [{message['symbol']}]")
            found_error = True
    if found_error:
        session.error("Pylint failed")


def add_codeqa(  # noqa: C901
    *,
    extra_code_files: list[str],
    # ruff check:
    run_ruff_check: bool,
    ruff_check_config: str | os.PathLike | None,
    ruff_check_package: PackageTypeOrList,
    # flake8:
    run_flake8: bool,
    flake8_config: str | os.PathLike | None,
    flake8_package: PackageTypeOrList,
    # pylint:
    run_pylint: bool,
    pylint_rcfile: str | os.PathLike | None,
    pylint_modules_rcfile: str | os.PathLike | None,
    pylint_package: PackageTypeOrList,
    pylint_ansible_core_package: PackageTypeOrList | None,
    pylint_extra_deps: list[str | PackageType],
) -> None:
    """
    Add nox session for codeqa.
    """

    def compose_dependencies(session: nox.Session) -> list[PackageType]:
        deps = []
        if run_ruff_check:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.ruff_check_package",
                    normalize_package_type(ruff_check_package),
                )
            )
        if run_flake8:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.flake8_package",
                    normalize_package_type(flake8_package),
                )
            )
        if run_pylint:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.pylint_package",
                    normalize_package_type(pylint_package),
                )
            )
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.pylint_ansible_core_package",
                    normalize_package_type(pylint_ansible_core_package),
                )
            )
            if os.path.isdir("tests/unit"):
                deps.append("pytest")
                if os.path.isfile("tests/unit/requirements.txt"):
                    deps.extend(["-r", "tests/unit/requirements.txt"])
            for idx, extra_dep in enumerate(pylint_extra_deps):
                deps.extend(
                    _split_arg(
                        session, extra_dep, "sessions.lint.pylint_extra_deps", idx
                    )
                )
        return deps

    def execute_ruff_check(session: nox.Session) -> None:
        command: list[str] = [
            "ruff",
            "check",
        ]
        if ruff_check_config is not None:
            command.extend(["--config", str(ruff_check_config)])
        command.extend(session.posargs)
        files = filter_paths(
            CODE_FILES + ["noxfile.py"] + extra_code_files, with_cd=True
        )
        if not files:
            session.warn("Skipping ruff check (no files to process)")
            return
        command.extend(files)
        session.run(*command)

    def execute_flake8(session: nox.Session) -> None:
        command: list[str] = [
            "flake8",
        ]
        if flake8_config is not None:
            command.extend(["--config", str(flake8_config)])
        command.extend(session.posargs)
        files = filter_paths(
            CODE_FILES + ["noxfile.py"] + extra_code_files, with_cd=True
        )
        if not files:
            session.warn("Skipping flake8 (no files to process)")
            return
        command.extend(files)
        session.run(*command)

    def execute_pylint_impl(
        session: nox.Session,
        prepared_collections: CollectionSetup,
        config: os.PathLike | str | None,
        paths: list[str],
    ) -> None:
        command = ["pylint"]
        if config is not None:
            command.extend(
                [
                    "--rcfile",
                    os.path.join(prepared_collections.current_collection.path, config),
                ]
            )
        command.extend(["--source-roots", "."])
        command.extend(["--output-format", "json2"])
        command.extend(session.posargs)
        command.extend(prepared_collections.prefix_current_paths(paths))
        with silence_run_verbosity():
            # Exit code is OR of some of 1, 2, 4, 8, 16
            output = session.run(
                *command, silent=True, success_codes=list(range(0, 32))
            )

        if output:
            process_pylint_errors(session, prepared_collections, output)

    def execute_pylint(
        session: nox.Session, prepared_collections: CollectionSetup
    ) -> None:
        if pylint_modules_rcfile is not None and pylint_modules_rcfile != pylint_rcfile:
            # Only run pylint twice when using different configurations
            module_paths = filter_paths(
                CODE_FILES, restrict=MODULE_PATHS, extensions=[".py"], with_cd=True
            )
            other_paths = filter_paths(
                CODE_FILES, remove=MODULE_PATHS, extensions=[".py"], with_cd=True
            )
            if not module_paths:
                session.warn("Skipping pylint for modules (no files to process)")
            if not other_paths:
                session.warn("Skipping pylint for other files (no files to process)")
            if not module_paths and not other_paths:
                return
        else:
            # Otherwise run it only once using the general configuration
            module_paths = []
            other_paths = filter_paths(CODE_FILES, with_cd=True)
            if not other_paths:
                session.warn("Skipping pylint (no files to process)")
                return

        with session.chdir(prepared_collections.current_place):
            if module_paths:
                execute_pylint_impl(
                    session,
                    prepared_collections,
                    pylint_modules_rcfile or pylint_rcfile,
                    module_paths,
                )

            if other_paths:
                execute_pylint_impl(
                    session, prepared_collections, pylint_rcfile, other_paths
                )

    def codeqa(session: nox.Session) -> None:
        install(session, *compose_dependencies(session))
        prepared_collections: CollectionSetup | None = None
        if run_pylint:
            prepared_collections = prepare_collections(
                session,
                install_in_site_packages=False,
                extra_deps_files=["tests/unit/requirements.yml"],
            )
            if not prepared_collections:
                session.warn("Skipping pylint...")
        if run_ruff_check:
            execute_ruff_check(session)
        if run_flake8:
            execute_flake8(session)
        if run_pylint and prepared_collections:
            execute_pylint(session, prepared_collections)

    codeqa.__doc__ = compose_description(
        prefix={
            "other": "Run code QA:",
        },
        programs={
            "ruff check": run_ruff_check,
            "flake8": run_flake8,
            "pylint": run_pylint,
        },
    )
    nox.session(name="codeqa", default=False)(codeqa)


def add_yamllint(
    *,
    run_yamllint: bool,
    yamllint_config: str | os.PathLike | None,
    yamllint_config_plugins: str | os.PathLike | None,
    yamllint_config_plugins_examples: str | os.PathLike | None,
    yamllint_config_extra_docs: str | os.PathLike | None,
    yamllint_package: PackageTypeOrList,
    yamllint_antsibull_docutils_package: PackageTypeOrList,
) -> None:
    """
    Add yamllint session for linting YAML files and plugin/module docs.
    """

    def compose_dependencies(session: nox.Session) -> list[PackageType]:
        deps = []
        if run_yamllint:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.yamllint_package",
                    normalize_package_type(yamllint_package),
                )
            )
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.yamllint_antsibull_docutils_package",
                    normalize_package_type(yamllint_antsibull_docutils_package),
                )
            )
        return deps

    def to_str(config: str | os.PathLike | None) -> str | None:
        return str(config) if config else None

    def execute_yamllint(session: nox.Session) -> None:
        all_files = list_all_files()
        all_yaml_filenames = filter_files_cd(
            [
                file
                for file in all_files
                if file.name.lower().endswith((".yml", ".yaml"))
            ],
        )
        if not all_yaml_filenames:
            session.warn("Skipping yamllint (no files to process)")
            return

        run_bare_script(
            session,
            "file-yamllint",
            use_session_python=True,
            files=all_yaml_filenames,
            extra_data={
                "config": to_str(yamllint_config),
            },
        )

    def execute_plugin_yamllint(session: nox.Session) -> None:
        all_files = list_all_files()
        cwd = Path.cwd()
        plugins_dir = cwd / "plugins"
        ignore_dirs = [
            plugins_dir / "action",
            plugins_dir / "module_utils",
            plugins_dir / "plugin_utils",
        ]
        all_plugin_files = filter_files_cd(
            [
                file
                for file in all_files
                if file.is_relative_to(plugins_dir)
                and file.name.lower().endswith((".py", ".yml", ".yaml"))
                and not any(file.is_relative_to(dir) for dir in ignore_dirs)
            ],
        )
        if not all_plugin_files:
            session.warn("Skipping yamllint for modules/plugins (no files to process)")
            return
        run_bare_script(
            session,
            "plugin-yamllint",
            use_session_python=True,
            files=all_plugin_files,
            extra_data={
                "config": to_str(yamllint_config_plugins or yamllint_config),
                "config_examples": to_str(
                    yamllint_config_plugins_examples
                    or yamllint_config_plugins
                    or yamllint_config
                ),
            },
        )

    def execute_extra_docs_yamllint(session: nox.Session) -> None:
        all_extra_docs = filter_files_cd(find_extra_docs_rst_files())
        if not all_extra_docs:
            session.warn("Skipping yamllint for extra docs (no files to process)")
            return
        run_bare_script(
            session,
            "rst-yamllint",
            use_session_python=True,
            files=all_extra_docs,
            extra_data={
                "config": to_str(
                    yamllint_config_extra_docs
                    or yamllint_config_plugins_examples
                    or yamllint_config_plugins
                    or yamllint_config
                ),
            },
        )

    def yamllint(session: nox.Session) -> None:
        install(session, *compose_dependencies(session))
        if run_yamllint:
            execute_yamllint(session)
            execute_plugin_yamllint(session)
            execute_extra_docs_yamllint(session)

    yamllint.__doc__ = compose_description(
        prefix={
            "one": "Run YAML checker:",
            "other": "Run YAML checkers:",
        },
        programs={
            "yamllint": run_yamllint,
        },
    )
    nox.session(name="yamllint", default=False)(yamllint)


def process_mypy_errors(
    session: nox.Session,
    prepared_collections: CollectionSetup,
    output: str,
) -> None:
    """
    Process errors reported by mypy in 'json' format.
    """
    found_error = False
    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            path = os.path.relpath(
                prepared_collections.current_place / data["file"],
                prepared_collections.current_path,
            )
            prefix = f"{path}:{data['line']}:{data['column']}: [{data['severity']}]"
            if data["code"]:
                print(f"{prefix} {data['message']} [{data['code']}]")
            else:
                print(f"{prefix} {data['message']}")
            if data["hint"]:
                prefix = " " * len(prefix)
                for hint in data["hint"].splitlines():
                    print(f"{prefix} {hint}")
        except Exception:  # pylint: disable=broad-exception-caught
            session.warn(f"Cannot parse mypy output: {line}")
        found_error = True
    if found_error:
        session.error("Type checking failed")


def add_typing(
    *,
    extra_code_files: list[str],
    run_mypy: bool,
    mypy_config: str | os.PathLike | None,
    mypy_package: PackageTypeOrList,
    mypy_ansible_core_package: PackageTypeOrList | None,
    mypy_extra_deps: list[str | PackageType],
) -> None:
    """
    Add nox session for typing.
    """

    def compose_dependencies(session: nox.Session) -> list[PackageType]:
        deps = []
        if run_mypy:
            deps.extend(
                check_package_types(
                    session,
                    "sessions.lint.mypy_package",
                    normalize_package_type(mypy_package),
                )
            )
            if mypy_ansible_core_package is not None:
                deps.extend(
                    check_package_types(
                        session,
                        "sessions.lint.mypy_ansible_core_package",
                        normalize_package_type(mypy_ansible_core_package),
                    )
                )
            if os.path.isdir("tests/unit"):
                deps.append("pytest")
                if os.path.isfile("tests/unit/requirements.txt"):
                    deps.extend(["-r", "tests/unit/requirements.txt"])
            for idx, extra_dep in enumerate(mypy_extra_deps):
                deps.extend(
                    _split_arg(session, extra_dep, "sessions.lint.mypy_extra_deps", idx)
                )
        return deps

    def execute_mypy(
        session: nox.Session, prepared_collections: CollectionSetup
    ) -> None:
        # Run mypy
        files = filter_paths(CODE_FILES + extra_code_files, with_cd=True)
        with session.chdir(prepared_collections.current_place):
            files = prepared_collections.prefix_current_paths(files)
            if not files:
                session.warn("Skipping mypy (no files to process)")
                return
            command = ["mypy"]
            if mypy_config is not None:
                command.extend(
                    [
                        "--config-file",
                        os.path.join(
                            prepared_collections.current_collection.path, mypy_config
                        ),
                    ]
                )
            command.append("--namespace-packages")
            command.append("--explicit-package-bases")
            command.extend(["--output", "json"])
            command.extend(session.posargs)
            command.extend(files)
            with silence_run_verbosity():
                output = session.run(
                    *command,
                    env={"MYPYPATH": str(prepared_collections.current_place)},
                    silent=True,
                    success_codes=(0, 1, 2),
                )

            if output:
                process_mypy_errors(session, prepared_collections, output)

    def typing(session: nox.Session) -> None:
        install(session, *compose_dependencies(session))
        prepared_collections = prepare_collections(
            session,
            install_in_site_packages=False,
            extra_deps_files=["tests/unit/requirements.yml"],
        )
        if not prepared_collections:
            session.warn("Skipping mypy...")
        if run_mypy and prepared_collections:
            execute_mypy(session, prepared_collections)

    typing.__doc__ = compose_description(
        prefix={
            "one": "Run type checker:",
            "other": "Run type checkers:",
        },
        programs={
            "mypy": run_mypy,
        },
    )
    nox.session(name="typing", default=False)(typing)


def add_config_lint(
    *,
    run_antsibullnox_config_lint: bool,
):
    """
    Add nox session for antsibull-nox config linting.
    """

    def antsibull_nox_config(session: nox.Session) -> None:
        if run_antsibullnox_config_lint:
            run_bare_script(
                session,
                "antsibull-nox-lint-config",
            )

            session.run("antsibull-nox", "lint-config")

    antsibull_nox_config.__doc__ = "Lint antsibull-nox config"
    nox.session(name="antsibull-nox-config", python=False, default=False)(
        antsibull_nox_config
    )


def add_lint_sessions(
    *,
    make_lint_default: bool = True,
    extra_code_files: list[str] | None = None,
    # isort:
    run_isort: bool = True,
    isort_config: str | os.PathLike | None = None,
    isort_package: PackageTypeOrList = "isort",
    # black:
    run_black: bool = True,
    run_black_modules: bool | None = None,
    black_config: str | os.PathLike | None = None,
    black_package: PackageTypeOrList = "black",
    # ruff format:
    run_ruff_format: bool = False,
    ruff_format_config: str | os.PathLike | None = None,
    ruff_format_package: PackageTypeOrList = "ruff",
    # ruff autofix:
    run_ruff_autofix: bool = False,
    ruff_autofix_config: str | os.PathLike | None = None,
    ruff_autofix_package: PackageTypeOrList = "ruff",
    ruff_autofix_select: list[str] | None = None,
    # ruff check:
    run_ruff_check: bool = False,
    ruff_check_config: str | os.PathLike | None = None,
    ruff_check_package: PackageTypeOrList = "ruff",
    # flake8:
    run_flake8: bool = True,
    flake8_config: str | os.PathLike | None = None,
    flake8_package: PackageTypeOrList = "flake8",
    # pylint:
    run_pylint: bool = True,
    pylint_rcfile: str | os.PathLike | None = None,
    pylint_modules_rcfile: str | os.PathLike | None = None,
    pylint_package: PackageTypeOrList = "pylint",
    pylint_ansible_core_package: PackageTypeOrList | None = "ansible-core",
    pylint_extra_deps: list[str | PackageType] | None = None,
    # yamllint:
    run_yamllint: bool = False,
    yamllint_config: str | os.PathLike | None = None,
    yamllint_config_plugins: str | os.PathLike | None = None,
    yamllint_config_plugins_examples: str | os.PathLike | None = None,
    yamllint_config_extra_docs: str | os.PathLike | None = None,
    yamllint_package: PackageTypeOrList = "yamllint",
    yamllint_antsibull_docutils_package: PackageTypeOrList = "antsibull-docutils",
    # mypy:
    run_mypy: bool = True,
    mypy_config: str | os.PathLike | None = None,
    mypy_package: PackageTypeOrList = "mypy",
    mypy_ansible_core_package: PackageTypeOrList | None = "ansible-core",
    mypy_extra_deps: list[str | PackageType] | None = None,
    # antsibull-nox config lint:
    run_antsibullnox_config_lint: bool = True,
) -> None:
    """
    Add nox sessions for linting.
    """
    has_formatters = (
        run_isort
        or run_black
        or run_black_modules
        or False
        or run_ruff_format
        or run_ruff_autofix
    )
    has_codeqa = run_ruff_check or run_flake8 or run_pylint
    has_yamllint = run_yamllint
    has_typing = run_mypy
    has_config_lint = run_antsibullnox_config_lint

    add_lint(
        has_formatters=has_formatters,
        has_codeqa=has_codeqa,
        has_yamllint=has_yamllint,
        has_typing=has_typing,
        has_config_lint=has_config_lint,
        make_lint_default=make_lint_default,
    )

    if has_formatters:
        add_formatters(
            extra_code_files=extra_code_files or [],
            run_isort=run_isort,
            isort_config=isort_config,
            isort_package=isort_package,
            run_black=run_black,
            run_black_modules=run_black_modules,
            black_config=black_config,
            black_package=black_package,
            run_ruff_format=run_ruff_format,
            ruff_format_config=ruff_format_config,
            ruff_format_package=ruff_format_package,
            run_ruff_autofix=run_ruff_autofix,
            ruff_autofix_config=ruff_autofix_config,
            ruff_autofix_package=ruff_autofix_package,
            ruff_autofix_select=ruff_autofix_select or [],
        )

    if has_codeqa:
        add_codeqa(
            extra_code_files=extra_code_files or [],
            run_ruff_check=run_ruff_check,
            ruff_check_config=ruff_check_config,
            ruff_check_package=ruff_check_package,
            run_flake8=run_flake8,
            flake8_config=flake8_config,
            flake8_package=flake8_package,
            run_pylint=run_pylint,
            pylint_rcfile=pylint_rcfile,
            pylint_modules_rcfile=pylint_modules_rcfile,
            pylint_package=pylint_package,
            pylint_ansible_core_package=pylint_ansible_core_package,
            pylint_extra_deps=pylint_extra_deps or [],
        )

    if has_yamllint:
        add_yamllint(
            run_yamllint=run_yamllint,
            yamllint_config=yamllint_config,
            yamllint_config_plugins=yamllint_config_plugins,
            yamllint_config_plugins_examples=yamllint_config_plugins_examples,
            yamllint_config_extra_docs=yamllint_config_extra_docs,
            yamllint_package=yamllint_package,
            yamllint_antsibull_docutils_package=yamllint_antsibull_docutils_package,
        )

    if has_typing:
        add_typing(
            extra_code_files=extra_code_files or [],
            run_mypy=run_mypy,
            mypy_config=mypy_config,
            mypy_package=mypy_package,
            mypy_ansible_core_package=mypy_ansible_core_package,
            mypy_extra_deps=mypy_extra_deps or [],
        )

    if has_config_lint:
        add_config_lint(
            run_antsibullnox_config_lint=run_antsibullnox_config_lint,
        )


__all__ = [
    "add_lint_sessions",
]
