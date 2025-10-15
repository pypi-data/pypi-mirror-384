# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Coverage utilities."""

import contextlib
import json
import logging
import shutil
import sys
from pathlib import Path
from pprint import pformat
from subprocess import run
from typing import TYPE_CHECKING

from mfd_code_quality.coverage.consts import COVERAGE_XML_FILE, DIFF_COVERAGE_THRESHOLD, COVERAGE_JSON_FILE
from mfd_code_quality.utils import get_root_dir

if TYPE_CHECKING:
    from subprocess import CompletedProcess

logger = logging.getLogger("mfd-code-quality.coverage")


def is_diff_coverage_threshold_reached() -> bool:
    """
    Check if diff coverage value has reached the threshold.

    We just call diff-cover tool here.
    Under the hood it's just parsing git diff output and compares it with coverage XML report.

    :return: True if threshold reached
    :raise FileNotFoundError: When XML report not found
    """
    if not (get_root_dir() / COVERAGE_XML_FILE).exists():
        raise FileNotFoundError(f"{COVERAGE_XML_FILE} does not exist in {get_root_dir()}")

    diff_cover_executable = Path(sys.executable).parent / "diff-cover"
    diff_cover_cmd = (
        f"{diff_cover_executable} {COVERAGE_XML_FILE} --include-untracked --fail-under={DIFF_COVERAGE_THRESHOLD}"
    )
    logger.info(f"[Coverage] Executing: {diff_cover_cmd}")

    completed_process: "CompletedProcess" = run(
        diff_cover_cmd, cwd=get_root_dir(), capture_output=True, text=True, check=False, shell=True
    )
    if completed_process.stdout.strip():
        logger.info(completed_process.stdout)
    if completed_process.stderr.strip():
        logger.info(completed_process.stderr)

    logger.info(
        "[Coverage] diff-cover tool reported that coverage threshold is "
        f"{'' if completed_process.returncode == 0 else 'NOT '}met"
    )
    return completed_process.returncode == 0


def get_current_coverage_json() -> dict[str, str | float | int] | None:
    """
    Get current coverage in JSON format.

    :return: JSON red from coverage report (totals section) or None if coverage report not found
    """
    new_coverage_path = get_root_dir() / COVERAGE_JSON_FILE
    if not new_coverage_path.exists():
        logger.warning("[Coverage] New coverage report not found.")
        return

    with open(new_coverage_path) as cov:
        new_coverage_json = json.load(cov)["totals"]

    return new_coverage_json


def log_module_coverage() -> None:
    """Log current coverage of module."""
    new_coverage_json = get_current_coverage_json()
    logger.debug(f"[Coverage] Calculated coverage of a module:\n{pformat(new_coverage_json, indent=4)}")


@contextlib.contextmanager
def coverage_section() -> None:
    """Contextmanager to be used on top of coverage operations."""

    def _log_section_info(info_between_separators: str) -> None:
        terminal_width = shutil.get_terminal_size().columns
        separator_len = (terminal_width - len(info_between_separators)) // 2
        logger.info(
            f"\n{'>' * separator_len}{info_between_separators}{'<' * separator_len}\n", extra={"is_separator": True}
        )

    _log_section_info(" COVERAGE SECTION START ")
    yield
    _log_section_info(" COVERAGE SECTION END ")
