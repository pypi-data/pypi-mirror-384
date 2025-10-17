# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import errno
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from dyff.schema.platform import MethodBase, MethodImplementationKind, Report

from .._internal import fqn
from . import context, jupyter, legacy, python


# https://stackoverflow.com/a/38662876/3709935
def _remove_ansi_escape_sequences(line):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", line)


def _delete_directory_contents(
    directory: Path, *, keep: Optional[list[Path]] = None
) -> None:
    if keep is None:
        keep = []
    if not directory.is_dir():
        raise ValueError(f"path must be a directory: {directory}")
    for p in directory.iterdir():
        if p.is_dir():
            _delete_directory_contents(p, keep=keep)
            try:
                p.rmdir()
            except OSError as ex:
                # Directory might not be empty if a sub-path is in 'keep'
                if ex.errno != errno.ENOTEMPTY:
                    raise
        elif all(not k.exists() or not p.samefile(k) for k in keep):
            p.unlink()


def _log_separator() -> str:
    lines = [
        "[dyff] " + ("=" * 72),
        "[dyff] START OF ANALYSIS RUN",
        "[dyff] " + ("=" * 72) + "\n",
    ]
    return "\n".join(lines)


def run_analysis(method: MethodBase, *, storage_root: Path, config_file: Path) -> None:
    """Run an analysis workflow locally.

    The analysis workflow consists of running a Method on specified inputs to
    generate output artifacts such as SafetyCases and Measurements.

    The analysis is run in a sub-process. Input artifacts must be accessible at
    ``storage_root / entity_id`` for each input entity. Output artifacts will
    be created in ``storage_root / analysis_id``. Logs will be saved in
    ``storage_root / analysis_id / .dyff / logs.txt``.

    :param method: The specification of the method to run.
    :keyword storage_root: The root directory for local storage of input and
        output artifacts.
    :keyword config_file: A YAML file containing a Kubernetes Analysis resource
        (kind ``analyses.dyff.io/v1alpha1``).

        .. note::

            The format of this file is expected to change in a future release.
    """
    # Need this to get the ID assigned to the analysis
    analysis_id = context.id_from_config_file(config_file)
    output_dir = storage_root / analysis_id

    pythonpath = os.pathsep.join(
        str(storage_root / module) for module in method.modules
    )
    env = os.environ.copy()
    env.update(
        {
            "DYFF_AUDIT_LOCAL_STORAGE_ROOT": str(storage_root),
            "DYFF_AUDIT_ANALYSIS_CONFIG_FILE": str(config_file),
            "PYTHONPATH": pythonpath,
        }
    )

    if method.implementation.kind == MethodImplementationKind.JupyterNotebook:
        impl_module, impl_name = fqn(jupyter.run_jupyter_notebook)
    elif method.implementation.kind == MethodImplementationKind.PythonFunction:
        impl_module, impl_name = fqn(python.run_python_function)
    elif method.implementation.kind == MethodImplementationKind.PythonRubric:
        impl_module, impl_name = fqn(python.run_python_rubric)
    else:
        raise NotImplementedError(
            f"method.implementation.kind = {method.implementation.kind}"
        )

    log_file = output_dir / ".dyff" / "logs.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    # Make sure log_file exists so we don't delete its parent directory
    log_file.touch()

    # [DYFF-577] If the analysis is re-tried due to an error, there may be
    # partial output already from the previous run. This can cause additional
    # spurious errors (e.g., for outputting "duplicate" data) that mask the
    # original error. Note that the config file may be in the output_dir tree
    # and must be kept if present. We also keep the log file because we're
    # appending each run to it.
    _delete_directory_contents(output_dir, keep=[config_file, log_file])

    try:
        with open(log_file, "ab", buffering=0) as fout:
            fout.write(_log_separator().encode())
            cmd = f"from {impl_module} import {impl_name}; {impl_name}()"
            subprocess.run(
                ["python3", "-u", "-X", "faulthandler", "-c", cmd],
                env=env,
                check=True,
                # Redirect both streams to log file
                stdout=fout,
                stderr=subprocess.STDOUT,
            )
    finally:
        # [DYFF-509] Output from Jupyter notebooks often has ANSI escape
        # sequences in it. We want to remove these sequences, but without
        # shadowing the original exception (if any) and without leaving a moment
        # where the logs.txt file could be lost if there's another error.
        current_exception = sys.exc_info()[1]
        try:
            scratch_file = Path(str(log_file) + ".tmp")
            with open(log_file, "r") as fin:
                with open(scratch_file, "w") as fout:
                    fout.writelines(_remove_ansi_escape_sequences(line) for line in fin)
            scratch_file.rename(log_file)
        except Exception as ex:
            if not current_exception:
                raise ex


def run_report(report: Report, *, storage_root: Path):
    """Run a Report workflow locally.

    .. deprecated:: 0.8.0

        Report functionality has been refactored into the
        Method/Measurement/Analysis apparatus. Creation of new Reports is
        disabled.

    The workflow is run in a sub-process. Input artifacts must be accessible at
    ``storage_root / entity_id`` for each input entity. Output artifacts will
    be created in ``storage_root / report_id``. Logs will be saved in
    ``storage_root / report_id / .dyff / logs.txt``.

    :param report: The specification of the Report to run.
    :keyword storage_root: The root directory for local storage of input and
        output artifacts.
    """
    return legacy_run_report(
        rubric=report.rubric,
        dataset_path=str(storage_root / report.dataset),
        evaluation_path=str(storage_root / report.evaluation),
        output_path=str(storage_root / report.id),
        modules=[str(storage_root / module) for module in report.modules],
    )


def legacy_run_report(
    *,
    rubric: str,
    dataset_path: str,
    evaluation_path: str,
    output_path: str,
    modules: Optional[list[str]] = None,
):
    if modules is None:
        modules = []

    def quote(s) -> str:
        return f'"{s}"'

    args = [
        quote(rubric),
        quote(dataset_path),
        quote(evaluation_path),
        quote(output_path),
        ", ".join(quote(module) for module in modules),
    ]

    impl_module, impl_name = fqn(legacy.run_python_rubric)
    cmd = (
        f"from {impl_module} import {impl_name}; {impl_name}"
        "(rubric={}, dataset_path={}, evaluation_path={}, output_path={}, modules=[{}])".format(
            *args
        )
    )

    pythonpath = os.pathsep.join(str(module) for module in modules)
    env = os.environ.copy()
    env.update({"PYTHONPATH": pythonpath})

    log_file = Path(output_path) / ".dyff" / "logs.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "wb", buffering=0) as fout:
        subprocess.run(
            ["python3", "-u", "-X", "faulthandler", "-c", cmd],
            env=env,
            check=True,
            # Redirect both streams to log file
            stdout=fout,
            stderr=subprocess.STDOUT,
        )


__all__ = [
    "legacy_run_report",
    "run_analysis",
    "run_report",
]
